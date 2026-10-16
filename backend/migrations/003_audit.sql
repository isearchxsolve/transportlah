CREATE TABLE tl.audit_events (
 id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, tenant_id uuid NOT NULL, actor_id uuid NOT NULL,
 action text NOT NULL CHECK(length(action) BETWEEN 1 AND 80), outcome text NOT NULL CHECK(outcome IN ('allowed','denied')),
 target_kind text NOT NULL CHECK(target_kind IN ('identity','wallet','ride','audit')),
 target_id text NOT NULL CHECK(length(target_id) BETWEEN 1 AND 100), request_id uuid NOT NULL,
 reason text NOT NULL CHECK(length(reason) BETWEEN 1 AND 200), created_at timestamptz NOT NULL DEFAULT now(),
 database_login text NOT NULL DEFAULT session_user,
 FOREIGN KEY(tenant_id,actor_id) REFERENCES tl.memberships
);
CREATE INDEX audit_tenant_id ON tl.audit_events(tenant_id,id);
CREATE TRIGGER immutable_audit BEFORE UPDATE OR DELETE ON tl.audit_events
FOR EACH ROW EXECUTE FUNCTION tl.immutable_row();
ALTER TABLE tl.audit_events ENABLE ROW LEVEL SECURITY;
CREATE FUNCTION tl.has_review_permission(t uuid,u uuid) RETURNS boolean LANGUAGE sql STABLE SECURITY DEFINER
SET search_path=pg_catalog,tl AS $$
 SELECT EXISTS(SELECT 1 FROM tl.memberships WHERE tenant_id=t AND user_id=u
               AND roles && ARRAY['fraud_reviewer','super_admin']::text[])
$$;
REVOKE ALL ON FUNCTION tl.has_review_permission(uuid,uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tl.has_review_permission(uuid,uuid) TO transportlah_app;
CREATE POLICY tenant_reviewer_audit ON tl.audit_events TO transportlah_app USING (
 tenant_id=NULLIF(current_setting('tl.tenant_id',true),'')::uuid AND
 tl.has_review_permission(tenant_id,NULLIF(current_setting('tl.user_id',true),'')::uuid)
);
GRANT SELECT ON tl.audit_events TO transportlah_app;
CREATE FUNCTION tl.record_audit(p_action text,p_outcome text,p_kind text,p_target text,p_request uuid,p_reason text)
RETURNS bigint LANGUAGE plpgsql SECURITY DEFINER SET search_path=pg_catalog,tl AS $$
DECLARE t uuid; u uuid; event_id bigint;
BEGIN
 t:=NULLIF(current_setting('tl.tenant_id',true),'')::uuid;
 u:=NULLIF(current_setting('tl.user_id',true),'')::uuid;
 IF t IS NULL OR u IS NULL OR NOT tl.has_membership(t,u) THEN RAISE EXCEPTION 'valid identity context required'; END IF;
 INSERT INTO tl.audit_events(tenant_id,actor_id,action,outcome,target_kind,target_id,request_id,reason)
 VALUES(t,u,p_action,p_outcome,p_kind,p_target,p_request,p_reason) RETURNING id INTO event_id;
 RETURN event_id;
END $$;
REVOKE ALL ON FUNCTION tl.record_audit(text,text,text,text,uuid,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION tl.record_audit(text,text,text,text,uuid,text) TO transportlah_app;
