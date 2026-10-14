# Parked High-reasoning work

Updated: 2026-10-15 (Asia/Calcutta)
User instruction: Continue routine work in Medium. When an item needs High reasoning, park it for the user to switch to High and then complete the parked work.

## Operating protocol

1. Keep independent routine implementation moving in Medium.
2. Park a specific problem when resolving it requires fundamental algorithm/policy reasoning, ambiguous evidence, or a consequential design trade-off.
3. Record the question, source files, known constraints, dependent tasks, required output, and acceptance checks.
4. Tell the user when a parked item becomes the next required dependency; do not claim to have changed the reasoning setting.
5. Once the user switches to High, read this queue and resolve the selected item before marking it complete. Record the decision, implementation where appropriate, and proof.
6. A High review does not substitute for authentic data, executed checks, physical-device proof, or client scope decisions.

## H01 - Verification policy and bus/rail evidence contract

Status: PARKED FOR HIGH. Source review is complete; design resolution is pending.
PLAN dependencies: B02-B03, V02-V09, V14, R01, R09-R11.

Question: How should the original seven weighted factors, four confidence classes, evidence tiers, reward eligibility, and per-contest trust rules be implemented without overstating what phone and public-feed evidence can prove?

Read:

- `docs/REQUIREMENTS.md` and `docs/DISCREPANCIES.md` (X01-X05, X11-X12).
- `D:/anonym/war-log/transportlah/TransportLah_Final_Proposal.pdf`, sections 6, 9, and 13.
- `D:/anonym/TransportLah_Implementation_Plan.pdf`, section 4.
- `D:/anonym/deliverables/transportlah/spatial_verification.py` and `lta_datamall_proxy.py` as historical defect references.
- `docs/DECISIONS.md`, D03-D04, D07-D08, D10, D12-D13.

Known constraints:

- NextBus slots are different arrival candidates; ETA is not position observation time. No guaranteed continuous same-vehicle trajectory is established by this feed contract.
- The spec's 80/60/40 class boundaries and seven weights are product requirements; calibration and factor evaluation need explicit assumptions and field validation.
- Missing/unreliable evidence must not inflate confidence or earn stronger trust by changing the denominator silently.
- Bus/car speeds overlap; nearby pedestrians and replayed GPS remain evidence limitations.
- Rail/tunnel behavior needs a separate evidence path.
- Contest evidence requirements must be configured independently of score; strong device proof cannot be inferred from a high score.
- No manufactured coordinates/payloads, altered master tests, or invented field outcomes.

Required output:

- `docs/VERIFICATION_CONTRACT.md` with factor inputs, evaluation states, weights, hard validity gates, unavailable-data policy, score classes, evidence tiers, reward/ranking/contest rules, and explanations.
- Separate bus/rail evidence capabilities and explicit unsupported cases.
- Decisions distinguishing engineering defaults from questions requiring client resolution.
- A meaningful validation plan using authentic evidence; record which cases cannot yet be verified.

Acceptance: Rules are internally consistent, traceable to the original scope, do not confer unsupported proof, and are specific enough to implement without copying the seed's faulty trajectory model. Do not mark the policy field-validated merely because its design is written.

Medium work that can proceed while H01 is parked: B04, B06-B08, folder/configuration scaffolding, authentic-capture inventory, health/logging setup, and parsing/cache work that does not depend on the scoring policy.

## H02 - Metre-correct spatial schema, indexes, and differential contract

Status: PARKED FOR HIGH. No corrected spatial migration is implemented.
PLAN dependencies: V00-V01, V05, V12-V13, F04 spatial portion.

Question: Which geometry/geography representation, route provenance, temporal model, and query/index expression can implement the reviewed corridor contract in metres, with meaningful differential checks and no invented same-vehicle trajectory?

Read `docs/DISCREPANCIES.md` X02/X06/X07/X14, the original schema/SQL generator in `reference/seed`, and the outcome of H01. The only identified capture is schedule-only with zero coordinates; it cannot validate a spatial corridor or throughput claim.

Required output: a reviewed schema/query plan, matched index strategy, spherical/spheroidal comparison policy, authentic-corpus validation contract, and explicit unavailable evidence. Implement and test only what real PostGIS/corpus evidence can support. Keep field accuracy and benchmark claims pending until executed.

## H03 - Commuter identity, authorization, and reward transaction design

Status: PARKED FOR HIGH before mobile/user or reward endpoints are enabled.
PLAN dependencies: F04-F05, C01, R00-R02, R07-R11.

Question: How should provider-backed user identity, ride ownership, role/tenant boundaries, idempotent awards/reversals, and contest trust be enforced together without allowing duplicate credits or cross-user access?

The current service token protects server/operator ingestion only. It is not a mobile credential and must not be embedded in Flutter. Read H01, original roles/entities, `docs/REQUIREMENTS.md`, and the new backend boundary in README.

Required output: an implementable identity/permission contract, durable reward transaction model, failure/concurrency cases, and genuine integration/security checks. No product-auth or reward-integrity acceptance is claimed now.

## Future candidates, not yet parked

- Route progression under uncertain geometry/GPS and signal fusion (V05-V06).
- Final security and evidence review if findings require deeper reasoning (A02-A04).

Add a concrete queue entry when one becomes active; do not label every routine implementation task as requiring High.
