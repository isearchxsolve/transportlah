# TransportLah

Corrected ingestion foundation for the original Singapore green-commute product. This is not the complete MVP and does not verify passenger journeys yet.

## Implemented and locally checked

- FastAPI ingestion endpoints, process health, dependency readiness, request IDs, and structured metadata logs.
- Explicit `LIVE_NETWORK` and integrity-checked historical `OFFLINE_FIXTURE` transports. Live mode never falls back to replay.
- Separate NextBus arrival candidates; ETA is never used as a position observation timestamp.
- Schedule-only estimates and unavailable/zero locations are explicit. No vehicle trajectory is manufactured.
- Thirty-second TTL cache, a shared per-stop polling budget, coalescing concurrent requests, bounded stop/cache capacity, timeouts, and upstream backoff handling.
- Optional active-stop polling through app lifespan.
- Constant-time service-token authorization on arrival endpoints. This is server/operator authorization, not commuter identity or mobile authentication.
- Nine byte-preserved historical seed artifacts and a SHA-256 manifest. Original master tests are unchanged.

## Quick start on Windows

From this project directory:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
.\.venv\Scripts\python.exe tools/init_local.py --historical-replay
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --env-file .env --host 127.0.0.1 --port 8000 --workers 1
```

`init_local.py` creates actual private local credentials without printing them and does not overwrite an existing `.env`. The replay option copies the original historical capture unchanged; no synthetic bus/device data is produced. `/health` reports liveness. `/ready` returns 503 until the configured database and Redis are reachable, the source is available, and service authorization is configured.

For authenticated API queries, use the service token from private configuration on the server/operator side. Never embed it or the LTA key in a mobile build.

```text
GET /v1/arrivals/44009?service_no=190
GET /v1/arrivals?bus_stop_codes=44009&bus_stop_codes=09048&service_no=190
Authorization: Bearer <private service token>
```

Only stop 44009/service 190 has an included historical capture. The multiple-stop endpoint reports missing recordings as unavailable; it does not fabricate a second stop. A service-filtered capture is not advertised as a complete all-services response.

## Real capture

Set `LTA_DATAMALL_KEY` or `LTA_KEY_PATH` in private configuration, then run:

```powershell
.\.venv\Scripts\python.exe tools/capture_lta.py --stop 09048 --service 190
```

The collector calls the official HTTPS endpoint, preserves the received payload and real capture time, hashes it, and writes a new file under ignored `private/captures`. Without a key, it exits with an explicit failure and writes no capture. Use a validated key and current genuine captures before claiming multi-stop live acceptance.

## Tests

```powershell
.\.venv\Scripts\python.exe tools/verify_seed.py
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
Push-Location reference/seed
..\..\.venv\Scripts\python.exe -m unittest test_spatial_engine -v
Pop-Location
```

The new ingestion tests read the unaltered historical capture and exercise real local elapsed-time/cache behavior. The historical master suite retains its pre-existing test vectors and known pedestrian/replay passes. Neither suite constitutes physical passenger verification.

With the actual backend running, `python demo_runner.py` sends a concurrent local HTTP burst, preserves the source capture time/hash, reports schedule/unavailable-location flags and readiness failures, and writes a local receipt. It does not generate GPS pings or claim live LTA acceptance.

## Database/cache and cloud checks

Authenticated, loopback-bound PostGIS/Redis/ingestion configuration is in `docker-compose.yml`. Start it on a suitable Docker/cloud host:

```text
docker compose --env-file .env up --build
python tools/check_dependencies.py
```

The current laptop has no Docker executable; the container stack and image builds have not been executed here. `.github/workflows/backend.yml` is prepared for manual dispatch to run the immutable master suite, ingestion checks, and a real PostGIS/Redis dependency gate. A workflow file is not a completed cloud run. Initial automatic triggers are withheld because the current private-runner allowance could not be read with the available account scopes.

## Important boundaries

- Included historical capture: 2026-10-10 21:42:59 UTC, stop 44009/service 190. Its stored payload hash matches, but its original network authenticity has not been independently reverified this session.
- All three captured candidates have `Monitored=0` and zero coordinates. Their estimated arrival times are usable as historical schedule context; vehicle position and passenger presence are not established.
- Cache/budgets are process-local. Run one worker; multi-worker/multi-instance Redis coordination is not implemented. The 20-second setting reflects documented refresh cadence, not a proven account-wide quota agreement.
- Freshness describes the locally captured source snapshot, not the unknown precise vehicle-position observation time.
- Full user auth, spatial migrations, stops/routes import, scoring, rewards, Flutter builds, physical-device background GPS, field validation, and release remain pending.
- See `docs/HIGH_MODE_QUEUE.md` before implementing parked fundamental decisions.

## Resume documents

Private source repository: https://github.com/isearchxsolve/transportlah. The initial implementation branch is `codex/transportlah-foundation`.

`python tools/run_checks.py` writes actual test output and SHA-256 source/output receipts under `receipts/`; it does not assert live/device/cloud acceptance.

- `docs/PLAN.md`: 87 tasks and gates.
- `docs/STATE.md`: exact status and resume point.
- `docs/DECISIONS.md`: decisions and unresolved choices.
- `docs/REQUIREMENTS.md`: original product traceability.
- `docs/DISCREPANCIES.md`: reviewed source conflicts.
- `docs/ASSUMPTIONS.md`: configurable assumptions and constraints.
- `docs/EVIDENCE_INVENTORY.md`: available versus missing evidence.
- `docs/HIGH_MODE_QUEUE.md`: parked items for the user's High pass.
