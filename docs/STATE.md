# TransportLah resume state

Updated: 2026-10-15 (Asia/Calcutta)

## User direction

The user authorized a fresh implementation if discrepancies justify it, requested the detailed checklist, and then chose Medium for routine execution with fundamentally complex items parked for a user-selected High pass. Follow `docs/HIGH_MODE_QUEUE.md`; keep independent routine work moving.

## Completed review/planning work

- Read the mission and readable files across the two TransportLah folders; inspected the actual PDFs and all distinct slides in the walkthrough video.
- Inventoried 85 project-folder files and 10 deliverable-folder files. Thirty JPEGs in `img` are corrupt duplicates; valid wireframes are in `img_proper`. Fifteen existing page PNGs are blank duplicates.
- Reviewed the October architecture PDF and proposal outside the project folder.
- Verified BusArrival field semantics against the official LTA guide and PostGIS units against official documentation.
- Reported scope/platform drift, scoring changes, arrival-candidate/ETA misuse, score-versus-contest eligibility ambiguity, unsupported speed discrimination, SQL unit/index concerns, and competing acceptance/commercial versions.
- Created the execution checklist in `docs/PLAN.md` and the decision register in `docs/DECISIONS.md`.
- Completed B00 as a source-review artifact: `docs/REQUIREMENTS.md` maps all ten must-haves, supporting requirements, exclusions, and acceptance evidence.
- Completed B01 as a source-review artifact: `docs/DISCREPANCIES.md` distinguishes scope changes, defects, ambiguous policy, and unproven claims.
- Recorded the reasoning workflow and parked H01 (B02-B03: verification policy and bus/rail evidence contract) for High; it is not resolved.
- Implemented the corrected ingestion foundation in `backend/app`: configuration, historical/live transports, separate arrival parsing, cache/coalescing, per-stop budgets, optional polling, protected API, structured logs, and health/readiness.
- Completed source/configuration scaffolding and B04/B06/B07/B08 documents. Preserved nine byte-identical seed archives; all available originals still match the manifest.
- Located a historical capture for stop 44009/service 190. Its stored payload hash matches; it is schedule-only with zero locations. The original live origin has not been independently reverified this session.
- Executed 14 new ingestion checks and the untouched eight-test master suite successfully. A real local HTTP burst completed 25 requests with 24 cached responses; source remains historical, no locations are present, and passenger verification is disabled.
- The real capture collector failed explicitly because no LTA key is configured. No new capture or fabricated fallback was produced.
- Prepared authenticated loopback-bound Docker services, pinned dependency files, and a manual cloud CI workflow. Docker/Flutter are unavailable locally; container/cloud/mobile builds are not claimed.
- Parked H02 (spatial representation/indexes/differential contract) and H03 (commuter identity/permissions/reward transactions) before their dependent work.

## Exact resume point

High next: H01, H02, H03 in dependency order. Routine work remaining needs current LTA credentials/genuine multi-stop captures and a real PostGIS/Redis/cloud host for its execution gates. After High contract decisions, implement the reviewed schema/auth and continue catalog/mobile/reward tasks. Do not copy the historical vehicle-trajectory logic.

Corrected ingestion source is implemented; no full milestone has been accepted. Local tests and actual local HTTP requests were executed. No current authenticated LTA handshake, successful PostGIS/Redis gate, cloud workflow run, iOS/Android build, device ride, store upload, or production deployment has been performed.

## Current external-state unknowns

- Current LTA key validity and authentic-capture availability.
- Consented Singapore device recordings and field-test availability.
- Apple/Google account and signing availability.
- Client hosting configuration and current signed commercial scope.

These are unknown, not confirmed absent. Independent contract/design tasks can proceed.

## Evidence and instructions to preserve

- Leave the existing master suite unchanged: `D:/anonym/deliverables/transportlah/test_spatial_engine.py`.
- Preserve seed/demo artifacts for traceability; build corrected source separately.
- Never manufacture coordinates, timestamps, or LTA payloads to produce acceptance evidence.
- Offline replay must preserve original authentic captured values and their provenance.
- Build scope is the original MVP working baseline. The later M1-M3 pilot is not complete product acceptance.

## File pointers

- `docs/PLAN.md`: ordered task IDs, next five actions, stage gates, dependencies, and sources.
- `docs/DECISIONS.md`: adopted engineering constraints versus proposed/unresolved decisions.
- `docs/REQUIREMENTS.md`: original-spec traceability and product acceptance map.
- `docs/DISCREPANCIES.md`: source-review finding register and remediation tasks.
- `docs/HIGH_MODE_QUEUE.md`: the user-selected Medium/High workflow and exact parked H01 question.
- `docs/ASSUMPTIONS.md`, `docs/EVIDENCE_INVENTORY.md`, `docs/COMMERCIAL_STATUS.md`: completed independent source/configuration inventories.
- `backend/app/main.py`: ingestion API and health/readiness, not a verification/reward API.
- `backend/app/models.py`: separate arrival candidates, source timestamps, quality flags, and absent position observation time.
- `backend/app/ingestion.py`: single-process cache, per-stop budget, coalescing, and lifespan polling.
- `backend/tests/test_ingestion.py`: 14 new meaningful checks using the unchanged historical capture.
- `receipts/local_ingestion_smoke.json`: actual local HTTP receipt; historical replay and dependency failures are explicit.
- `D:/anonym/war-log/transportlah/TransportLah_Final_Proposal.pdf`: original product requirements.
- `D:/anonym/TransportLah_Implementation_Plan.pdf`: October architecture and commercial blueprint.
- `D:/anonym/deliverables/transportlah/lta_datamall_proxy.py`: existing arrival-candidate/ETA trajectory defect.
- `D:/anonym/deliverables/transportlah/spatial_verification.py`: current Haversine score and degree-based SQL generator.

Update these documents before ending an implementation session. Add verified line references when implementation source exists. Do not record stale line numbers or unearned completion claims.
