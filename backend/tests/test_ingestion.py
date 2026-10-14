"""Replay checks use the unaltered historical LTA capture, never invented GPS."""

import asyncio
from datetime import datetime
import json
from pathlib import Path
import secrets
import tempfile
import time
import unittest

import httpx

from backend.app.config import Settings
from backend.app.ingestion import ArrivalService
from backend.app.main import create_app
from backend.app.models import parse_arrivals
from backend.app.transport import CaptureTransport, SourceUnavailable


DATA = Path(__file__).parent / "data"
CAPTURE = DATA / "lta_stop44009_service190_20261010.json"


class CountingCaptureTransport(CaptureTransport):
    """Count actual reads of the historical capture transport."""

    def __init__(self, directory):
        super().__init__(directory)
        self.calls = 0
        self.call_times = []

    async def fetch(self, stop, service):
        self.calls += 1
        self.call_times.append(time.monotonic())
        return await super().fetch(stop, service)


class CaptureChecks(unittest.IsolatedAsyncioTestCase):
    async def test_original_hash_is_checked_and_times_are_preserved(self):
        source = CaptureTransport(DATA)
        result = await source.fetch("44009", "190")
        original = json.loads(CAPTURE.read_text(encoding="utf-8"))
        self.assertEqual(result.captured_at, datetime.fromisoformat(original["captured_at_utc"]))
        self.assertEqual(result.raw, original["raw"])
        self.assertEqual(result.raw_sha256, original["raw_sha256"])
        self.assertEqual(result.source, "OFFLINE_FIXTURE")

    async def test_schedule_only_zero_locations_never_become_a_trajectory(self):
        capture = await CaptureTransport(DATA).fetch("44009", "190")
        result = parse_arrivals(capture)
        candidates = result.services[0].candidates
        self.assertEqual([c.slot for c in candidates], ["NextBus", "NextBus2", "NextBus3"])
        self.assertTrue(all(c.location is None for c in candidates))
        self.assertTrue(all(c.monitored is False for c in candidates))
        self.assertTrue(all(c.position_observed_at is None for c in candidates))
        for c in candidates:
            original = capture.raw["Services"][0][c.slot]
            self.assertEqual(c.estimated_arrival, datetime.fromisoformat(original["EstimatedArrival"]))
            self.assertIn("schedule_based_estimate", c.quality_flags)
            self.assertIn("unavailable_location", c.quality_flags)
        self.assertEqual(result.source_captured_at, capture.captured_at)
        self.assertTrue(result.is_historical_replay)

    async def test_unrecorded_stop_and_unrecorded_scope_fail_without_fallback(self):
        source = CaptureTransport(DATA)
        with self.assertRaises(SourceUnavailable):
            await source.fetch("09048", "190")
        with self.assertRaises(SourceUnavailable):
            await source.fetch("44009", None)

    async def test_absent_capture_directory_is_not_ready(self):
        with tempfile.TemporaryDirectory() as directory:
            source = CaptureTransport(Path(directory))
            self.assertFalse(source.available)
            with self.assertRaises(SourceUnavailable):
                await source.fetch("44009", "190")

    async def test_concurrent_burst_is_coalesced_using_one_actual_capture_read(self):
        source = CountingCaptureTransport(DATA)
        service = ArrivalService(source, cache_ttl=30, min_poll_interval=20)
        results = await asyncio.gather(*(service.get("44009", "190") for _ in range(25)))
        self.assertEqual(source.calls, 1)
        self.assertEqual(sum(not r.cache_hit for r in results), 1)
        self.assertEqual(service.metrics["cache_hits"], 24)

    async def test_ttl_expiry_respects_stop_rate_limit_with_real_elapsed_time(self):
        source = CountingCaptureTransport(DATA)
        service = ArrivalService(source, cache_ttl=0.01, min_poll_interval=0.06)
        await service.get("44009", "190")
        await asyncio.sleep(0.02)
        second = await service.get("44009", "190")
        self.assertFalse(second.cache_hit)
        self.assertEqual(source.calls, 2)
        self.assertGreaterEqual(source.call_times[1] - source.call_times[0], 0.055)

    async def test_unrecorded_services_share_stop_budget(self):
        source = CountingCaptureTransport(DATA)
        service = ArrivalService(source, cache_ttl=0.01, min_poll_interval=0.06)
        await service.get("44009", "190")
        with self.assertRaises(SourceUnavailable):
            await service.get("44009", None)
        self.assertGreaterEqual(source.call_times[1] - source.call_times[0], 0.055)


