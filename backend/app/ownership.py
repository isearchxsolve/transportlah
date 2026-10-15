"""Transaction-scoped identity. Call only after OIDCVerifier verifies a bearer."""
from contextlib import contextmanager
from uuid import UUID
import psycopg
from backend.app.identity import Principal


def assert_app_role(conn):
    row=conn.execute("""
    SELECT r.rolsuper,r.rolbypassrls,
      EXISTS(SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
             WHERE n.nspname='tl' AND pg_has_role(current_user,c.relowner,'MEMBER')),
      pg_has_role(current_user,'transportlah_worker','MEMBER')
    FROM pg_roles r WHERE r.rolname=current_user
    """).fetchone()
    if not row or any(row):
        raise PermissionError('Commuter database role must not own/bypass tables or inherit worker permissions')


@contextmanager
def owned_transaction(url,principal,tenant_id):
    if not isinstance(principal,Principal): raise TypeError('Verified Principal required')
    tenant=UUID(str(tenant_id))
    with psycopg.connect(url) as conn:
        assert_app_role(conn)
        identity=conn.execute('SELECT * FROM tl.resolve_identity(%s,%s,%s)',(principal.issuer,principal.subject,tenant)).fetchone()
        if not identity: raise PermissionError('No tenant membership')
        conn.execute("SELECT set_config('tl.tenant_id',%s,true),set_config('tl.user_id',%s,true)",(str(tenant),str(identity[0])))
        yield conn,identity
