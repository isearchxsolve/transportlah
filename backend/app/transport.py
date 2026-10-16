"""Real LTA and integrity-checked historical capture transports."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import httpx


BUS_ARRIVAL_URL = "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


class SourceUnavailable(Exception):
    def __init__(self, message="Transit source is unavailable", *, status_code=503, retry_after=None):
        super().__init__(message)
        self.status_code = status_code
        self.retry_after = retry_after


@dataclass(frozen=True)
class CapturedResponse:
    raw: dict[str, Any]
    captured_at: datetime
    raw_sha256: str
    source: str
    service_scope: str | None


def raw_hash(raw):
    # Matches the historical capture's original hashing convention.
    return hashlib.sha256(json.dumps(raw, sort_keys=True).encode("utf-8")).hexdigest()


class CaptureTransport:
    def __init__(self, directory: Path):
        self._captures = {}
        for path in sorted(Path(directory).glob("*.json")):
            document = json.loads(path.read_text(encoding="utf-8"))
            raw = document["raw"]
            captured_at = datetime.fromisoformat(document["captured_at_utc"])
            if captured_at.tzinfo is None:
                raise ValueError("Capture time must include a timezone")
            if document.get("source") != "LIVE_NETWORK":
                raise ValueError("Replay requires a historical network capture")
            if not isinstance(raw, dict) or raw_hash(raw) != document["raw_sha256"]:
                raise ValueError("Historical capture payload integrity check failed")
            stop = str(document["stop"])
            service = str(document["service"]) if document.get("service") else None
            if raw.get("BusStopCode") != stop:
                raise ValueError("Capture stop metadata disagrees with its payload")
            if service and any(s.get("ServiceNo") != service for s in raw.get("Services", [])):
                raise ValueError("Capture service scope disagrees with its payload")
            key = (stop, service)
            candidate = CapturedResponse(raw, captured_at, document["raw_sha256"], "OFFLINE_FIXTURE", service)
            if key not in self._captures or captured_at > self._captures[key].captured_at:
                self._captures[key] = candidate

    @property
    def available(self):
        return bool(self._captures)

    @property
    def targets(self):
        return tuple(self._captures)

    async def fetch(self, stop, service):
        candidate = self._captures.get((stop, service))
        if candidate is None and service is not None:
            candidate = self._captures.get((stop, None))
        if candidate is None:
            raise SourceUnavailable("No authentic historical capture for the requested stop/service scope")
        # Preserve every original value and timestamp; caller never receives mutable source storage.
        return CapturedResponse(json.loads(json.dumps(candidate.raw)), candidate.captured_at, candidate.raw_sha256, candidate.source, candidate.service_scope)

    async def close(self):
        pass


class LiveTransport:
    def __init__(self, account_key, timeout=10.0):
        if not account_key:
            raise ValueError("Live transport requires an LTA key")
        self._account_key = account_key
        self._client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)

    @property
    def available(self):
        # Configuration availability is not a successful network handshake.
        return bool(self._account_key)

    async def fetch(self, stop, service):
        params = {"BusStopCode": stop}
        if service:
            params["ServiceNo"] = service
        try:
            async with self._client.stream("GET", BUS_ARRIVAL_URL, params=params, headers={"AccountKey": self._account_key, "accept": "application/json"}) as response:
                if response.status_code != 200:
                    retry_after = None
                    if response.status_code == 429:
                        value = response.headers.get("Retry-After", "20")
                        try:
                            retry_after = min(300.0, max(20.0, float(value)))
                            if not math.isfinite(float(value)): retry_after=20.0
                        except ValueError:
                            retry_after = 20.0
                    raise SourceUnavailable("LTA upstream rejected the request", status_code=502, retry_after=retry_after)
                chunks = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > MAX_RESPONSE_BYTES:
                        raise SourceUnavailable("LTA response exceeds the configured size limit", status_code=502)
                    chunks.append(chunk)
            raw = json.loads(b"".join(chunks))
            if not isinstance(raw, dict):
                raise SourceUnavailable("LTA response must be a JSON object", status_code=502)
            return CapturedResponse(raw, datetime.now(timezone.utc), raw_hash(raw), "LIVE_NETWORK", service)
        except (httpx.HTTPError, json.JSONDecodeError, UnicodeDecodeError):
            # Never expose raw exception text, headers, or credentials to logs/API clients.
            raise SourceUnavailable("LTA network or response decoding failure", status_code=502) from None

    async def close(self):
        await self._client.aclose()
