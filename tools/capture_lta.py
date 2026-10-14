"""Capture only real authenticated LTA replies. No fixture fallback or time shifts."""

import argparse
import asyncio
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from backend.app.config import Settings
from backend.app.models import parse_arrivals
from backend.app.transport import LiveTransport, SourceUnavailable


async def capture(args):
    load_dotenv(ROOT / ".env")
    settings = Settings.from_env()
    if not settings.lta_account_key:
        raise SystemExit("No configured LTA key. No network capture or fake fallback was produced.")
    if not re.fullmatch(r"\d{5}", args.stop) or (args.service and not re.fullmatch(r"[A-Za-z0-9]{1,8}", args.service)):
        raise SystemExit("Invalid stop/service format")
    transport = LiveTransport(settings.lta_account_key, settings.upstream_timeout_seconds)
    try:
        result = await transport.fetch(args.stop, args.service)
        parse_arrivals(result, args.stop, args.service)
        args.output.mkdir(parents=True, exist_ok=True)
        timestamp = result.captured_at.strftime("%Y%m%dT%H%M%S%fZ")
        path = args.output / f"lta_{args.stop}_{args.service or 'all'}_{timestamp}.json"
        document = {"captured_at_utc": result.captured_at.isoformat(), "source": "LIVE_NETWORK", "stop": args.stop, "service": args.service, "raw": result.raw, "raw_sha256": result.raw_sha256, "endpoint": "https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival"}
        with path.open("x", encoding="utf-8") as file:
            json.dump(document, file, indent=2)
        print(json.dumps({"capture_file": str(path), "captured_at_utc": result.captured_at.isoformat(), "raw_sha256": result.raw_sha256, "source": result.source}))
    except SourceUnavailable as error:
        raise SystemExit(str(error)) from None
    finally:
        await transport.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--stop", required=True)
    parser.add_argument("--service")
    parser.add_argument("--output", type=Path, default=ROOT / "private/captures")
    asyncio.run(capture(parser.parse_args()))
