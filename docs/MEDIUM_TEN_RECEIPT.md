# Ten priority Medium items: completion receipt

Date2026-10-16, Asia/Calcutta. Completed30/87 engineering checklist items: previous20 plus these10. The existing plan contains87 unique tasks; no task was deleted, split or weakened to change the total. This is engineering completion, with client/live/device milestones separately gated.

Tested source:514dc15f21ba1d18dc02ade669d47241a8d126a1. [Final cloud run38929431922](https://github.com/isearchxsolve/transportlah/actions/runs/38929431922): SUCCESS. Exact execution timestamp and all hashes are in receipts/medium10_cloud/checks.json and provenance.json.

## Completed items and receipts

| ID | Completed implementation | Executed proof |
| --- | --- | --- |
| F03 | Password-authenticated PostGIS/Redis, loopback development/CI bindings and separate runtime roles | access_controls.txt: valid access works, PostgreSQL explicitly rejects wrong password, Redis rejects absent/wrong password; actual readiness200 |
| F04 | Versioned migrations001–003 for identities/memberships/catalog/routes/rides/pings/verification/ledger and append-only human audit | Migration rerun checks; immutable audit records with actor/tenant/action/outcome/target/request/time; reviewer RLS/no-context rejection |
| F05 | Provider-signature JWT verification, database role/action engine and authenticated read HTTP boundary | Actual app DB login plus generated valid/invalid signed JWTs; spoofed token roles cannot elevate; commuter/campaign/reviewer/admin action checks |
| F06 | Current endpoint validation,256KiB body bound, UUID request IDs, owner/tenant checks and redacted logs/errors | Foreign/inaccessible IDs404, role denial403, invalid JWT401, invalid pagination422; chunked/declared/invalid length checks; credential/location redaction |
| I03 | Monitoring/empty/absent/malformed/uncertain telemetry and HTTP failures/backoff | Genuine unchanged capture plus explicitly generated edge cases; timeout/401/500/badJSON/oversize/invalid Retry-After tests |
| I06 | Both transports share one parser and preserve payload/ETA semantics, with provenance separation and no fallback | Identical original payload/hash/service records through stubbed live-client and genuine replay paths; missing replay/upstream errors remain failures |
| I07 | Ingestion regression battery for expiry/coalescing/scopes/multi-stop missing data and failures | Unchanged historical capture,25-request burst→one source read/24 cache hits, actual elapsed-time rate checks and HTTP-stub failure counts |
| V02 | Configurable PostGIS boarding proximity using reported accuracy | Real engine tests: inside/outside/ambiguous envelopes, poor accuracy, changed radius and test-catalog provenance fail-closed |
| V03 | Versioned catalog service/operator/direction/downstream occurrence validation | Imported TEST_VECTOR catalog checks correct direction/loop occurrences and rejects mismatched service/operator/stop/order; missing/test source unavailable by default |
| R02 | Owner wallet balance/history HTTP reads derived from immutable PostgreSQL ledger | Duplicate retries, cap/failed transactions, exact reversal and pagination reconcile; other users/tenants excluded; POST credit unavailable |

## Verification totals and provenance

Cloud:83 backend checks, including24 actual-database checks; original master8. Total91 passed, zero skips. Additional access-control/readiness, pip consistency, syntax and seed-integrity gates passed. The prior full cloud run38929038691 passed90 before the final malformed-length regression was added; final91 is the acceptance receipt for this batch.

Local:83 backend cases discovered,59 passed and24 actual-database cases explicitly skipped; original8 passed. Local skips are not database proof. Actual cloud PostGIS/Redis execution is the independent receipt.

All42 tested source hashes were compared to exact Git blobs at the tested SHA. All downloaded output hashes were recomputed and matched. The runner artifact uses receipts/cloud_high; its untouched files are stored locally under receipts/medium10_cloud, with that mapping recorded in provenance.json. completion.json lists the exact prior20 and new10 task IDs.

Seed/master and the original historical stop44009/service190 capture remain unchanged. Its old timestamp, schedule-only flags and unavailable positions are preserved. Generated edge mutations, catalog points, tenants, rides and signed identity tokens are TEST_VECTOR cases. Stubbed live-client tests do not establish an actual LTA handshake.

## Remaining external/product gates

Client LTA key/current genuine multi-stop/catalog import, client OIDC provisioning/real login handshake, hosting/signing, remaining ride/evidence/mutation flows, campaign/fraud screens, Flutter, representative field/load/recovery/retention and complete MVP acceptance remain pending. This batch enables optional read endpoints only; verification_enabled remainsfalse. Existing economics/thresholds are provisional, not field-calibrated or newly agreed client terms.

Client progress email: docs/EMAIL_DRAFT_PROGRESS_30_OF_87.md, prepared for review and not sent. Shareable evidence archive and file manifest are under handover; it contains whitelisted receipts/docs and excludes private credentials/raw device recordings.
