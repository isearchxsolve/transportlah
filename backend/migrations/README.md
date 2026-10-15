# Migration boundary

`001_foundation.sql` implements geography, provenance/occurrences, tenants/identity/memberships, rides/pings, immutable verification/ledger, owner RLS and worker-only settlement/reversal. H02/H03 are resolved; read the spatial and identity/reward contracts in docs.

Run `tools/migrate.py` with an explicit privileged MIGRATION_DATABASE_URL. It verifies applied-file SHA hashes and applies new migrations transactionally under an advisory lock. Never edit an already deployed migration; add the next version. The first migration expects a fresh database and unused transportlah_app/transportlah_worker group names; pre-existing roles need administrator review. No destructive automatic rollback exists. Do not mount the historical seed schema.
