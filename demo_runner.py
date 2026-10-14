"""Talk to the actual local ingestion service; never generate transit/device data."""

import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

from dotenv import dotenv_values
import httpx


async def run(args):
    root = Path(__file__).resolve().parent
    config = dotenv_values(root / ".env")
    token = config.get("API_SERVICE_TOKEN")
    if not token:
        raise SystemExit("Private service token is not configured")
    async with httpx.AsyncClient(base_url=args.url, timeout=15) as client:
        health = await client.get("/health")
        health.raise_for_status()
        ready = await client.get("/ready")
        responses = await asyncio.gather(*(client.get(f"/v1/arrivals/{args.stop}", params={"service_no": args.service}, headers={"Authorization": f"Bearer {token}"}) for _ in range(args.requests)))
        for response in responses:
            response.raise_for_status()
        arrivals = responses[0].json()
        candidates = [candidate for service in arrivals["services"] for candidate in service["candidates"]]
        receipt = {
            "receipt_kind": "actual_local_http_ingestion_only",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "health_status": health.status_code,
            "readiness_status": ready.status_code,
            "readiness": ready.json(),
            "requests_completed": len(responses),
            "source": arrivals["source"],
            "source_captured_at": arrivals["source_captured_at"],
            "raw_sha256": arrivals["raw_sha256"],
            "is_historical_replay": arrivals["is_historical_replay"],
            "snapshot_fresh": arrivals["snapshot_fresh"],
            "arrival_candidates": len(candidates),
            "candidates_with_location": sum(candidate["location"] is not None for candidate in candidates),
            "schedule_based_candidates": sum(candidate["monitored"] is False for candidate in candidates),
            "cached_responses": sum(response.json()["cache_hit"] for response in responses),
            "verification_enabled": False,
            "live_api_acceptance": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--stop", default="44009")
    parser.add_argument("--service", default="190")
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--output", type=Path, default=Path("receipts/local_ingestion_smoke.json"))
    args = parser.parse_args()
    if not 1 <= args.requests <= 100:
        raise SystemExit("Request count must be between 1 and 100")
    asyncio.run(run(args))
