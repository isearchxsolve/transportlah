# TransportLah execution checklist

Date: 2026-10-15 (Asia/Calcutta)
Status: Corrected ingestion foundation implemented and checked locally. Full product, live multi-stop acceptance, cloud dependency checks, and High-policy work remain pending.

## Working basis

Use the original product specification as the product baseline: iOS and Android, bus and rail context, lightweight ride verification, Green Points, verified-only leaderboards, admin promotions, contest registration, basic fare comparison, CO2 estimates, and basic fraud controls. The later three-milestone mission is an intermediate engineering pilot, not acceptance of the complete MVP.

Flutter, a modular FastAPI backend, PostgreSQL/PostGIS, and Redis are the proposed implementation direction. Preserve the existing demo and master tests as historical reference. Build corrected implementation separately. Do not represent this backlog as signed client scope, a new commercial offer, or a delivery-date commitment.

## Rules for every task

- Never fabricate LTA responses, device coordinates, timestamps, credentials, or live proof.
- Offline replay must use authentic captured responses with provenance; preserve original values and times.
- Do not change, weaken, delete, or disable the existing master tests.
- Add meaningful tests for new behavior without misrepresenting existing synthetic test vectors as real observations.
- Distinguish source review, automated test results, live API proof, physical device proof, and client acceptance.
- Keep keys and raw device location recordings private, out of Git and public logs. Obtain consent before field capture.
- Run heavy builds, performance tests, and device-build workloads in cloud CI. Keep local work light.
- Do not send client messages, incur fees, or publish releases merely because they appear in this backlog.
- User-selected workflow: routine work in Medium; park fundamentally complex items in `docs/HIGH_MODE_QUEUE.md` for the user to switch to High. Keep independent work moving; never claim to change the setting automatically.

## Next five actions

1. High H01: Resolve B02-B03 verification policy, evidence tiers, and bus/rail contract.
2. High H02: Resolve the metre-correct spatial migration/query/index and authentic differential contract.
3. High H03: Resolve user authentication, ownership/roles, and reward transaction design.
4. I00-I01: Verify a real configured LTA key and capture multiple genuine stop/service responses when credentials are available.
5. F03/F08: Execute real PostGIS/Redis/container/cloud gates when an appropriate host and runner allowance are established; then continue I05 catalog ingestion and policy-dependent implementation.

## Stage 0: Reconcile the contract before implementation

- [x] B00 Map every original MVP requirement to implementation tasks and acceptance evidence; include all ten must-haves and explicit exclusions. Receipt: `docs/REQUIREMENTS.md`; mapping completion is not product acceptance.
- [x] B01 Record discrepancies across the original spec, architecture PDF, commercial drafts, later mission, demo, and walkthrough video. Receipt: `docs/DISCREPANCIES.md`; proposed remedies remain unimplemented.
- [ ] B02 Separate the 0-100 weighted score from verification tier, points awarded, public ranking eligibility, and contest eligibility.
- [ ] B03 Define separate bus and rail verification inputs; identify what cannot be established by public feeds or phone GPS alone.
- [x] B04 Mark boarding radius, corridor width, time tolerances, sampling cadence, speed features, and retention rules as configurable assumptions pending validation. Receipt: `docs/ASSUMPTIONS.md`; field calibration remains pending.
- [ ] B05 Draft the API contract for authentication, stops/services, arrivals, ride start/ping/end/status, rewards, rankings, and admin operations.
- [x] B06 Inventory credential and field-data availability without exposing secret values; distinguish available, unverified, absent, and externally required. Receipt: `docs/EVIDENCE_INVENTORY.md`.
- [x] B07 Record the current commercial baseline as unresolved if documentary evidence does not establish it; reconcile code ownership, milestones, and payment terms separately from engineering. Receipt: `docs/COMMERCIAL_STATUS.md`; no current signed contract is asserted.
- [x] B08 Hash and inventory original seed files and the untouched master test suite; record which historical claims lack supporting artifacts. Receipts: `docs/SEED_MANIFEST.json`, `tools/verify_seed.py`, discrepancy X10.

Gate: Every mandatory feature has an acceptance criterion; product scope and unresolved decisions are explicit. A pilot is not mislabeled as full MVP completion.

## Stage 1: Establish a secure, reproducible foundation

