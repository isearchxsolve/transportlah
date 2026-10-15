-- Requires PostGIS and a migration administrator. No commuter credentials here.
CREATE SCHEMA tl;
CREATE ROLE transportlah_app NOLOGIN NOSUPERUSER NOBYPASSRLS;
CREATE ROLE transportlah_worker NOLOGIN NOSUPERUSER NOBYPASSRLS;
REVOKE ALL ON SCHEMA tl FROM PUBLIC;
GRANT USAGE ON SCHEMA tl TO transportlah_app, transportlah_worker;

CREATE TABLE tl.tenants (id uuid PRIMARY KEY, kind text NOT NULL CHECK(kind IN ('production','test')));
CREATE TABLE tl.identities (id uuid PRIMARY KEY, issuer text NOT NULL, subject text NOT NULL, UNIQUE(issuer,subject));
CREATE TABLE tl.memberships (
 tenant_id uuid REFERENCES tl.tenants, user_id uuid REFERENCES tl.identities,
 roles text[] NOT NULL DEFAULT ARRAY['commuter']::text[], PRIMARY KEY(tenant_id,user_id),
 CHECK(roles <@ ARRAY['commuter','super_admin','campaign_manager','sponsor_admin','support_agent','fraud_reviewer','analyst']::text[])
);
CREATE TABLE tl.route_patterns (
 id uuid PRIMARY KEY, mode text NOT NULL CHECK(mode IN ('bus','rail')), service text NOT NULL,
 direction text NOT NULL, source_version text NOT NULL,
 geometry_quality text NOT NULL CHECK(geometry_quality IN ('authoritative','stop_sequence_chord','TEST_VECTOR')),
 path geography(LineString,4326) NOT NULL
);
CREATE INDEX route_path_gist ON tl.route_patterns USING gist(path);
CREATE TABLE tl.stops (
 code text PRIMARY KEY, mode text NOT NULL CHECK(mode IN ('bus','rail')),
 source_version text NOT NULL, provenance text NOT NULL CHECK(provenance IN ('AUTHORITATIVE','TEST_VECTOR')),
 location geography(Point,4326) NOT NULL
);
CREATE INDEX stop_location_gist ON tl.stops USING gist(location);
CREATE TABLE tl.route_stop_occurrences (
 route_id uuid REFERENCES tl.route_patterns, sequence integer CHECK(sequence>=0), stop_code text REFERENCES tl.stops,
 PRIMARY KEY(route_id,sequence)
);
CREATE TABLE tl.arrival_observations (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, stop_code text NOT NULL, service text NOT NULL,
 slot text NOT NULL CHECK(slot IN ('NextBus','NextBus2','NextBus3')), captured_at timestamptz NOT NULL,
 estimated_arrival timestamptz, position_observed_at timestamptz, position geography(Point,4326),
 monitored boolean NOT NULL, raw_sha256 text NOT NULL CHECK(raw_sha256 ~ '^[a-f0-9]{64}$'), historical boolean NOT NULL,
 CHECK(position_observed_at IS NULL OR (position IS NOT NULL AND monitored AND NOT historical))
);
CREATE INDEX arrival_position_gist ON tl.arrival_observations USING gist(position);
CREATE INDEX arrival_observed_at ON tl.arrival_observations(position_observed_at);
CREATE TABLE tl.rides (
 id uuid PRIMARY KEY, tenant_id uuid NOT NULL, user_id uuid NOT NULL,
 mode text NOT NULL CHECK(mode IN ('bus','rail')), status text NOT NULL CHECK(status IN ('active','ended','cancelled')),
 route_id uuid REFERENCES tl.route_patterns, started_at timestamptz NOT NULL, ended_at timestamptz,
 FOREIGN KEY(tenant_id,user_id) REFERENCES tl.memberships,
 UNIQUE(id,tenant_id,user_id), CHECK((status='ended')=(ended_at IS NOT NULL)), CHECK(ended_at>=started_at)
);
CREATE TABLE tl.pings (
 ride_id uuid NOT NULL, tenant_id uuid NOT NULL, user_id uuid NOT NULL, event_id uuid NOT NULL,
 captured_at timestamptz NOT NULL, accuracy_metres double precision NOT NULL CHECK(accuracy_metres>0 AND accuracy_metres<10000),
 position geography(Point,4326) NOT NULL, payload_sha256 text NOT NULL CHECK(payload_sha256 ~ '^[a-f0-9]{64}$'),
 PRIMARY KEY(ride_id,event_id), FOREIGN KEY(ride_id,tenant_id,user_id) REFERENCES tl.rides(id,tenant_id,user_id)
);
CREATE INDEX ping_position_gist ON tl.pings USING gist(position);
CREATE INDEX ping_ride_time ON tl.pings(ride_id,captured_at);
CREATE TABLE tl.verifications (
 ride_id uuid PRIMARY KEY REFERENCES tl.rides, tenant_id uuid NOT NULL, user_id uuid NOT NULL,
 decision jsonb NOT NULL, digest text NOT NULL CHECK(digest ~ '^[a-f0-9]{64}$'), created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY(ride_id,tenant_id,user_id) REFERENCES tl.rides(id,tenant_id,user_id)
);
CREATE TABLE tl.ledger (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, tenant_id uuid NOT NULL, user_id uuid NOT NULL,
 ride_id uuid NOT NULL REFERENCES tl.verifications, kind text NOT NULL CHECK(kind IN ('award','reversal')),
 points integer NOT NULL, original_id bigint UNIQUE REFERENCES tl.ledger, reason text NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(), actor_database_role text NOT NULL DEFAULT session_user,
 FOREIGN KEY(ride_id,tenant_id,user_id) REFERENCES tl.rides(id,tenant_id,user_id),
 CHECK((kind='award' AND points>=0 AND original_id IS NULL) OR (kind='reversal' AND points<=0 AND original_id IS NOT NULL))
);
CREATE UNIQUE INDEX one_award_per_ride ON tl.ledger(ride_id) WHERE kind='award';
CREATE INDEX ledger_wallet ON tl.ledger(tenant_id,user_id,created_at);

