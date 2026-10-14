"""Generate private local configuration without displaying credentials."""

import argparse
from pathlib import Path
import secrets
import shutil


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--historical-replay", action="store_true", help="Copy the unchanged historical test capture to private/captures")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    target = root / ".env"
    if target.exists():
        raise SystemExit("Existing .env retained; edit it locally if needed")
    pg, redis, service = (secrets.token_hex(32) for _ in range(3))
    capture_dir = root / "private" / "captures"
    capture_dir.mkdir(parents=True, exist_ok=True)
    if args.historical_replay:
        source = root / "backend/tests/data/lta_stop44009_service190_20261010.json"
        shutil.copyfile(source, capture_dir / source.name)
    target.write_text("\n".join([
        "LTA_MODE=OFFLINE_FIXTURE", "LTA_CAPTURE_DIR=private/captures", "LTA_DATAMALL_KEY=", "LTA_KEY_PATH=",
        f"API_SERVICE_TOKEN={service}", f"POSTGRES_PASSWORD={pg}", f"REDIS_PASSWORD={redis}",
        f"DATABASE_URL=postgresql://transportlah:{pg}@127.0.0.1:5433/transportlah",
        f"REDIS_URL=redis://:{redis}@127.0.0.1:6380/0",
        "CACHE_TTL_SECONDS=30", "MIN_POLL_INTERVAL_SECONDS=20", "UPSTREAM_TIMEOUT_SECONDS=10",
        "MAX_ACTIVE_STOPS=128", "MAX_CACHE_ENTRIES=512", "ACTIVE_STOPS=", "",
    ]), encoding="utf-8")
    print("Private .env created; secrets were not printed. Historical replay is not live verification.")


if __name__ == "__main__":
    main()
