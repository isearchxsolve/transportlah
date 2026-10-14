# Original-spec requirement traceability

Date: 2026-10-15 (Asia/Calcutta)
Purpose: Complete PLAN task B00. This is a requirement/evidence map, not a product acceptance receipt.

Source: `D:/anonym/war-log/transportlah/TransportLah_Final_Proposal.pdf`, sections 6, 9-15. Acceptance descriptions below translate the spec into checks; unresolved policy questions remain explicit.

## Ten mandatory MVP features

| ID | Original requirement | Backlog tasks | Required acceptance evidence | Current status |
| --- | --- | --- | --- | --- |
| MVP01 | Lightweight ride verification | B02-B04, V00-V14, C03-C07 | A genuine consented ride is evaluated through an explainable seven-factor policy; the API distinguishes confidence class and evidence tier; genuine negative/ambiguous examples and limitations are reported. Rail is validated separately. | Policy parked for High review; corrected implementation absent. |
| MVP02 | Green Points wallet | R00-R03 | An eligible ride awards the configured points exactly once; balance/history reconcile with the durable ledger; repeated events and auditable reversals do not corrupt balances. | Not implemented. |
| MVP03 | Public verified-only leaderboard | R04-R06 | Only qualifying verified rides contribute; display names, period views, tie rules, and privacy work; Redis rankings can be recovered from PostgreSQL. | Not implemented. |
| MVP04 | Admin promotions | F05-F06, R07-R08 | An authorized manager can create, schedule, publish, expire, and manage only permitted promotions; commuter/unauthorized access is rejected; actions are auditable. | Not implemented. |
| MVP05 | Contest registration | R09-R11 | A user can register for a contest; its configured mode, dates, trust requirement, scoring, and eligibility are enforced; high-value results support review. | Trust policy unresolved; not implemented. |
| MVP06 | Fare-Smart Routes, basic | U00-U02 | Supported route alternatives display time and explicitly estimated fare with fare profile, transfer warnings, rule/source version, crowd context, and rewards where available. Unsupported options are disclosed. | Not implemented. |
| MVP07 | CO2 avoided estimate | U05 | Calculation exposes documented factors, units, baseline assumptions, and source versions; UI labels the result as an estimate. | Not implemented. |
| MVP08 | Live bus arrivals | I00-I08, C02 | Multiple real stops/services render authenticated LTA responses with correct arrival-slot, ETA, load, Monitored, freshness, empty/unavailable-data, caching, and rate-limit behavior. | Historical seed only; no current live receipt. |
| MVP09 | Train alerts and station crowd information | U03 | Supported lines/stations show authoritative alert/crowd context with timestamp/freshness and unavailable-data handling; context is not portrayed as passenger evidence. | Not implemented. |
| MVP10 | Basic fraud controls | V03-V09, R10-R11, A02-A04 | Duplicate/repeated rides, implausible movement, invalid service/stop, and replay flags are handled under explicit rules; suspicious claims enter review; stronger-trust contests require their configured proof. Limitations are disclosed. | Historical seed documents replay/pedestrian passes; production controls absent. |

## Supporting requirements

| Requirement | Source section | Tasks / dependency |
| --- | --- | --- |
| iOS and Android experience with the supplied product flow and wireframes | 11.1, 14 | C00-C10; Flutter is the proposed shared implementation. |
| User identity, login, profile, preferences, and display name | 11.2, 12, 13.2 | F05-F06, C01, U07. |
| User explicitly starts/ends an active ride; phase-aware GPS sampling stops after ride end | 5.4, 6.1-6.2, 13 | C03-C06; permission, battery, background behavior need physical-device evidence. |
| Bus, MRT/LRT, and mixed-mode journey support | 5.1, 8 | U00, U03-U04, V14; bus implementation does not establish rail coverage. |
| Rewards, streaks, badges, levels, profile impact, and history | 8, 14 | R00-R03, C06, U05-U07. |
| Global/period/friends/team/neighbourhood/mode/verified ranking views | 9.3 | R04-R06; trace view-by-view scope rather than silently omitting views. |
| Campaign roles, sponsor ownership, fraud review, exports, and announcements | 10 | F05-F06, R07-R12; details mapped into the API contract before implementation. |
| Temporary raw-trace retention, flagged-review exception, summary storage, and privacy controls | 13.2 | U06-U07; choose the definitive policy explicitly and prove deletion jobs execute. |
| Configuration under client-provisioned accounts, operating/recovery documentation, builds, and handover | Architecture proposal, not original product feature | F02, F08-F09, C08-C10, A06-A11; do not conflate account provisioning, successful build, upload, installation, and acceptance. |

## Explicit MVP exclusions (section 15.2)

1. Full fare-card integration.
2. Payment wallet or card top-ups.
3. Real voucher marketplace at launch.
4. Best-in-class turn-by-turn journey navigation.
5. Continuous GPS streaming or long-term raw GPS storage.
6. Advanced ML recommendations.

Do not interpret exclusion 5 as permission to collect location outside active rides. The exact active-ride sampling approach still needs platform and field validation.

## Policy questions before acceptance

- Confidence class and evidence tier are separate axes. Resolve section 6.5 stronger-trust eligibility against section 9.2 Tier 2 contest examples; do not automatically grant all contests at score >=80.
- Distinguish temporary raw-trace retention from flagged-review retention and long-term summaries.
- Define rail evidence under tunnel/GPS-loss conditions without pretending bus arrival checks apply.
- Freeze the agreed views, supported journey/fare profiles, and campaign fields in the scope contract; retain unresolved items in the map.
- The three-milestone pilot is an intermediate technical checkpoint. It does not cover this entire requirement table.

## Review boundary

All statuses above describe source review on this date. No newly executed tests, live handshake, physical ride, database run, build, or client acceptance is asserted.
