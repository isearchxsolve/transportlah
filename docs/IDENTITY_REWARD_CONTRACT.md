# Identity, ownership and durable reward contract

Engineering resolution of H03, updated2026-10-16. Identity, ownership, permissions, audit and wallet/ride read HTTP boundaries are implemented and tested. They are opt-in through COMMUTER_API_ENABLED plus provider/separate app-DB configuration; default configuration keeps them unavailable. Ride mutation, campaign/review product flows and evidence publication remain closed. Operator credentials never go into Flutter.

## Identity and authorization

Use a managed OpenID Connect provider. The verifier has an explicitly configured HTTPS issuer, API audience, fixed HTTPS JWKS endpoint and asymmetric RS256/ES256 allowlist. Require valid signature, issuer, audience, expiration, issuance time and nonempty subject. Ignore token role/tenant/email claims and token-provided key URLs. JWT subjects map to the unique (issuer, subject) identity; verified email alone never merges accounts.

JWKS requests have a five-second timeout, no redirects, 256 KiB/64-key limits, a five-minute cache and at most one refresh attempt every 30 s. Unknown keys fail closed during that interval. Rotation should overlap old/new public keys; operators must account for the maximum refresh delay. Weak RSA keys, duplicate signing keys and unsupported critical headers fail closed. Generated RSA signature tests prove local cryptographic/claim behavior; they are not an authenticated handshake with a client-owned provider.

Provision memberships from trusted administration, not client claims or automatic administrator signup. Resolve identity and membership through a narrow SQL function; set user/tenant context transaction-locally only after token verification. The non-owner runtime role must not be superuser, BYPASSRLS, a member of a table-owner role, or a member of the worker role. The runtime guard rejects these configurations.

RLS restricts rides, pings, verification and ledger reads to both tenant and owner, with an existing membership. Missing context yields no rows. Connection transaction completion clears context. Backend credentials stay server-side; a compromised database login could set its own context, so RLS complements the verified HTTP/backend boundary rather than replacing it.

The schema stores commuter, super-admin, campaign-manager, sponsor-admin, support-agent, fraud-reviewer and analyst roles. `permissions.py` maps explicit actions, defaulting to denied. HTTP /me exposes server-derived allowed actions; review/admin roles alone may read tenant-scoped audit events. Campaign/sponsor management still needs sponsor-bound product endpoints; support search, fraud decisions and analyst aggregates remain future product work. No role name enables an unimplemented endpoint.

## Database roles and function boundaries

`transportlah_app` and `transportlah_worker` are NOLOGIN group roles. Provision separate login credentials inheriting exactly the appropriate group. The migration administrator owns tables/functions. Ownership bypass of RLS is intentional inside narrowly granted SECURITY DEFINER functions with fixed search paths and qualified relations; PUBLIC function execute is revoked. App has owner-scoped SELECT and no direct writes/settlement privilege. Worker has only settlement/reversal execute, not arbitrary table writes. Worker credentials are an explicitly trusted verification-service boundary and are never accepted as mobile identity.

No commuter may submit a score, tier or reward amount. The worker must derive decisions from server evaluators using the reviewed policy and evidence provenance. SQL independently checks policy version, mode, score/class/tier/reward/ranking consistency, ended lifecycle and test-tenant provenance. It cannot cryptographically prove that the privileged worker truly evaluated the factors; securing that worker and retaining input evidence are required deployment responsibilities.

## Settlement, retries and corrections

Lock the ended ride before writing its one immutable verification snapshot. SHA-256 of PostgreSQL's canonical JSONB text identifies that decision. An exact retry returns the existing ledger ID; a changed retry raises a conflict. Insert decision and award in the same transaction; errors roll back both. A unique partial index permits one award per ride.

An advisory transaction lock serializes different rides for the same tenant/user before checking the gross daily award cap on the Singapore date. Current version: bus base 10, probable multiplier 50%, verified 100%, daily gross cap 100. Rail points remain zero and verified rail settlement is refused until a separately validated adapter/version enables it. These economics are provisional, not a new client offer.

Balances derive from signed append-only ledger sums. A reversal locks the original award and creates exactly its negative amount; one reversal per original. Exact retry returns the existing reversal; conflicting reason or reversing a reversal fails. Original award/decision/pings cannot be updated or deleted. Each ledger entry records the physical database login and reason. Human fraud-review actor/reason/case binding must be added to the future authorized review API before it is exposed; a database worker login alone is not a complete human audit trail.

Duplicate ping event IDs cannot insert new or conflicting observations. An upload endpoint must compare the existing payload digest for exact retry and reject mismatches; that endpoint is subsequent lifecycle work. Do not implement ON CONFLICT UPDATE on immutable pings. Retention needs an explicitly privileged, separately audited deletion path; ordinary update/delete triggers intentionally prevent ad hoc mutation.

Rankings must select verified Tier 2+ durable decisions, apply current allowed-mode policy and exclude reversed awards; Redis is rebuildable acceleration. Contest registration also checks per-contest modes/tier and test-only provenance. Ranking rebuild, contest registration and human review screens remain separate product tasks.

## Executable checks and remaining gates

Crypto tests exercise correct/wrong signatures, issuer/audience, expiry/future issuance, missing claims, unsigned tokens, attacker key URLs and unknown-key refresh storms. Real PostGIS tests use separate actual app/worker login roles; check cross-user/cross-tenant/no-context RLS, missing membership, privileged-role rejection, denied commuter credit, 12 concurrent retries, 15 concurrent rides against the cap, atomic rejection, immutable evidence and eight concurrent reversals. All generated tenants/identities/rides are explicitly test data in a disposable CI database.

HTTP ownership/role reads and immutable human-identity access auditing now pass real-login/database integration with generated signed JWTs. Client provider provisioning/handshake, account lifecycle, ride mutations, remaining factor evaluators, trusted boarding proof, campaign/review screens and genuine ride acceptance remain external or implementation gates.

Primary references: [PyJWT validation](https://pyjwt.readthedocs.io/en/stable/usage.html), [PostgreSQL row security](https://www.postgresql.org/docs/16/ddl-rowsecurity.html), [transaction isolation](https://www.postgresql.org/docs/16/transaction-iso.html).
