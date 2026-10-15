# Spatial storage and query contract

Engineering resolution of H02, 2026-10-15. Migration: `backend/migrations/001_foundation.sql`. Query/reference code: `backend/app/spatial.py`. Real-engine checks: `backend/tests/test_database.py`.

## Units, provenance and time

Store stop/ping/arrival locations as `geography(Point,4326)` and route paths as `geography(LineString,4326)`. Construct points in longitude, latitude order; distance/radius arguments are metres. Match native geography columns directly with `ST_DWithin`; the GiST indexes use exactly those columns. Production geography distance defaults to the WGS84 spheroid. Never apply a metre radius to degree-based geometry, and never cast only the query side to a mismatched unindexed expression.

Routes carry service, direction, source version and geometry quality. `authoritative` means a route path obtained from an authoritative geometry source. `stop_sequence_chord` means lines joining official stops; they are not a surveyed road path. `TEST_VECTOR` is generated geometry. Full corridor queries filter for authoritative quality. Tests that temporarily use the authoritative flag to test that filter label the entire source version TEST_VECTOR; they do not constitute an imported authoritative catalog. Catalog ingestion must validate both source version and quality before an evaluator grants credit.

Route-stop occurrences use (route, sequence), so revisits to the same stop remain distinct. Fractional projection, if added, is only a supporting diagnostic; loops/repeated stops need sequence and ordered evidence. PostgreSQL UUID route IDs and source versions prevent a ride silently switching catalog versions.

Arrival rows preserve independent slot, captured timestamp, ETA, monitored flag, raw-payload hash and historical marker. Position observation time stays null when absent from the source contract. The position query requires that explicit timestamp and a ±30 s window; ETA/capture time never substitute for it. Historical/schedule-only observations cannot acquire a valid live position timestamp through this schema.

## Differential and index checks

The Python Haversine function is a spherical reference. Its comparisons use `ST_DistanceSphere`, with the engine's radius derived from a one-degree equatorial arc, avoiding a hidden Earth-radius mismatch. The generated battery contains 2,000 deterministic pairs including coincident, near-coincident, antimeridian and polar cases; maximum permitted absolute mismatch is 1 mm. Singapore-like random points remain TEST_VECTOR data.

Production uses spheroidal geography. Sphere/spheroid distances are not expected to be identical. Boundary tests create points at 149 m and 151 m using the engine's `ST_Project` and check a 150 m geography radius. Route examples check the 100/150 m difference and geometry-quality exclusion. Missing position-observation time is tested independently.

An explicitly disposable CI database loads 10,000 generated stop locations, runs ANALYZE, and records EXPLAIN ANALYZE with the default planner. The test requires the native `stop_location_gist` index; it does not disable sequential scans to force the result. The receipt is an executed index-capability check on the stated generated dataset. It is not a production throughput benchmark or a claim of sub-5 ms query latency.

## Migration and evidence boundaries

`tools/migrate.py` uses an explicit privileged MIGRATION_DATABASE_URL, transaction lock and per-file SHA-256 ledger. Exact reruns skip already applied migrations; a changed applied file aborts. PostGIS/pgcrypto installation requires administrator privileges. Application connections use separate non-owner roles; the migration URL is never a mobile/backend commuter credential. There is no automatic destructive rollback.

Generated differential/index checks were permitted after the user withdrew prior AGENTS.md instructions. Genuine route geometry import, real recorded-point differential comparisons, ambiguous-route progression, representative load measurements and physical-device outcomes remain V05/V10–V13. The preserved zero-coordinate historical capture cannot establish spatial verification accuracy.

Primary technical references: [ST_DWithin](https://postgis.net/docs/ST_DWithin.html), [ST_DistanceSphere](https://postgis.net/docs/ST_DistanceSphere.html), [ST_LineLocatePoint](https://postgis.net/docs/ST_LineLocatePoint.html).
