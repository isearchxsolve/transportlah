# TransportLah

Corrected ingestion plus verification, spatial, identity and reward foundations for the original Singapore green-commute product. This is not the complete MVP and does not verify passenger journeys yet.

## Implemented and locally checked

- FastAPI ingestion endpoints, process health, dependency readiness, request IDs, and structured metadata logs.
- Explicit `LIVE_NETWORK` and integrity-checked historical `OFFLINE_FIXTURE` transports. Live mode never falls back to replay.
- Separate NextBus arrival candidates; ETA is never used as a position observation timestamp.
- Schedule-only estimates and unavailable/zero locations are explicit. No vehicle trajectory is manufactured.
- Thirty-second TTL cache, a shared per-stop polling budget, coalescing concurrent requests, bounded stop/cache capacity, timeouts, and upstream backoff handling.
- Optional active-stop polling through app lifespan.
- Constant-time service-token authorization on arrival endpoints. This is server/operator authorization, not commuter identity or mobile authentication.
- Nine byte-preserved historical seed artifacts and a SHA-256 manifest. Original master tests are unchanged.
- Explainable seven-factor policy with conservative missing-data/tier/contest rules and a separate rail gate.
- Versioned native-geography schema, matching indexes, restricted commuter/worker roles and immutable verification/points ledger.
- Managed-provider asymmetric JWT verifier, server memberships and transaction-local owner/tenant RLS.
- Worker-only atomic settlement, exact retries, gross daily cap and immutable reversals.

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

Ingestion tests read the unaltered historical capture. New policy/crypto/database cases are labelled generated TEST_VECTOR data. Without TEST_DATABASE_URL, 15 real-engine tests explicitly skip; that is not database acceptance. CI requires a real disposable database and forbids skipping that gate. The historical master suite remains unchanged. None of these tests constitutes physical passenger verification.

With the actual backend running, `python demo_runner.py` sends a concurrent local HTTP burst, preserves the source capture time/hash, reports schedule/unavailable-location flags and readiness failures, and writes a local receipt. It does not generate GPS pings or claim live LTA acceptance.

## Database/cache and cloud checks

Authenticated, loopback-bound PostGIS/Redis/ingestion configuration is in `docker-compose.yml`. Start it on a suitable Docker/cloud host:

```text
docker compose --env-file .env up --build
python tools/check_dependencies.py
```

The laptop has no Docker executable. GitHub CI now executes actual PostgreSQL16/PostGIS and Redis7.4 containers, migrations, real login/RLS/concurrency checks, policy/crypto/ingestion checks, unchanged master tests and readiness. Push triggers are restricted to backend/tool/dependency/workflow changes; manual dispatch is available. Output/source hashes are saved as an artifact. Product Docker-image builds and mobile/device builds remain pending. See `docs/HIGH_PASS_RECEIPT.md` for the executed run.

Run `python tools/migrate.py` with an explicitly privileged MIGRATION_DATABASE_URL to apply the schema. Provision separate server-only login users inheriting either transportlah_app or transportlah_worker; commuter logins must not own tables, bypass RLS or inherit worker permissions. See `docs/IDENTITY_REWARD_CONTRACT.md`. Do not deploy commuter paths using the administrator DATABASE_URL. Provider/HTTP integration remains pending.

## Important boundaries

- Included historical capture: 2026-10-10 21:42:59 UTC, stop 44009/service 190. Its stored payload hash matches, but its original network authenticity has not been independently reverified this session.
- All three captured candidates have `Monitored=0` and zero coordinates. Their estimated arrival times are usable as historical schedule context; vehicle position and passenger presence are not established.
- Cache/budgets are process-local. Run one worker; multi-worker/multi-instance Redis coordination is not implemented. The 20-second setting reflects documented refresh cadence, not a proven account-wide quota agreement.
- Freshness describes the locally captured source snapshot, not the unknown precise vehicle-position observation time.
- Policy core, schema, JWT/RLS boundary and settlement functions are implemented/tested. Real evaluators, provider/HTTP integration, catalogs, admin permissions, ranking/contest flows, Flutter/device validation and release remain pending.
- H01-H03 are resolved; their contracts are linked in `docs/HIGH_MODE_QUEUE.md`.

## Resume documents

Private source repository: https://github.com/isearchxsolve/transportlah. The initial implementation branch is `codex/transportlah-foundation`.

`python tools/run_checks.py --output-dir receipts/high_local` saves local output/source hashes including skipped-test counts. Cloud receipts under `receipts/cloud_high` separately record CI SHA/run and real dependency results. Neither claims live LTA or device acceptance.

- `docs/PLAN.md`: 87 tasks and gates.
- `docs/STATE.md`: exact status and resume point.
- `docs/DECISIONS.md`: decisions and unresolved choices.
- `docs/REQUIREMENTS.md`: original product traceability.
- `docs/DISCREPANCIES.md`: reviewed source conflicts.
- `docs/ASSUMPTIONS.md`: configurable assumptions and constraints.
- `docs/EVIDENCE_INVENTORY.md`: available versus missing evidence.
- `docs/HIGH_MODE_QUEUE.md`: parked items for the user's High pass.
