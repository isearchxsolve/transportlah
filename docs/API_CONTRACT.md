# TransportLah API contract v1

B05 design artifact, 2026-10-15. This document defines implementation work; only the health/readiness and operator-arrival endpoints listed below exist today. New commuter/admin endpoints remain closed until their auth, lifecycle, evidence and audit dependencies pass. Generated catalog tests are not live acceptance.

## Common boundary

Use HTTPS, JSON and UUID resource IDs. Every commuter/admin endpoint requires a provider bearer verified against the fixed issuer/audience/JWKS configuration. Tenant ID is explicit in the URL; resolve membership and identity from trusted server records. Never trust submitted user IDs, roles, score/tier/reward amounts, attestation booleans or token tenant claims. Unknown/inaccessible resources return404 to avoid enumeration. Missing/invalid bearer returns401; missing tenant/action permission403; unavailable dependencies503.

Generate/validate X-Request-ID and return it in every response. Log selected request metadata, never bearer/key/raw-GPS payloads. Errors use `{code, message, request_id, retryable}` without stack traces. Existing operator endpoints currently use their documented FastAPI detail shape; migrate them explicitly before asserting this new error contract.

Mutation requests carry an Idempotency-Key UUID bound to (tenant, verified user, operation). Store a canonical request digest with the durable result. Exact retries return the original status/body; changed requests under the same key return409. Event IDs additionally identify individual pings. Database uniqueness and transactional writes enforce behavior across processes; an in-memory cache is insufficient.

Initial limits: JSON body256KiB; ping batch100; cursor pages default20/max100; active rides at mostone per user/tenant; start/end requests30/minute/user and ping uploads60/minute/user. These are deployment/evaluator defaults requiring measured tuning. Rate limiting must be shared in Redis before multiple instances; no scaling claim from the current single-worker ingestion cache.

## Existing operator endpoints

| Method/path | Auth | Current behavior |
| --- | --- | --- |
| GET /health | None | Process alive, mode, verification_enabled=false |
| GET /ready | None | Actual PostGIS/Redis/source/credential readiness;503 on failure |
| GET /v1/arrivals/{stop}?service_no= | Server operator token | Separate arrival slots, source hash/time, quality/freshness and historical indicators |
| GET /v1/arrivals?bus_stop_codes=... | Server operator token | At most10 stops, individual unavailable results |

The operator credential and LTA key stay server-side. Flutter never uses either. Mobile arrival routes below delegate internally through authenticated server code.

## Commuter contract

All paths below start `/v1/tenants/{tenant_id}`. Ownership is implicit in the verified identity and transaction-local DB context.

| Method/path | Request / response | Required behavior |
| --- | --- | --- |
| GET /me | ID, display name, tenant membership and permitted UI actions | Provisioned membership only; no automatic administrator signup |
| GET /stops?latitude=&longitude=&radius_metres=&catalog_version= | Versioned stops with distance, description and geometry/source quality | Finite/range-valid coordinates; radius1–2000m; active reviewed catalog only; do not log query coordinates |
| GET /services?stop_code=&catalog_version= | Service/operator/direction and ordered stop occurrences | Repeated stops remain distinct by sequence; preserve suffix service IDs |
| GET /arrivals/{stop}?service_no= | Existing arrival representation | Recent context and schedule/unavailable flags; no vehicle/passenger claim |
| POST /rides | Client ride UUID, bus/rail mode, immutable catalog version, service/operator/direction, boarding occurrence, device started_at and consent version | Server derives owner; validates references and active-ride limit;201 with ride ID, server_received_at and upload window |
| POST /rides/{ride}/pings | Array of event UUID, monotonic device sequence, timezone captured_at, latitude/longitude, accuracy_metres; optional measured speed with units | Validate each entry; exact event retry acknowledges existing event; conflicting payload409; return accepted IDs/high-water mark |
| POST /rides/{ride}/end | Downstream alighting occurrence, device ended_at, final sequence, reason | Active→ended_pending; persist watermark and enqueue verification once;202 with pending status |
| POST /rides/{ride}/cancel | Reason | Active→cancelled, stop collection; no reward; exact retries stable |
| GET /rides/{ride} | Lifecycle state, upload status, verification result and ledger references | Owner only; pending is not verified |
| GET /rides?cursor= | Owner history | Stable signed cursor/order, no cross-user lookup parameters |
| GET /wallet and /wallet/entries?cursor= | Signed ledger balance and auditable history | PostgreSQL ledger is authoritative; zero/capped/reversed outcomes visible |
| GET /rankings?view=&period=&cursor= | Display-name verified rankings | Configured global/weekly/friends/company/school scopes; membership/privacy, ties and period rules explicit; exclude reversed/disallowed-mode outcomes |
| GET /promotions | Published/in-window promotions | Tenant/sponsor scope and visibility filters |
| GET /contests and /contests/{id} | Rules, dates, allowed modes, required tier and eligibility explanation | Tier/reward score are separate; unsupported stronger proof remains ineligible |
| POST /contests/{id}/registrations | Consent/rules version | Idempotent, transaction-safe eligibility/capacity check; no client-scored entry |
| GET /journeys?origin=&destination=&fare_profile= | Agreed bus/MRT/mixed candidates, estimated fares/time/CO2 and source versions | Explicit coverage/estimate labels; no unsupported real-time predictions |
| PATCH /profile/privacy | Display-name/ranking visibility/preferences | Explicit writable fields; no role/identity escalation |
| POST /privacy/deletion-requests | Request ID and consent | Audited controlled deletion workflow, retention/review exceptions explained |