- [x] F00 Create `backend/app`, `backend/tests`, `backend/migrations`, `mobile`, and `docs` without overwriting historical artifacts. Mobile/migrations are boundary documentation, not completed clients/schemas.
- [x] F01 Pin backend dependencies and document lightweight local setup and cloud build commands. Receipts: requirements files and README.
- [x] F02 Define environment configuration and a secret-free example file; ignore real credentials and private captures. Private .env generated without printing credentials; reviewed project files contain no generated secret values.
- [ ] F03 Configure PostgreSQL/PostGIS and Redis with authenticated access and restricted development exposure.
- [ ] F04 Add versioned migrations for users, stops, route patterns, rides, observations, verification outcomes, and audit events.
- [ ] F05 Implement authentication and distinguish commuter, campaign manager, fraud reviewer, and administrator permissions.
- [ ] F06 Add request validation, authenticated ownership checks, request IDs, and structured logs with secret/location redaction.
- [x] F07 Add health/readiness endpoints that distinguish process health, database health, and upstream availability. Local HTTP health=200, readiness=503 truthfully reports unavailable PostGIS/Redis; no dependency success claimed.
- [ ] F08 Establish backend CI, migration checks, Flutter build checks, and immutable master-test execution; disclose failures honestly.
- [x] F09 Define receipt storage: commit SHA, test commands/results, capture provenance, deployment identity, known limits, and hashes. Receipts: `receipts/checks.json`, raw check outputs, local HTTP smoke, seed manifest, and the implementation commit recorded in STATE. Local execution is distinguished from absent live/cloud/device acceptance.

Gate: A clean checkout can start the backend, apply migrations, authenticate, and pass appropriate foundation checks. No plaintext production secrets or unauthenticated database exposure.

## Stage 2: M1 pilot - authentic transit ingestion (nine tasks)

- [ ] I00 Verify a configured LTA key against the real endpoint without printing it; preserve sanitized request/response metadata and original capture time.
- [ ] I01 Capture authentic BusArrival responses for multiple real stops and record endpoint, parameters, response hash, and provenance.
- [x] I02 Parse NextBus/NextBus2/NextBus3 as separate arrival candidates; preserve ETA separately from fetch time and any documented observation time. Exercised on unchanged historical capture; zero locations remain unavailable and observation time is not invented.
- [ ] I03 Handle Monitored, empty fields, absent services, malformed upstream responses, and estimated-location uncertainty without invented values.
- [x] I04 Implement active-stop polling, per-stop limits, request coalescing, TTL caching, timeouts, and bounded backoff. Local replay/burst/elapsed-time/lifespan checks pass; live HTTP error/backoff integration and distributed coordination remain unverified/unimplemented respectively.
- [ ] I05 Import paginated BusStops, BusServices, and BusRoutes; preserve direction, stop sequence, visit information, and source version.
- [ ] I06 Implement LIVE_NETWORK and authentic-capture replay transports using the same parser and validation path; fail clearly when capture data is absent.
- [ ] I07 Add ingestion checks for cache expiry, duplicate requests, multiple stops, service filtering, and upstream failure handling; use genuine captures and actual request-count receipts.
- [ ] I08 Document current upstream contracts and limitations; demonstrate multi-stop processing and rate-limit behavior with live proof clearly distinguished from replay results.

Gate: Multiple real stops are processed correctly; rate-limit behavior is evidenced; replay is traceable to authentic captures. ETA is never treated as vehicle-position observation time, and three different buses are never joined into one trajectory.

## Stage 3: M2 pilot - verification against actual route and ride evidence

- [ ] V00 Design route geometry provenance; do not describe straight lines between stops as surveyed road paths.
- [ ] V01 Choose metre-correct PostGIS geography or a suitable projected coordinate system; create indexes matching the actual query expressions.
- [ ] V02 Implement boarding-stop proximity using reported device accuracy and configurable tolerances.
- [ ] V03 Validate selected service, direction, and stop sequence against imported official records.
- [ ] V04 Evaluate live/recent arrival context with freshness and Monitored quality; do not claim it proves passenger presence.
- [ ] V05 Evaluate forward route progress and corridor fit; handle stops, detours, GPS gaps, and ambiguous parallel corridors conservatively.
- [ ] V06 Evaluate speed and motion features as supporting signals; do not classify bus versus car using the 12-65 km/h range alone.
- [ ] V07 Validate downstream alighting and meaningful journey progression/duration.
- [ ] V08 Compute the seven weighted factors with explainable outcomes; define unavailable evidence without inflating scores.
- [ ] V09 Implement ride lifecycle, event ordering, idempotency, replay flags, and conservative rejection/low-confidence outcomes.
- [ ] V10 Acquire consented, genuine Singapore bus recordings with boarding/alighting notes and corresponding LTA capture context; do not invent missing traces.
- [ ] V11 Add new acceptance cases from authentic recordings, including genuine negative/ambiguous examples where available; leave the master suite unchanged.
- [ ] V12 Run differential comparisons on unaltered recorded points, thresholds, ordering, and subsets; align sphere/spheroid math and boundary tolerances explicitly.
- [ ] V13 Inspect query plans and benchmark representative recorded workloads in cloud infrastructure; report hardware, dataset, concurrency, latency, and uncertainty.
- [ ] V14 Define rail-specific station, transfer, tunnel/GPS-loss, and journey-duration evidence; validate separately before enabling verified rail rewards.

