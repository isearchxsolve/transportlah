"""Real PostGIS/Redis connectivity gate; does not substitute fake dependencies."""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
from backend.app.config import Settings
from backend.app.main import create_app
import httpx


async def main():
    load_dotenv(ROOT / ".env")
    app = create_app(Settings.from_env())
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://dependency-check") as client:
            response = await client.get("/ready")
            print(response.text)
            if response.status_code != 200:
                raise SystemExit("Dependency readiness gate failed; no fake success was produced.")


if __name__ == "__main__":
    asyncio.run(main())
