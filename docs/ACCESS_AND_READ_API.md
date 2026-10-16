# Infrastructure and authenticated-read operations

Updated2026-10-16. Development/CI access configuration and tested backend implementation; no client cloud deployment/provider handshake implied.

## Database and Redis

Compose binds PostgreSQL5433, Redis6380 and backend8000 to127.0.0.1. Both data services require independently generated private passwords. No credentials are committed; .env is ignored. Start the stack on a Docker-capable host, then apply versioned migrations using tool-only MIGRATION_DATABASE_URL. PostGIS and pgcrypto installation needs administrator privileges.

The operator ingestion DATABASE_URL may perform readiness queries. Commuter APP_DATABASE_URL must be a separate non-owner/non-superuser/NOBYPASSRLS login inheriting transportlah_app and no worker group. WORKER_DATABASE_URL inherits only transportlah_worker. Migration credentials never go to mobile apps or commuter handlers. Use private networking/TLS/secrets management on the provisioned production host; local loopback configuration is not a production deployment receipt.

CI uses actual loopback-bound PostGIS/Redis containers. The disposable Redis is assigned its generated CI password before application checks. tools/check_access_controls.py demonstrates successful authenticated access, an explicit PostgreSQL password-authentication failure, and rejected missing/wrong Redis credentials. Client keys and production secrets are not used.

## Optional authenticated reads

Set COMMUTER_API_ENABLED=true and configure APP_DATABASE_URL, OIDC_ISSUER, OIDC_AUDIENCE, OIDC_JWKS_URL. The JWKS endpoint/issuer must be HTTPS, with RS256/ES256 keys and explicit audience. Trusted administration provisions unique issuer/subject identities and tenant memberships; there is no self-admin registration. Real provider setup remains a client/deployment dependency.

Paths under /v1/tenants/{tenant_id}:

- GET /me: trusted identity, roles and permitted actions.
- GET /rides/{ride_id}: existing owner's lifecycle record; cross-owner/tenant/unknown IDs404.
- GET /wallet and /wallet/entries: ledger balance plus descending immutable entries. `limit`1–100; optional positive `before` bigint; next_before continues pagination. No POST award API exists.
- GET /admin/audit-events: tenant-scoped events, restricted to fraud reviewer or super-admin actions. Campaign managers do not gain fraud privileges from token claims.

Roles come from the database, never unverified JWT role/tenant/email claims. Missing/invalid JWT401; missing resource/membership404; denied role403; unsafe/unavailable DB503. Requests use generated/validated UUID request IDs and bounded/redacted validation/log responses. No trace location or token is logged.

Profile/ride/wallet/audit access records include verified human identity, tenant, action/outcome, target, request UUID, fixed server reason and actual server time. Denials persist after permission checking. Audit rows reject update/delete. Reviewer RLS prevents cross-tenant audit reads; ordinary commuters cannot read the audit table. Human fraud-case decisions/correction workflows require additional product endpoints and are still pending.

## Spatial evaluator boundaries

boarding_proximity computes spheroidal PostGIS stop distance against the versioned catalog and reported device accuracy. It passes when distance+accuracy is within radius; fails when distance-accuracy exceeds radius; overlap, poor accuracy, absent stops/catalogs yield unavailable. Default radius50m and accuracy limit50m are configurable initial assumptions, not calibrated accuracy guarantees.

service_sequence validates exact version/service/operator/direction, boarding/alighting sequence and stop codes, requiring a downstream occurrence. Loop returns to the same physical stop remain distinct occurrences. Unknown/test-only catalog yields unavailable by default; generated vectors require an explicit internal allow_test flag. These helpers do not prove boarding, progression or passenger presence and are not exposed as client-scored inputs.