class ConfigurationChecks(unittest.TestCase):
    def test_invalid_configuration_fails_explicitly(self):
        with self.assertRaises(ValueError):
            Settings(mode="INVENTED_MODE")
        with self.assertRaises(ValueError):
            Settings(cache_ttl_seconds=-1)
        with self.assertRaises(ValueError):
            Settings(api_service_token="short")
        with self.assertRaises(ValueError):
            Settings(mode="LIVE_NETWORK")

    def test_secret_values_are_not_in_settings_repr(self):
        token = secrets.token_hex(32)
        key = secrets.token_hex(32)
        settings = Settings(api_service_token=token, lta_account_key=key)
        self.assertNotIn(token, repr(settings))
        self.assertNotIn(key, repr(settings))


class ApiChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token = secrets.token_hex(32)
        settings = Settings(capture_dir=DATA, api_service_token=self.token)
        self.app = create_app(settings)
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_arrivals_require_service_authorization(self):
        response = await self.client.get("/v1/arrivals/44009", params={"service_no": "190"})
        self.assertEqual(response.status_code, 401)
        response = await self.client.get("/v1/arrivals/44009", params={"service_no": "190"}, headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["source"], "OFFLINE_FIXTURE")
        self.assertTrue(body["is_historical_replay"])
        self.assertIsNone(body["services"][0]["candidates"][0]["location"])
        self.assertNotIn(self.token, response.text)

    async def test_readiness_reports_external_dependencies_instead_of_claiming_ready(self):
        response = await self.client.get("/ready")
        self.assertEqual(response.status_code, 503)
        body = response.json()
        self.assertEqual(body["components"]["postgres"], "not_configured")
        self.assertEqual(body["components"]["redis"], "not_configured")
        self.assertEqual(body["components"]["transit_source"], "historical_replay_available")
        self.assertFalse(body["ready"])

    async def test_multiple_stop_endpoint_reports_missing_capture_truthfully(self):
        response = await self.client.get("/v1/arrivals", params=[("bus_stop_codes", "44009"), ("bus_stop_codes", "09048"), ("service_no", "190")], headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 200)
        entries = response.json()["results"]
        self.assertEqual(entries[0]["status"], "ok")
        self.assertEqual(entries[1]["status"], "unavailable")
        self.assertEqual(entries[1]["bus_stop_code"], "09048")

    async def test_request_id_is_generated_and_bad_stop_is_rejected(self):
        response = await self.client.get("/health", headers={"X-Request-ID": "not a uuid"})
        self.assertEqual(response.status_code, 200)
        from uuid import UUID
        UUID(response.headers["X-Request-ID"])
        response = await self.client.get("/v1/arrivals/not-a-stop", headers={"Authorization": f"Bearer {self.token}"})
        self.assertEqual(response.status_code, 422)

    async def test_lifespan_polls_only_configured_historical_target_and_cancels(self):
        settings = Settings(capture_dir=DATA, api_service_token=self.token,
                            cache_ttl_seconds=0.02, min_poll_interval_seconds=0.02,
                            active_stops=(("44009", "190"),))
        app = create_app(settings)
        async with app.router.lifespan_context(app):
            await asyncio.sleep(0.05)
            self.assertGreaterEqual(app.state.arrivals.metrics["source_requests"], 1)
            self.assertEqual(app.state.arrivals.metrics["source_failures"], 0)
        requests_at_shutdown = app.state.arrivals.metrics["source_requests"]
        await asyncio.sleep(0.03)
        self.assertEqual(app.state.arrivals.metrics["source_requests"], requests_at_shutdown)


if __name__ == "__main__":
    unittest.main()
