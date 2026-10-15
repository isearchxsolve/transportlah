-- Immutable snapshots keep historical route/stop coordinates stable across refreshes.
CREATE TABLE tl.catalog_versions (
 id text PRIMARY KEY CHECK(id ~ '^[a-f0-9]{64}$'), provenance text NOT NULL CHECK(provenance IN ('LIVE_NETWORK','TEST_VECTOR')),
 started_at timestamptz NOT NULL, completed_at timestamptz NOT NULL, captured_document jsonb NOT NULL,
 CHECK(completed_at>=started_at)
);
CREATE TABLE tl.catalog_stops (
 version text REFERENCES tl.catalog_versions, code text CHECK(code ~ '^[0-9]{5}$'), road_name text NOT NULL,
 description text NOT NULL, location geography(Point,4326) NOT NULL, PRIMARY KEY(version,code)
);
CREATE INDEX catalog_stop_location_gist ON tl.catalog_stops USING gist(location);
CREATE TABLE tl.catalog_services (
 version text REFERENCES tl.catalog_versions, service text NOT NULL, operator text NOT NULL,
 direction integer CHECK(direction IN (1,2)), raw jsonb NOT NULL, PRIMARY KEY(version,service,operator,direction)
);
CREATE TABLE tl.catalog_route_stops (
 version text NOT NULL, service text NOT NULL, operator text NOT NULL, direction integer NOT NULL,
 sequence integer CHECK(sequence>0), stop_code text NOT NULL, distance_km numeric NOT NULL CHECK(distance_km>=0),
 route_id uuid REFERENCES tl.route_patterns, raw jsonb NOT NULL,
 PRIMARY KEY(version,service,operator,direction,sequence),
 FOREIGN KEY(version,stop_code) REFERENCES tl.catalog_stops,
 FOREIGN KEY(version,service,operator,direction) REFERENCES tl.catalog_services
);
DO $$ DECLARE tab text; BEGIN
 FOREACH tab IN ARRAY ARRAY['catalog_versions','catalog_stops','catalog_services','catalog_route_stops'] LOOP
  EXECUTE format('CREATE TRIGGER immutable_catalog BEFORE UPDATE OR DELETE ON tl.%I FOR EACH ROW EXECUTE FUNCTION tl.immutable_row()',tab);
 END LOOP;
END $$;
-- Catalog is public transit metadata; no raw commuter locations or product identity here.
GRANT SELECT ON tl.catalog_versions,tl.catalog_stops,tl.catalog_services,tl.catalog_route_stops TO transportlah_app;
CREATE TRIGGER immutable_route_geometry BEFORE UPDATE OR DELETE ON tl.route_patterns
FOR EACH ROW EXECUTE FUNCTION tl.immutable_row();