-- Fail closed when transaction-local context is absent; memberships are server-owned.
CREATE FUNCTION tl.has_membership(t uuid, u uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path=pg_catalog,tl AS $$
 SELECT EXISTS(SELECT 1 FROM tl.memberships WHERE tenant_id=t AND user_id=u)
$$;
REVOKE ALL ON FUNCTION tl.has_membership(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tl.has_membership(uuid,uuid) TO transportlah_app;
DO $$ DECLARE tab text; BEGIN
 FOREACH tab IN ARRAY ARRAY['rides','pings','verifications','ledger'] LOOP
  EXECUTE format('ALTER TABLE tl.%I ENABLE ROW LEVEL SECURITY',tab);
  EXECUTE format($p$CREATE POLICY owner_scope ON tl.%I TO transportlah_app USING (
   tenant_id=NULLIF(current_setting('tl.tenant_id',true),'')::uuid AND
   user_id=NULLIF(current_setting('tl.user_id',true),'')::uuid AND tl.has_membership(tenant_id,user_id))$p$,tab);
 END LOOP;
END $$;
GRANT SELECT ON tl.rides,tl.pings,tl.verifications,tl.ledger TO transportlah_app;
-- No direct write permissions for app/worker. Narrow functions are the worker boundary.
CREATE FUNCTION tl.immutable_row() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'append-only evidence/ledger'; END $$;
CREATE TRIGGER immutable_ledger BEFORE UPDATE OR DELETE ON tl.ledger FOR EACH ROW EXECUTE FUNCTION tl.immutable_row();
CREATE TRIGGER immutable_verification BEFORE UPDATE OR DELETE ON tl.verifications FOR EACH ROW EXECUTE FUNCTION tl.immutable_row();
CREATE TRIGGER immutable_ping BEFORE UPDATE OR DELETE ON tl.pings FOR EACH ROW EXECUTE FUNCTION tl.immutable_row();

CREATE FUNCTION tl.settle(p_ride uuid, p_decision jsonb) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,tl,public AS $$
DECLARE r tl.rides%ROWTYPE; existing tl.verifications%ROWTYPE; award_id bigint; pct integer;
 pts integer; used integer; d text; tier integer; confidence numeric; state text; test_only boolean;
BEGIN
 SELECT * INTO STRICT r FROM tl.rides WHERE id=p_ride FOR UPDATE;
 IF r.status<>'ended' THEN RAISE EXCEPTION 'ride must be ended'; END IF;
 d:=encode(public.digest(p_decision::text,'sha256'),'hex');
 SELECT * INTO existing FROM tl.verifications WHERE ride_id=p_ride;
 IF FOUND THEN
  IF existing.digest<>d THEN RAISE EXCEPTION 'conflicting verification retry'; END IF;
  SELECT id INTO award_id FROM tl.ledger WHERE ride_id=p_ride AND kind='award'; RETURN award_id;
 END IF;
 IF p_decision->>'policy_version' IS DISTINCT FROM 'tl-bus-policy-1' OR p_decision->>'mode' IS DISTINCT FROM r.mode
    OR NOT p_decision ?& ARRAY['score','tier','status','reward_percent','test_only','leaderboard_eligible']
 THEN RAISE EXCEPTION 'unsupported decision contract'; END IF;
 IF EXISTS(SELECT 1 FROM unnest(ARRAY['score','tier','status','reward_percent','test_only','leaderboard_eligible']) k
            WHERE p_decision->k IS NULL OR p_decision->k='null'::jsonb)
 THEN RAISE EXCEPTION 'decision values cannot be null'; END IF;
 test_only:=(p_decision->>'test_only')::boolean;
 IF test_only AND (SELECT kind FROM tl.tenants WHERE id=r.tenant_id)<>'test'
 THEN RAISE EXCEPTION 'test evidence forbidden in production'; END IF;
 tier:=(p_decision->>'tier')::integer; confidence:=(p_decision->>'score')::numeric;
 state:=p_decision->>'status'; pct:=(p_decision->>'reward_percent')::integer;
 IF tier NOT BETWEEN 0 AND 3 OR confidence NOT BETWEEN 0 AND 100 OR confidence::text='NaN'
 THEN RAISE EXCEPTION 'invalid tier/score'; END IF;
 IF (state='verified' AND confidence>=80 AND tier>=2 AND pct=100) OR
    (state='probable' AND confidence>=60 AND confidence<80 AND pct=CASE WHEN tier>=1 THEN 50 ELSE 0 END) OR
    (state='low_confidence' AND confidence>=40 AND confidence<60 AND pct=0) OR
    (state='rejected' AND confidence<40 AND pct=0) THEN NULL;
 ELSE RAISE EXCEPTION 'inconsistent decision'; END IF;
 IF (p_decision->>'leaderboard_eligible')::boolean IS DISTINCT FROM (state='verified' AND tier>=2)
 THEN RAISE EXCEPTION 'inconsistent ranking eligibility'; END IF;
 -- Serialize different rides for the same wallet before calculating the daily gross cap.
 PERFORM pg_advisory_xact_lock(hashtextextended(r.tenant_id::text||':'||r.user_id::text,0));
 SELECT coalesce(sum(points),0) INTO used FROM tl.ledger
 WHERE tenant_id=r.tenant_id AND user_id=r.user_id AND kind='award'
 AND (created_at AT TIME ZONE 'Asia/Singapore')::date=(now() AT TIME ZONE 'Asia/Singapore')::date;
 -- Rail rewards are gated off until its separate adapter is implemented and validated.
 pts:=CASE WHEN r.mode='bus' THEN least(10*pct/100,greatest(0,100-used)) ELSE 0 END;
 INSERT INTO tl.verifications(ride_id,tenant_id,user_id,decision,digest) VALUES(p_ride,r.tenant_id,r.user_id,p_decision,d);
 INSERT INTO tl.ledger(tenant_id,user_id,ride_id,kind,points,reason)
 VALUES(r.tenant_id,r.user_id,p_ride,'award',pts,'policy settlement') RETURNING id INTO award_id;
 RETURN award_id;
END $$;
CREATE FUNCTION tl.reverse_award(p_original bigint, p_reason text) RETURNS bigint
LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,tl AS $$
DECLARE a tl.ledger%ROWTYPE; reversal_id bigint; previous_reason text;
BEGIN
 IF p_reason IS NULL OR length(trim(p_reason)) NOT BETWEEN 1 AND 500 THEN RAISE EXCEPTION 'reason required'; END IF;
 SELECT * INTO STRICT a FROM tl.ledger WHERE id=p_original FOR UPDATE;
 IF a.kind<>'award' THEN RAISE EXCEPTION 'only awards can be reversed'; END IF;
 SELECT id,reason INTO reversal_id,previous_reason FROM tl.ledger WHERE original_id=p_original;
 IF FOUND THEN
  IF previous_reason<>p_reason THEN RAISE EXCEPTION 'conflicting reversal retry'; END IF;
  RETURN reversal_id;
 END IF;
 INSERT INTO tl.ledger(tenant_id,user_id,ride_id,kind,points,original_id,reason)
 VALUES(a.tenant_id,a.user_id,a.ride_id,'reversal',-a.points,a.id,p_reason) RETURNING id INTO reversal_id;
 RETURN reversal_id;
END $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA tl FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tl.has_membership(uuid,uuid) TO transportlah_app;
GRANT EXECUTE ON FUNCTION tl.settle(uuid,jsonb),tl.reverse_award(bigint,text) TO transportlah_worker;
CREATE FUNCTION tl.resolve_identity(p_issuer text,p_subject text,p_tenant uuid)
RETURNS TABLE(user_id uuid,roles text[]) LANGUAGE sql STABLE SECURITY DEFINER SET search_path=pg_catalog,tl AS $$
 SELECT i.id,m.roles FROM tl.identities i JOIN tl.memberships m ON m.user_id=i.id
 WHERE i.issuer=p_issuer AND i.subject=p_subject AND m.tenant_id=p_tenant
$$;
REVOKE ALL ON FUNCTION tl.resolve_identity(text,text,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tl.resolve_identity(text,text,uuid) TO transportlah_app;