Gate: A genuine recorded bus ride produces an explainable result through PostGIS. Index usage and performance are measured. Pedestrian, car, replay, missing-data, and rail limitations remain disclosed. A corpus differential battery is not falsely called the requested synthetic-coordinate fuzz battery.

## Stage 4: M3 pilot - one complete ride on Flutter iOS and Android

- [ ] C00 Scaffold the shared Flutter app and align navigation, colors, typography, and components with the supplied wireframes.
- [ ] C01 Implement login, secure session storage, and signed-out/error states.
- [ ] C02 Implement nearby stops and live arrival screens with freshness, loading, unavailable-data, and schedule-estimate indicators.
- [ ] C03 Implement explicit Start Green Ride, stop/service selection, and consent/permission explanations.
- [ ] C04 Capture device location only during an active ride; use accuracy-aware, battery-aware sampling and stop capture at ride end.
- [ ] C05 Implement persistent local upload queue, reconnect/retry behavior, event IDs, and safe handling of interrupted sessions.
- [ ] C06 Implement active ride, end ride, pending verification, result explanation, and history screens.
- [ ] C07 Connect the app to the verification API; ensure a failed/repeated upload cannot duplicate a ride or reward.
- [ ] C08 Configure cloud macOS iOS and cloud Linux Android builds; document signing as an external configuration dependency.
- [ ] C09 Run simulator/emulator API integration checks using authentic replay; separately collect physical-device foreground/background, connectivity, and battery receipts.
- [ ] C10 Write reproducible TestFlight/Play internal-test runbooks; record build-ready, signed, uploaded, installed, and field-tested as separate states.

Gate: A consenting tester can start, record, finish, and inspect a real bus ride. Both platform builds are evidenced. Simulator success does not establish background GPS behavior or passenger verification on physical devices. This is an intermediate pilot, not full product completion.

## Stage 5: Complete the rewards and campaign product

- [ ] R00 Implement an append-only points ledger with transaction-safe, idempotent awards and auditable reversals/adjustments.
- [ ] R01 Configure verified/probable/low-confidence reward rules separately from ranking and contest trust requirements.
- [ ] R02 Implement wallet balance and history derived from the ledger; reconcile duplicate events and failed transactions.
- [ ] R03 Implement streaks, badges, and levels with configurable rules and reproducible calculations.
- [ ] R04 Implement verified-only rankings with display names, period rollover, tie rules, and privacy preferences.
- [ ] R05 Rebuild Redis rankings from durable PostgreSQL records and verify reconciliation after cache loss.
- [ ] R06 Implement the agreed global/weekly/friends/company/school views; map any additional original-spec views explicitly rather than silently omitting them.
- [ ] R07 Build the admin portal with role-restricted user/ride search and verification explanations.
- [ ] R08 Implement promotion drafts, scheduling, publishing, expiry, sponsor ownership, and banner upload validation.
- [ ] R09 Implement contest rules, registration, eligibility, scoring, closure, and results with audit logs.
- [ ] R10 Block stronger-trust contests until the required QR/NFC/device-integrity evidence is implemented and verified; do not equate a high score with attestation.
- [ ] R11 Implement the fraud review queue, decisions, point corrections, and high-value winner review workflow.
- [ ] R12 Implement agreed notifications and reward-fulfilment tracking without expanding into the excluded payment wallet/voucher marketplace.

Gate: An accepted ride awards points once, updates an eligible ranking, and participates only in permitted contests. An authorized administrator can manage a campaign and review suspicious rides. Ledger recovery and access-control checks pass.

## Stage 6: Complete utility, rail context, and privacy controls

