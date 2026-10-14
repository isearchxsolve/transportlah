# TransportLah discrepancy register

Date: 2026-10-15 (Asia/Calcutta)
Purpose: Complete PLAN task B01. This register records source-review findings and proposed remedies; it does not assert those remedies are implemented.

Source abbreviations:

- SPEC: `D:/anonym/war-log/transportlah/TransportLah_Final_Proposal.pdf`.
- ARCH: `D:/anonym/TransportLah_Implementation_Plan.pdf` (October architecture blueprint).
- PROPOSAL: `D:/anonym/TransportLah_Implementation_Plan.md`.
- PILOT: `D:/anonym/deliverables/transportlah/SOL_MISSION_PROMPT.md`.
- SEED: `D:/anonym/deliverables/transportlah/`.

| ID | Type | Source conflict / gap | Consequence | Proposed resolution / tasks |
| --- | --- | --- | --- | --- |
| X00 | Scope/platform change | SPEC/ARCH describe the full iOS+Android reward/campaign MVP; PILOT ends at a native Swift iOS verification client. | Pilot completion cannot fulfil the full product or Android obligation. | Preserve the original MVP map; shared Flutter proposal; distinguish pilot from acceptance. B00, C00-C10, A00. |
| X01 | Verification model change | SPEC section 6/ARCH section 4 use seven weighted factors and confidence classes; PILOT/SEED use a >=75% spatial/time match ratio. | A 100% ping match does not establish the original confidence policy. | Specify a new policy contract and keep old test semantics intact as historical reference. B02, V02-V09. |
| X02 | Incorrect upstream semantics | `lta_datamall_proxy.py:160` joins NextBus slots into a trajectory; lines 166/175 assign EstimatedArrival to trajectory timestamp. Official LTA documentation identifies different approaching buses and ETA. | False single-vehicle trajectory and incorrect temporal correlation. | Preserve each arrival candidate; keep ETA/fetch/observation timing distinct; route evidence is the proposed foundation. I02-I03, V00-V05. |
| X03 | Contest trust ambiguity | SPEC section 6.5 identifies Tier 3 stronger evidence; section 9.2 includes Tier 2+ examples. ARCH section 4 grants full public/sponsor eligibility to all 80-100 scores. | Score alone bypasses contest-specific trust requirements. | Define confidence, evidence tier, reward, ranking, and contest rules independently. B02, R01, R09-R11. |
| X04 | Unsupported discriminator | ARCH section 4 says 12-65 km/h rejects private-car speeds; fixed radii/time windows are introduced without field receipts. | Speeds overlap; genuine bus stops/congestion can be mishandled; thresholds are unvalidated. | Treat speed as supporting evidence and preserve configurable assumptions. B04, V06, V10-V13. |
| X05 | Missing mode-specific design | SPEC includes MRT/LRT/mixed journeys; ARCH's service/arrival checks and SEED are predominantly bus-specific. | Rail rewards would be unsupported if bus rules were reused. | Park rail evidence design; separately validate station progression, transfers, GPS-loss, and duration. B03, V14, U04. |
| X06 | Distance-unit defect | `spatial_verification.py:57` uses ST_DWithin on SRID-4326 geometry with a metre-labelled value; `schema_postgis.sql:52` instead casts to geography. | Degree-based SQL and metre-based calculations disagree. | Choose metre-correct representation and matched indexes; execute differential checks and inspect query plans. V01, V12-V13. |
| X07 | Index/performance proof gap | Seed indexes geometry while matching geography expressions; ARCH promises sub-millisecond/sub-5ms performance. | An index declaration does not prove the actual query uses it or meets latency targets. | High-review the query strategy; measure query plans and workload performance. V01, V13, A05. |
| X08 | Acceptance endpoint conflict | PILOT accepts source/CI/runbook pending credentials; MILESTONES.md accepts upload/install; full delivery plan requires original MVP and store/device acceptance. | Source-ready could be mislabeled delivered. | Preserve separate build/sign/upload/install/field/client states. C08-C10, A08-A11. |
| X09 | Authenticity gap | Seed embeds fixed vectors and demo-generated offset pings; labels alone do not supply original LTA/device capture receipts. | They cannot serve as real network/device proof. | Preserve historical inputs; acquire genuine captures/recordings for new evidence; no fabricated replacement data. I00-I01, V10-V11. |
| X10 | Historical evidence gap | Walkthrough video asserts fuzz results, directional/stationary checks, and live-capture evidence not supported by files in the reviewed folders. | Presentation claims exceed reviewable artifacts. | Inventory references and require execution/capture receipts before retaining claims. B08, A01, A04, A10. |
| X11 | Threshold inconsistency | Seed engine defaults to 60 seconds while pilot/schema describe 30 seconds; architecture boarding-arrival context uses +/-3 minutes. | Different concepts/settings are conflated. The +/-3 minute boarding-context window is not inherently a contradiction with a separate position-correlation window. | Name each threshold's meaning, units, source, and validation status. B03-B04. |
| X12 | Retention-policy ambiguity | SPEC permits 24-72h raw traces and a flagged-review exception; ARCH describes permanent purge within 48-72h; oldest plan says no raw GPS stored. | A purge promise could contradict review retention or actual collection. | Establish precise policy and enforce/test expiration, exceptions, access, and summary boundaries. U06-U07. |
| X13 | Commercial/IP versions | Older plan is INR 2 lakh/8 weeks/non-exclusive reuse; October proposal is SGD 15,000/8 weeks; Partha plan is INR 28 lakh/24 weeks/four resources; handover wording varies. | Documents cannot collectively establish a single current signed agreement. | Record authoritative documentary status; do not silently change pricing, staffing, ownership, or delivery dates. B07. |
| X14 | Fuzz requirement conflict | PILOT requests differential fuzz; current user instruction prohibits synthetic coordinates/payloads. | Generating fake coordinates to earn acceptance is unauthorized; corpus comparisons are a different test class. | Use authentic-corpus comparisons honestly and keep the unresolved requirement explicit. V12, D18. |

## Verified upstream references

- LTA guide checked on 2026-10-15, version 6.10 (1 Oct 2026), Bus Arrival section 2.1: https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf.
- PostGIS distance units and index-aware ST_DWithin behavior: https://postgis.net/docs/ST_DWithin.html.

The original specification is broadly coherent and the October architecture retains its core product. This register distinguishes later scope changes, implementation defects, ambiguous policy, and unproven targets rather than treating every difference as an error.
