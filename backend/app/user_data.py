"""Owner-scoped HTTP read operations and human-identity audit recording."""
from .ownership import owned_transaction
from .permissions import permits,allowed_actions


class ActionDenied(Exception): pass
class ResourceMissing(Exception): pass


def read_user_data(url,principal,tenant_id,action,request_id,*,resource=None,before=None,limit=20):
    denied=False; result=None
    with owned_transaction(url,principal,tenant_id) as (conn,identity):
        user_id,roles=identity
        permitted=permits(roles,action)
        kind='wallet' if action.startswith('wallet.') else 'ride' if action=='ride.read' else 'audit' if action=='audit.read' else 'identity'
        conn.execute('SELECT tl.record_audit(%s,%s,%s,%s,%s,%s)',
                     (action,'allowed' if permitted else 'denied',kind,str(resource or user_id),request_id,
                      'authorized_read' if permitted else 'role_action_denied'))
        if not permitted:
            denied=True
        elif action=='profile.read':
            result={'user_id':str(user_id),'tenant_id':str(tenant_id),'roles':roles,'allowed_actions':sorted(allowed_actions(roles))}
        elif action=='ride.read':
            row=conn.execute('SELECT id,mode,status,started_at,ended_at FROM tl.rides WHERE id=%s',(resource,)).fetchone()
            if row:
                result=dict(zip(('id','mode','status','started_at','ended_at'),row))
            # Inaccessible IDs and absent IDs both produce404 after the access audit commits.
        elif action=='wallet.read':
            balance=conn.execute('SELECT coalesce(sum(points),0) FROM tl.ledger').fetchone()[0]
            rows=conn.execute('SELECT id,ride_id,kind,points,original_id,reason,created_at FROM tl.ledger WHERE (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s',
                              (before,before,limit+1)).fetchall()
            items=[dict(zip(('id','ride_id','kind','points','original_id','reason','created_at'),r)) for r in rows[:limit]]
            result={'balance':balance,'entries':items,'next_before':items[-1]['id'] if len(rows)>limit else None}
        elif action=='audit.read':
            rows=conn.execute('SELECT id,actor_id,action,outcome,target_kind,target_id,request_id,reason,created_at FROM tl.audit_events WHERE (%s::bigint IS NULL OR id<%s) ORDER BY id DESC LIMIT %s',
                              (before,before,limit+1)).fetchall()
            items=[dict(zip(('id','actor_id','action','outcome','target_kind','target_id','request_id','reason','created_at'),r)) for r in rows[:limit]]
            result={'entries':items,'next_before':items[-1]['id'] if len(rows)>limit else None}
        else:
            denied=True
    if denied: raise ActionDenied()
    if result is None: raise ResourceMissing()
    return result