- [ ] U00 Implement basic journey candidates for the agreed bus/MRT/mixed modes with service/stop/transfer validation and explicit coverage limits.
- [ ] U01 Implement versioned fare tables, fare profiles, transfer rules, and estimated-fare labels with current authoritative-source provenance.
- [ ] U02 Implement route trade-off cards for time, estimated fare, crowd context, and rewards; do not imply unavailable live predictions exist.
- [ ] U03 Integrate train alerts, station crowd context, and accessibility notices; keep these separate from proof of an individual rail ride.
- [ ] U04 Complete and field-validate the rail verification method before enabling verified train/mixed-mode rewards.
- [ ] U05 Implement CO2 estimates with documented factors, units, assumptions, and source versions; display estimates as estimates.
- [ ] U06 Implement raw-trace expiry/downsampling, flagged-review retention, access restrictions, and deletion checks; reconcile the original retention exceptions.
- [ ] U07 Implement profile privacy controls, display-name rankings, and active-ride-only location collection disclosures.

Gate: Every original MVP utility requirement is traced to evidence or explicitly unresolved. Retention actually executes; train context is not mistaken for train passenger proof.

## Stage 7: Prove and hand over the complete MVP

- [ ] A00 Run all ten original MVP must-haves through a traceability-based acceptance checklist.
- [ ] A01 Run the untouched master suite and new meaningful regression/integration checks; retain exact outputs and hashes.
- [ ] A02 Check authentication, ownership isolation, admin privileges, API validation, rate limiting, and secret/log exposure.
- [ ] A03 Conduct a consented Singapore physical-device pilot across bus/rail, connectivity, accuracy, and background-location conditions with real observations.
- [ ] A04 Report observed verification outcomes and limitations without claiming unsupported accuracy, anti-spoofing guarantees, or universal mode coverage.
- [ ] A05 Run cloud load/latency checks on representative genuine datasets; measure rather than assume ranking/query performance.
- [ ] A06 Exercise backup/restore, migration rollback/recovery, points reconciliation, retention execution, and operational alerts.
- [ ] A07 Resolve acceptance-blocking defects; record remaining limitations and any explicit stakeholder acceptance separately.
- [ ] A08 Prepare signed iOS/Android builds, store metadata, location/privacy disclosures, and account configuration under the client's provisioned accounts.
- [ ] A09 Submit authorized internal-test/store releases and collect upload, installation, review, and physical-device receipts separately; do not mark pending credentials/review complete.
- [ ] A10 Deliver source, configuration instructions, architecture decisions, deployment/recovery runbooks, and an honest walkthrough with SHA-256 manifests.
- [ ] A11 Obtain written acceptance against the reconciled scope and preserve the exact delivered version and evidence set.

Gate: The original agreed MVP is proven against genuine data on physical devices, client-owned configuration is documented, and client acceptance is recorded. Source-ready, CI-green, uploaded, store-approved, and production-accepted are different statuses.

## Dependencies and boundaries

- Credential availability is not established by this planning pass. The files referring to a previously registered key are historical claims, not a current authenticated handshake receipt.
- Genuine multi-stop captures and consented Singapore device recordings are external evidence dependencies when absent.
- Apple/Google accounts, signing, hosting, and release authorization must be available before dependent release actions.
- Any mandatory synthetic-coordinate fuzz requirement conflicts with the current zero-manufacture instruction. Use authentic corpus comparisons and mark the unresolved acceptance difference honestly; do not generate fake coordinates to satisfy it.
- The original score/tier/contest language contains ambiguity. Resolve it in an explicit policy contract; do not silently loosen trust requirements.
- No calendar, budget, IP transfer, scope change, field accuracy, or performance guarantee is established by this backlog.

## Source references

- Original product specification: `D:/anonym/war-log/transportlah/TransportLah_Final_Proposal.pdf`, especially sections 6, 9, 13, and 15.
- October architecture blueprint: `D:/anonym/TransportLah_Implementation_Plan.pdf`, especially sections 4, 6, and 7.
- October proposal: `D:/anonym/TransportLah_Implementation_Plan.md`.
- Delivery plan: `D:/anonym/war-log/transportlah/DELIVERY-PLAN-TRANSPORTLAH.md`.
- Later pilot mission: `D:/anonym/deliverables/transportlah/SOL_MISSION_PROMPT.md`.
- Seed code/master suite: `D:/anonym/deliverables/transportlah/`.
- LTA current official API guide checked on 2026-10-15: https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf (version 6.10, 1 Oct 2026).
- PostGIS distance semantics: https://postgis.net/docs/ST_DWithin.html.
