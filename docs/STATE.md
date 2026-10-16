# TransportLah resume state

Updated: 2026-10-16 (Asia/Calcutta).

## Current outcome

The user-selected High pass resolved H01-H03. The latest ten-item Medium batch is complete: F03,F04,F05,F06,I03,I06,I07,V02,V03,R02. PLAN has30/87 completed engineering tasks; live/company-provider/device and full-MVP acceptance remain separately gated. No new High item was parked.

- H01: original seven weights, conservative missing-data/validity rules, independent score/tier/reward/ranking/contest eligibility and bus/rail contract. Twelve generated policy checks.
- H02: versioned native geography schema and matching GiST queries; geometry quality/source/stop occurrences; independent arrival ETA/capture/position time. Actual PostGIS metre-boundary, default-planner index and 2,000-pair spherical differential checks.
- H03: asymmetric provider JWT validation, fixed bounded JWKS, server-owned identity/membership mapping, non-owner commuter RLS, worker-only atomic settlement, daily-cap serialization and exact immutable reversals. Generated cryptographic and actual-login/concurrency database tests.

Opt-in authenticated read endpoints now cover profile, owner ride/wallet and tenant reviewer audit records. COMMUTER_API_ENABLED defaultsfalse and requires separate non-owner DB plus provider configuration. Score-submission, settlement and ride-mutation HTTP endpoints remain closed. Health/readiness still advertise verification_enabled=false. The ingestion credential is server/operator-only.

## Evidence and repository

Private repository: https://github.com/isearchxsolve/transportlah, branch codex/transportlah-foundation. Final execution identity and receipt hashes are recorded in docs/HIGH_PASS_RECEIPT.md and receipts/cloud_high/checks.json; local execution is separate in receipts/high_local/checks.json.

Real cloud PostgreSQL/PostGIS/Redis runs now exist. The initial run failed a SQL modulo typo in a generated index test; it was corrected and complete later runs passed. No local Docker installation was needed. The laptop still has no Docker/Flutter executables; the product Docker image, iOS/Android builds and deployment have not been executed.

All nine archived seed files and available originals remain byte-identical. The eight-test historical master suite remains unchanged. The stop44009/service190 historical capture (2026-10-10T21:42:59.758498+00:00) preserves its original hash/time and Monitored=0/zero positions. It is not a live handshake or passenger proof.

Generated mathematical, cryptographic and database records are TEST_VECTOR evidence. The user withdrew prior AGENTS.md instructions before this High pass; earlier synthetic-test/hardware restrictions no longer apply. Genuine captures and generated tests remain separate. No prior AGENTS.md instructions are active.

Latest Medium catalog batch: tested source4b24bfdf802805b1b9b04ce8441f759396b0b29a, CI38664361496 passed71 tests with zero skips and actual PostGIS/Redis readiness. Source/output artifact hashes verified; preserved in receipts/catalog_cloud. Local receipts/catalog_local record45 passing backend cases plus18 explicit database skips and the unchanged8 master checks. The real catalog collector exited1 for absent LTA key before creating a capture. See docs/MEDIUM_CATALOG_RECEIPT.md.

## Exact next implementation work

1. Implement ride lifecycle/start/ping/end mutations (V09) using the completed identity/read boundary and transactional idempotency; never accept client scores.
2. Execute the implemented paginated catalog collector/importer (I05 partial) with the company LTA key; review genuine consistency before promotion. Catalog snapshots and chord geometry are immutable and versioned.
3. Boarding proximity and service/direction/occurrence checks V02/V03 are implemented/tested. Continue V04-V07 context/progression/motion/alighting and genuine field validation.
4. Provision the client-managed OIDC provider and separate DB logins; execute the real provider handshake before deployment. Role actions, HTTP ownership and human-identity access audit now pass; human fraud-case decisions/corrections and campaign product flows remain pending.
5. Build Flutter active-ride flows and execute separate simulator/build/device gates.

No fundamental item remains parked from this pass. Add a specific new entry if route ambiguity/signal fusion or final security review exposes a new complex question.

## External and product gates still open

- Company LTA key/authenticated capture, official catalog import and genuine multi-stop responses.
- Consented Singapore recordings, actual route geometry and bus/car/pedestrian/replay/rail field evaluation.
- Client OIDC provider, hosting, Apple/Google accounts and signing configuration.
- Client confirmation of provisional bus10/probable50%/gross-daily100 reward defaults and raw-retention48h with controlled review extension.
- Server factor evaluators, commuter/admin endpoints, human audit, retention, rankings/contests and remaining MVP features.
- Physical-device foreground/background GPS, Android/iOS builds, store/release submission and written acceptance.

The client access email remains an unsent draft in docs/EMAIL_DRAFT_CLIENT_ACCESS.md.

## Pointers

- docs/VERIFICATION_CONTRACT.md: deterministic evidence/score/tier and bus/rail rules.
- docs/SPATIAL_CONTRACT.md: geography/index/time/provenance and differential boundaries.
- docs/IDENTITY_REWARD_CONTRACT.md: trust, roles, RLS, settlement/reversal and acceptance boundaries.
- docs/API_CONTRACT.md: implemented operator/optional owner-wallet-reviewer reads and designed lifecycle/product endpoints, retry/clock/upload/action rules.
- docs/MEDIUM_TEN_RECEIPT.md and receipts/medium10_cloud: latest ten-item completion matrix,91 cloud tests with zero skips, authenticated service checks, source/output hashes and exact tested SHA.
- docs/EMAIL_DRAFT_PROGRESS_30_OF_87.md: detailed client progress email prepared for review; no message sent.
- docs/ACCESS_AND_READ_API.md: tested optional read/audit/role boundary, infrastructure configuration and evaluator semantics.
- docs/CATALOG_IMPORT.md and backend/app/catalog.py: bounded paginated captures, integrity/normalization, immutable snapshots and transactional import; no real-key capture or active-catalog promotion yet.
- backend/migrations/001_foundation.sql and tools/migrate.py: privileged versioned migration and grants.
- backend/tests/test_database.py: actual PostGIS/login/RLS/concurrency checks; local skips are not acceptance.
- docs/PLAN.md, DECISIONS.md, HIGH_MODE_QUEUE.md: updated task status and closed High entries.
- docs/REQUIREMENTS.md, DISCREPANCIES.md, COMMERCIAL_STATUS.md: original scope/client discrepancies.
