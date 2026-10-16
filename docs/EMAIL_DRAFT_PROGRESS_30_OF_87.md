# TransportLah progress email — draft for review

To: Aveek Sengupta <aveek_rec@yahoo.co.in>
From: Kunal Das <isearch.xsolve@gmail.com>
Status: Prepared for review; not sent.
Suggested attachment: TransportLah_30_of_87_Engineering_Receipts_2026-10-16.zip

Subject: TransportLah engineering update — 30 of 87 checklist items completed, with receipts

Hi Aveek,

Following the engineering work started on 14 October, I wanted to share a detailed progress update with the supporting implementation and test receipts.

We have completed ten additional priority items, bringing the engineering checklist to **30 completed out of 87**. This tally includes requirements/design work and implemented backend components. The live-data, physical-device and full-product acceptance gates remain separately tracked in the delivery plan.

The latest completed batch covers the following:

| Item | What is complete |
| --- | --- |
| F03 — Database/cache access | PostgreSQL/PostGIS and Redis password authentication and restricted local/CI exposure. Tests confirm correct access succeeds and missing/incorrect credentials are rejected. |
| F04 — Versioned schema and audit | Migrations cover identities, memberships, stops/routes, rides, observations, verification, points and immutable human-identity access audit records. |
| F05 — Authentication and roles | Signed JWT validation, trusted database memberships and distinct commuter, campaign-manager, fraud-reviewer and administrator actions. Client-supplied role claims cannot grant privileges. |
| F06 — API ownership and validation | Authenticated owner/tenant boundaries, request IDs, request-size/input checks and structured logs that exclude credentials and location inputs. |
| I03 — Telemetry edge cases | Conservative handling of monitoring flags, empty/missing values, malformed responses, unavailable positions, upstream errors and retry limits. |
| I06 — Live/replay transport implementation | Both transport paths use the same parser, preserving payload/arrival semantics and clearly identifying historical replay. Live failures return explicit errors. |
| I07 — Ingestion regression checks | Cache expiry, duplicate-request coalescing, service filtering, missing-stop behavior, request counts and upstream failure checks. |
| V02 — Boarding proximity | PostGIS distance checks incorporate reported GPS accuracy and configurable tolerances. Ambiguous or poor-quality fixes remain unavailable evidence. |
| V03 — Service/direction validation | Selected service, operator, direction and downstream stop occurrences are checked against a fixed catalog version, including repeated visits to the same stop. |
| R02 — Wallet reads | Owner-only wallet balance/history derives from the durable points ledger. Tests reconcile duplicate settlement retries, failed transactions, reversals and pagination. |

**Test and execution receipts**

The final cloud run passed **91 tests with zero skips**: 83 backend checks and the original eight-test master suite. The backend checks include 24 tests against actual PostgreSQL/PostGIS with restricted database login roles. Redis authentication and real service readiness also passed, alongside migration, dependency, syntax and seed-integrity checks.

The security checks demonstrate that another user's ride/wallet cannot be retrieved, tenant boundaries hold, token role forgery cannot elevate access, and reviewer access is audited with the verified actor and request ID. Existing settlement tests continue to confirm one credit under concurrent retries and exact, non-duplicated reversals.

The original seed/master tests and the identified historical transit capture remain unchanged. Historical responses retain their original timestamps and quality flags. Generated mathematical/security test cases and stubbed HTTP-client checks are labelled separately from genuine network/device evidence.

**Evidence references**

- [Successful cloud execution](https://github.com/isearchxsolve/transportlah/actions/runs/38929431922)
- Tested implementation: 514dc15f21ba1d18dc02ade669d47241a8d126a1
- [Tested source snapshot](https://github.com/isearchxsolve/transportlah/tree/514dc15f21ba1d18dc02ade669d47241a8d126a1)
- Completion matrix: docs/MEDIUM_TEN_RECEIPT.md in the attached bundle.
- Exact run output, source/output SHA-256 values and task-ID list: receipts/medium10_cloud in the bundle.
- Updated checklist: docs/PLAN.md, showing 30/87 completed items.

The private repository links require access. The attached receipt bundle provides the checklist, implementation summary, test outputs, provenance and SHA-256 file manifest for review without repository access.

**Earlier completed work**

The previous 20 completed items comprise scope/requirements/discrepancy and assumption mapping (B00–B08), source/configuration/health/receipt foundations (F00, F01, F02, F07, F09), corrected arrival parsing/caching (I02, I04), geometry/policy foundations (V00, V01, V08), and separated reward/ranking/contest rules (R01). The new ten build on those foundations.

**Next steps and access needed**

The next implementation work is the active-ride upload/lifecycle flow and remaining transit-context, progression, motion and alighting evaluators, followed by the mobile integration and genuine ride validation.

Please arrange the company LTA DataMall AccountKey through a secure channel and access to the TransportLah AWS/GCP project, as covered in our proposal. Client identity-provider configuration will also be needed for the deployed login integration; I can help select/configure it within the agreed scope. Apple/Google signing accounts are needed for the later mobile delivery gates.

Current LTA/company-catalog collection, a real client-provider login handshake, physical-device ride testing and production deployment remain pending. The authenticated read APIs are opt-in and require explicit provider and non-owner database configuration. Points economics and GPS tolerances remain provisional until confirmed and validated.

I will continue attaching executed evidence to each completed batch so progress remains reviewable against the original MVP requirements.

Regards,
Kunal Das
isearch.xsolve@gmail.com