These scopes cover the original product map; fare, CO2, promotions, rankings and rail features still require their own implementation/acceptance.

## Ride and upload rules

The durable lifecycle is active→ended_pending→verified/probable/low_confidence/rejected, or active→cancelled. Keep transport completion separate from verification class. The present schema's active/ended/cancelled status plus immutable verification record represents the boundary; sequence/watermark/upload-queue fields need a subsequent lifecycle migration.

Phone timestamps include a timezone and remain original. Store actual server receipt time independently. Reject nonfinite/out-of-range coordinates, impossible accuracy, duplicate sequence conflicts and device times inconsistent with the journey. Preserve low-quality observations with quality flags rather than granting strong proximity proof. Never rewrite a phone timestamp to make a trip valid.

Initial delayed-upload window is10minutes after end; permitted phone/server skew is2minutes. Earlier offline start requests need the original device start and explicit offline/untrusted-clock flags; elapsed phone time alone cannot confer stronger trust. A started ride must precede capture by the consenting app, even if the server receives it later. Pending batches may finish within the upload window; verification waits for the declared final sequence or the deadline. Missing sequence/gaps produce explicit unavailable evidence, never silently filled observations. These timing settings require device testing.

An exact end retry cannot award twice. Cancellation/end races lock the ride and permit one legal transition; conflicting transitions409. Late/conflicting data cannot mutate an immutable decision; authorized re-review produces a new audited case/correction, not a rewritten ledger award. Do not expose settlement functions as HTTP commuter endpoints.

## Admin contract and minimum action permissions

Admin paths begin `/v1/tenants/{tenant_id}/admin`. A role stored in a JWT never grants these permissions. Map server-owned roles to explicit actions, with additional sponsor ownership where relevant.

| Capability / proposed routes | Allowed role/action boundary |
| --- | --- |
| GET /users, /rides, /rides/{id}/verification | Support may see minimum metadata; raw trace access requires scoped fraud-review action and access audit |
| Promotion POST/PATCH, POST /promotions/{id}/publish | Campaign manager; sponsor admin only its assigned sponsor; draft/publish/expiry audited |
| Contest POST/PATCH, /close, /results | Campaign manager with configured trust/rules; winner/high-value review separately authorized |
| GET /fraud-cases, POST /fraud-cases/{id}/decisions | Fraud reviewer with tenant/case scope; reason, immutable actor identity and evidence references required |
| POST /fraud-cases/{id}/point-corrections | Validated fraud-review decision; worker performs exact reversal/approved ledger correction; no arbitrary client points |
| GET /analytics | Analyst aggregate outputs without raw GPS/identity disclosure |
| Membership/admin-role provisioning | Explicit super-admin action, audited; no self-promotion or unrestricted tenant traversal |

Admin searches paginate and audit access. State-changing case/campaign operations use optimistic version checks plus idempotency; conflicting edits409. Record verified human actor, tenant, target, action, reason, before/after hashes and server time. A worker database login alone is insufficient human audit.

## Implementation gates

Before enabling commuter mutations: real provider handshake, restricted DB login guard, HTTP cross-owner/tenant tests, transactional idempotency/races, immutable event ordering and active-only device collection. Before publishing results/rewards: server evaluators, reviewed catalog provenance, current context and genuine ride validation. Before admin routes: explicit action permissions, human audit and correction tests. CI/generated tests and genuine API/device acceptance remain separate receipts.
