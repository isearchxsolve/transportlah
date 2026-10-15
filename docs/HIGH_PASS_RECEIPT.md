# High pass execution receipt

2026-10-15. H01, H02 and H03 are resolved as engineering decisions plus implemented/tested foundations. No full MVP, live LTA, rail, device or client acceptance is asserted.

Final tested source: `e25420c5351529fb019b8b2b4675847b27730de6` on private `isearchxsolve/transportlah`, branch `codex/transportlah-foundation`.

Executed cloud run: [38662867180](https://github.com/isearchxsolve/transportlah/actions/runs/38662867180), SUCCESS. Receipt timestamp: 2026-10-15T00:57:30.216122+00:00.

## Executed results

| Check | Actual result |
| --- | --- |
| Backend checks | 49 passed: ingestion14, policy12, identity8, actual-database15; zero skips |
| Unchanged historical master | 8 passed; originals/archive hashes unchanged |
| Database | PostgreSQL16.9, PostGIS3.5.2; migration rerun/hash checks, actual restricted login/RLS grants |
| Reward integrity | 12 concurrent retries return one award; 15 different rides respect100 gross daily cap; eight concurrent reversals produce one exact negative; inconsistent/conflicting/test-production settlement rejected |
| Metre boundaries | Spheroid149m/151m against150m radius, route100/150m differences, weak-geometry exclusion and absent position-time exclusion pass |
| Differential | 2,000 generated spherical pairs; max absolute Python/engine error7.159542292356491e-09m, below1mm contract |
| Index | Default-planner EXPLAIN ANALYZE uses stop_location_gist on10,000 generated stops; no planner coercion |
| Readiness | HTTP200 with actual reachable PostGIS and Redis, historical replay source, verification_enabled=false |
| Dependency/syntax | pip check and compileall passed |

The first cloud run38662245576 failed a generated-index SQL modulo typo. It was fixed; subsequent complete runs passed. The failure was not suppressed or relabelled as success.

Local results are independently saved in `receipts/high_local`: 34 backend checks passed and15 database cases explicitly skipped; original8 passed. Local success does not establish database execution. Cloud executed all57 without skips.

## Preserved proof

Downloaded artifact files are in `receipts/cloud_high`. `checks.json` contains exact executed source/output SHA-256 values, run ID and tested commit. Every output hash was recomputed against downloaded bytes, and all29 source hashes were compared to exact Git blobs at the tested commit. All matched. `provenance.json` preserves run identity, engine versions, differential result and full executed index plan.

The cloud/database/cryptographic points, tenants and rides are explicitly generated TEST_VECTOR cases in a disposable database. They are not real LTA positions or device recordings. Existing authentic-labelled historical capture remains unchanged and separate.

H01 output: `docs/VERIFICATION_CONTRACT.md` and pure policy core. H02 output: `docs/SPATIAL_CONTRACT.md`, geography schema/queries and real-engine checks. H03 output: `docs/IDENTITY_REWARD_CONTRACT.md`, OIDC/ownership components and immutable settlement functions. STATE and PLAN record the next implementation work and external gates.

Remaining: genuine official catalog/evaluator input, managed-provider handshake/HTTP integration, human admin audit and correction flows, Flutter, current LTA/device proof, representative load tests, retention/recovery and complete MVP acceptance. The client email remains an unsent draft.
