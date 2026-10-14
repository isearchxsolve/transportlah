"""Bounded single-process TTL cache, per-stop budget, and coalesced requests."""

import asyncio
from collections import OrderedDict
from datetime import datetime, timezone
import time

from .models import parse_arrivals
from .transport import SourceUnavailable


class ArrivalService:
    def __init__(self, transport, cache_ttl=30.0, min_poll_interval=20.0, max_stops=128, max_cache_entries=512):
        self.transport = transport
        self.cache_ttl = cache_ttl
        self.min_poll_interval = min_poll_interval
        self.max_stops = max_stops
        self.max_cache_entries = max_cache_entries
        self._locks = {}
        self._next_allowed = {}
        self._cache = OrderedDict()
        self.last_success_at = None
        self.last_failure_at = None
        self.metrics = {"source_requests": 0, "cache_hits": 0, "source_failures": 0}

    def _cached(self, key):
        entry = self._cache.get(key)
        if entry is not None:
            if time.monotonic() < entry[0]:
                self._cache.move_to_end(key)
                return entry[1]
            del self._cache[key]
        return None

    def _serve(self, result, cache_hit):
        age = max(0.0, (datetime.now(timezone.utc) - result.source_captured_at).total_seconds())
        return result.model_copy(update={"cache_hit": cache_hit, "source_snapshot_age_seconds": round(age, 3), "snapshot_fresh": not result.is_historical_replay and age <= self.cache_ttl})

    async def get(self, stop, service=None):
        key = (stop, service)
        cached = self._cached(key)
        if cached is not None:
            self.metrics["cache_hits"] += 1
            return self._serve(cached, True)
        if stop not in self._locks:
            if len(self._locks) >= self.max_stops:
                raise SourceUnavailable("Active-stop capacity is exhausted")
            self._locks[stop] = asyncio.Lock()
        async with self._locks[stop]:
            cached = self._cached(key)
            if cached is not None:
                self.metrics["cache_hits"] += 1
                return self._serve(cached, True)
            delay = self._next_allowed.get(stop, 0.0) - time.monotonic()
            if delay > 0:
                await asyncio.sleep(delay)
            self._next_allowed[stop] = time.monotonic() + self.min_poll_interval
            self.metrics["source_requests"] += 1
            try:
                capture = await self.transport.fetch(stop, service)
                result = parse_arrivals(capture, stop, service)
            except SourceUnavailable as error:
                self.last_failure_at = time.monotonic()
                self.metrics["source_failures"] += 1
                if error.retry_after:
                    self._next_allowed[stop] = max(self._next_allowed[stop], time.monotonic() + error.retry_after)
                raise
            self.last_success_at = time.monotonic()
            self._cache[key] = (time.monotonic() + self.cache_ttl, result)
            self._cache.move_to_end(key)
            while len(self._cache) > self.max_cache_entries:
                self._cache.popitem(last=False)
            return self._serve(result, False)

    async def poll(self, targets, interval):
        """Explicit configured targets only; cancellation belongs to app lifespan."""
        while True:
            async def fetch_target(target):
                try:
                    await self.get(*target)
                except SourceUnavailable:
                    pass  # Already counted; subsequent attempt obeys the same budget.
            await asyncio.gather(*(fetch_target(target) for target in targets))
            await asyncio.sleep(interval)
