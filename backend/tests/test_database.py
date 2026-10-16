"""Real PostGIS/authorization/concurrency checks in an explicitly disposable database.

All catalog/ride records here are generated TEST_VECTOR data. Never field evidence.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import math
import os
import random
import asyncio
import time
import unittest
from uuid import uuid4,uuid5,NAMESPACE_URL
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
from backend.app.identity import Principal
from backend.app.ownership import assert_app_role, owned_transaction
from backend.app.spatial import haversine_metres, CORRIDOR_SQL, POSITION_SQL
from backend.app.verification import Evidence, Factor, Observation, State, decide
from tools.migrate import migrate
from backend.app.catalog import import_catalog, normalize_catalog
from backend.tests.test_catalog import catalog_vector, rehash
from backend.app.evaluators import boarding_proximity,service_sequence
from backend.app.verification import State
from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.identity import OIDCVerifier
from cryptography.hazmat.primitives.asymmetric import rsa
import httpx
import jwt


DB_URL=os.getenv('TEST_DATABASE_URL')
if os.getenv('TL_REQUIRE_DATABASE')=='1' and not DB_URL:
    raise RuntimeError('Real database tests are required in this run')


@unittest.skipUnless(DB_URL,'Real PostGIS tests require TEST_DATABASE_URL; local skip is not acceptance')
class DatabaseChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.getenv('TL_TEST_DATABASE_CONFIRMED')!='1':
            raise RuntimeError('Explicit disposable database acknowledgement required')
        migrate(DB_URL)
        cls.logins=[]
        cls.signing_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        cls.jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(cls.signing_key.public_key()))
        cls.jwk.update(kid='TEST_VECTOR:signing-key',alg='RS256',use='sig')
        with psycopg.connect(DB_URL) as conn:
            versions=conn.execute('SELECT version(),PostGIS_Full_Version()').fetchone()
            print(json.dumps({'database_checks_origin':'TEST_VECTOR','postgres':versions[0],'postgis':versions[1]}))
            for role in ('transportlah_app','transportlah_worker'):
                login='tl_test_'+uuid4().hex; password=uuid4().hex+uuid4().hex
                conn.execute(sql.SQL('CREATE ROLE {} LOGIN PASSWORD {} NOSUPERUSER NOBYPASSRLS IN ROLE {}').format(sql.Identifier(login),sql.Literal(password),sql.Identifier(role)))
                cls.logins.append(login)
                setattr(cls,'app_url' if role.endswith('app') else 'worker_url',make_conninfo(DB_URL,user=login,password=password))

    @classmethod
    def tearDownClass(cls):
        with psycopg.connect(DB_URL) as conn:
            for login in cls.logins: conn.execute(sql.SQL('DROP ROLE {}').format(sql.Identifier(login)))

    def setUp(self):
        self.tenant,self.other_tenant,self.user,self.other_user=[uuid4() for _ in range(4)]
        with psycopg.connect(DB_URL) as conn:
            conn.execute('INSERT INTO tl.tenants VALUES (%s,%s),(%s,%s)',(self.tenant,'test',self.other_tenant,'test'))
            conn.execute('INSERT INTO tl.identities VALUES (%s,%s,%s),(%s,%s,%s)',
                         (self.user,'https://test.example',str(self.user),self.other_user,'https://test.example',str(self.other_user)))
            conn.execute('INSERT INTO tl.memberships(tenant_id,user_id) VALUES (%s,%s),(%s,%s),(%s,%s)',
                         (self.tenant,self.user,self.tenant,self.other_user,self.other_tenant,self.user))
        self.principal=Principal('https://test.example',str(self.user))
        self.decision=decide(Evidence({f:Observation(State.PASSED,Decimal(1)) for f in Factor},'TEST_VECTOR')).payload()

    def ride(self,*,tenant=None,user=None,status='ended'):
        identifier=uuid4(); now=datetime.now(timezone.utc)
        with psycopg.connect(DB_URL) as conn:
            conn.execute('INSERT INTO tl.rides(id,tenant_id,user_id,mode,status,started_at,ended_at) VALUES (%s,%s,%s,%s,%s,%s,%s)',
                         (identifier,tenant or self.tenant,user or self.user,'bus',status,now-timedelta(minutes=10),now if status=='ended' else None))
        return identifier

    def settle(self,ride,decision=None):
        with psycopg.connect(self.worker_url) as conn:
            return conn.execute('SELECT tl.settle(%s,%s)',(ride,Jsonb(decision or self.decision))).fetchone()[0]

    def test_migration_is_idempotent(self): migrate(DB_URL)

    def bearer(self,**changes):
        claims={'iss':'https://test.example','aud':'transportlah-test','sub':str(self.user),
                'iat':int(time.time())-1,'exp':int(time.time())+300,**changes}
        return {'Authorization':'Bearer '+jwt.encode(claims,self.signing_key,algorithm='RS256',headers={'kid':'TEST_VECTOR:signing-key'})}

    def http_checks(self,operation):
        async def run():
            verifier=OIDCVerifier(issuer='https://test.example',audience='transportlah-test',jwks_url='https://test.example/jwks',
                                  client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,json={'keys':[self.jwk]}))))
            settings=Settings(capture_dir=__import__('pathlib').Path(__file__).parent/'data',commuter_api_enabled=True,
                              app_database_url=self.app_url,oidc_issuer='https://test.example',oidc_audience='transportlah-test',
                              oidc_jwks_url='https://test.example/jwks')
            app=create_app(settings,identity_verifier=verifier)
            async with app.router.lifespan_context(app):
                async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),base_url='http://test') as client:
                    await operation(client)
        asyncio.run(run())

    def test_authenticated_http_owner_tenant_and_missing_identity_boundaries(self):
        own=self.ride(); other=self.ride(user=self.other_user); third=self.ride(tenant=self.other_tenant)
        async def check(client):
            base=f'/v1/tenants/{self.tenant}'
            self.assertEqual((await client.get(base+'/me')).status_code,401)
            self.assertEqual((await client.get(base+'/me',headers=self.bearer(iss='https://attacker.example'))).status_code,401)
            self.assertEqual((await client.get(base+'/me',headers=self.bearer(sub=str(uuid4())))).status_code,404)
            self.assertEqual((await client.get(base+'/me',headers=self.bearer())).json()['user_id'],str(self.user))
            self.assertEqual((await client.get(base+f'/rides/{own}',headers=self.bearer())).status_code,200)
            for inaccessible in (other,third,uuid4()):
                self.assertEqual((await client.get(base+f'/rides/{inaccessible}',headers=self.bearer())).status_code,404)
            self.assertEqual((await client.get(f'/v1/tenants/{uuid4()}/wallet',headers=self.bearer())).status_code,404)
        self.http_checks(check)

    def test_http_roles_come_from_database_and_denials_have_immutable_human_audit(self):
        async def check(client):
            base=f'/v1/tenants/{self.tenant}'
            headers=self.bearer(roles=['super_admin'],tenant=str(self.other_tenant))
            denied=await client.get(base+'/admin/audit-events',headers=headers)
            self.assertEqual(denied.status_code,403)
            request_id=denied.headers['x-request-id']
            with psycopg.connect(DB_URL) as conn:
                event=conn.execute('SELECT actor_id,outcome,request_id FROM tl.audit_events WHERE tenant_id=%s ORDER BY id DESC LIMIT 1',(self.tenant,)).fetchone()
                self.assertEqual(event[:2],(self.user,'denied')); self.assertEqual(str(event[2]),request_id)
                conn.execute("UPDATE tl.memberships SET roles=ARRAY['campaign_manager'] WHERE tenant_id=%s AND user_id=%s",(self.tenant,self.user))
            profile=(await client.get(base+'/me',headers=headers)).json()
            self.assertIn('campaign.manage',profile['allowed_actions']); self.assertNotIn('fraud.review',profile['allowed_actions'])
            self.assertEqual((await client.get(base+'/admin/audit-events',headers=headers)).status_code,403)
            with psycopg.connect(DB_URL) as conn:
                conn.execute("UPDATE tl.memberships SET roles=ARRAY['fraud_reviewer'] WHERE tenant_id=%s AND user_id=%s",(self.tenant,self.user))
            result=await client.get(base+'/admin/audit-events',headers=headers)
            self.assertEqual(result.status_code,200)
            self.assertTrue(all(entry['actor_id']==str(self.user) for entry in result.json()['entries']))
            with psycopg.connect(DB_URL) as conn:
                conn.execute("UPDATE tl.memberships SET roles=ARRAY['super_admin'] WHERE tenant_id=%s AND user_id=%s",(self.tenant,self.user))
            self.assertIn('memberships.manage',(await client.get(base+'/me',headers=headers)).json()['allowed_actions'])
        self.http_checks(check)
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute('DELETE FROM tl.audit_events WHERE tenant_id=%s',(self.tenant,))

    def test_wallet_http_balance_pagination_duplicate_retry_and_reversal_reconcile(self):
        a=self.ride(); b=self.ride(); other=self.ride(user=self.other_user)
        first=self.settle(a); self.assertEqual(self.settle(a),first); self.settle(b); self.settle(other)
        with psycopg.connect(self.worker_url) as conn: conn.execute('SELECT tl.reverse_award(%s,%s)',(first,'TEST_VECTOR:wallet-correction'))
        async def check(client):
            base=f'/v1/tenants/{self.tenant}/wallet'
            response=await client.get(base,params={'limit':1},headers=self.bearer())
            self.assertEqual(response.status_code,200); self.assertEqual(response.json()['balance'],10)
            entries=[]; page=response.json()
            while True:
                entries.extend(page['entries'])
                if page['next_before'] is None: break
                page=(await client.get(base+'/entries',params={'limit':1,'before':page['next_before']},headers=self.bearer())).json()
            self.assertEqual(len(entries),3); self.assertEqual(sum(e['points'] for e in entries),10)
            self.assertNotIn(str(other),json.dumps(entries))
            self.assertEqual((await client.get(base,params={'limit':101},headers=self.bearer())).status_code,422)
            self.assertEqual((await client.post(base,json={'points':999},headers=self.bearer())).status_code,405)
            self.assertEqual((await client.get(f'/v1/tenants/{self.other_tenant}/wallet',headers=self.bearer())).json()['balance'],0)
        self.http_checks(check)

    def test_audit_context_and_reviewer_rls_do_not_leak_other_tenants(self):
        with psycopg.connect(self.app_url) as conn,self.assertRaises(psycopg.Error):
            conn.execute("SELECT tl.record_audit('profile.read','allowed','identity',%s,%s,'TEST_VECTOR')",(str(self.user),uuid4()))
        with owned_transaction(self.app_url,self.principal,self.tenant) as (conn,_):
            conn.execute("SELECT tl.record_audit('profile.read','allowed','identity',%s,%s,'TEST_VECTOR')",(str(self.user),uuid4()))
            self.assertEqual(conn.execute('SELECT * FROM tl.audit_events').fetchall(),[])
        with owned_transaction(self.app_url,self.principal,self.other_tenant) as (conn,_):
            conn.execute("SELECT tl.record_audit('profile.read','allowed','identity',%s,%s,'TEST_VECTOR:other-tenant')",(str(self.user),uuid4()))
        with psycopg.connect(DB_URL) as conn:
            conn.execute("UPDATE tl.memberships SET roles=ARRAY['fraud_reviewer'] WHERE tenant_id=%s AND user_id=%s",(self.tenant,self.user))
        with owned_transaction(self.app_url,self.principal,self.tenant) as (conn,_):
            self.assertEqual([r[0] for r in conn.execute('SELECT tenant_id FROM tl.audit_events')],[self.tenant])

    def test_boarding_accuracy_envelope_and_test_provenance_with_real_postgis(self):
        with psycopg.connect(DB_URL) as conn:
            version=import_catalog(conn,catalog_vector())
            def evaluate(distance,accuracy=5,**kwargs):
                lon,lat=conn.execute("SELECT ST_X(g::geometry),ST_Y(g::geometry) FROM (SELECT ST_Project(location,%s,0) g FROM tl.catalog_stops WHERE version=%s AND code='00001') s",(distance,version)).fetchone()
                return boarding_proximity(conn,version=version,stop_code='00001',latitude=lat,longitude=lon,
                                          accuracy_metres=accuracy,**kwargs)
            self.assertEqual(evaluate(0).state,State.UNAVAILABLE)
            self.assertEqual(evaluate(40,allow_test=True).state,State.PASSED)
            self.assertEqual(evaluate(45,10,allow_test=True).state,State.UNAVAILABLE)
            self.assertEqual(evaluate(70,allow_test=True).state,State.FAILED)
            self.assertEqual(evaluate(0,75,allow_test=True).state,State.UNAVAILABLE)
            self.assertEqual(evaluate(70,radius_metres=100,allow_test=True).state,State.PASSED)
            for invalid in (float('nan'),-1,True):
                with self.assertRaises(ValueError): evaluate(0,invalid,allow_test=True)

    def test_service_catalog_direction_and_loop_occurrences_are_validated(self):
        with psycopg.connect(DB_URL) as conn:
            version=import_catalog(conn,catalog_vector())
            params=dict(version=version,service='T1',operator='TEST',direction=1,boarding_sequence=1,alighting_sequence=3,
                        boarding_stop='00001',alighting_stop='00001')
            self.assertEqual(service_sequence(conn,**params).state,State.UNAVAILABLE)
            self.assertEqual(service_sequence(conn,**params,allow_test=True).state,State.PASSED)
            for changes in ({'service':'NO'},{'operator':'OTHER'},{'direction':2},{'alighting_sequence':1},{'alighting_stop':'00002'}):
                with self.subTest(changes=changes):
                    self.assertEqual(service_sequence(conn,**{**params,**changes},allow_test=True).state,State.FAILED)
            self.assertEqual(service_sequence(conn,**{**params,'version':'f'*64},allow_test=True).state,State.UNAVAILABLE)

    def test_catalog_version_import_is_atomic_idempotent_and_preserves_loop_visits(self):
        document=catalog_vector()
        with psycopg.connect(DB_URL) as conn:
            version=import_catalog(conn,document)
            self.assertEqual(import_catalog(conn,document),version)
            visits=conn.execute("SELECT sequence,stop_code,distance_km FROM tl.catalog_route_stops WHERE version=%s AND direction=1 ORDER BY sequence",(version,)).fetchall()
            self.assertEqual([row[1] for row in visits],['00001','00002','00001'])
            qualities=conn.execute('SELECT geometry_quality FROM tl.route_patterns WHERE source_version=%s',(version,)).fetchall()
            self.assertEqual(qualities,[('TEST_VECTOR',),('TEST_VECTOR',)])
            changed=catalog_vector(); changed['pages'][0]['raw']['value'][0]['Latitude']=1.32
            new_version=import_catalog(conn,rehash(changed))
            self.assertNotEqual(version,new_version)
            self.assertEqual(conn.execute("SELECT ST_Y(location::geometry) FROM tl.catalog_stops WHERE version=%s AND code='00001'",(version,)).fetchone()[0],1.3)
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute('DELETE FROM tl.catalog_versions WHERE id=%s',(version,))

    def test_invalid_catalog_cannot_write_partial_snapshot_or_mutate_geometry(self):
        document=catalog_vector(); document['pages'][2]['raw']['value'][0]['BusStopCode']='99999'; rehash(document)
        with psycopg.connect(DB_URL) as conn:
            before=conn.execute('SELECT count(*) FROM tl.catalog_versions').fetchone()[0]
            with self.assertRaises(ValueError): import_catalog(conn,document)
            self.assertEqual(conn.execute('SELECT count(*) FROM tl.catalog_versions').fetchone()[0],before)
        document=catalog_vector()
        with psycopg.connect(DB_URL) as conn: version=import_catalog(conn,document)
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute("UPDATE tl.route_patterns SET path=ST_GeogFromText('LINESTRING(103.7 1.3,103.9 1.4)') WHERE source_version=%s",(version,))

    def test_catalog_sql_failure_after_stop_inserts_rolls_back_new_version(self):
        document=catalog_vector(); version=normalize_catalog(document)['version']
        collision=uuid5(NAMESPACE_URL,'transportlah:'+version+':T1:TEST:1')
        with psycopg.connect(DB_URL) as conn:
            conn.execute("INSERT INTO tl.route_patterns VALUES (%s,'bus','TEST_VECTOR','1','TEST_VECTOR:injected-conflict','TEST_VECTOR',ST_GeogFromText('LINESTRING(103.8 1.3,103.81 1.31)'))",(collision,))
            with self.assertRaises(psycopg.errors.UniqueViolation): import_catalog(conn,document)
            self.assertEqual(conn.execute('SELECT count(*) FROM tl.catalog_versions WHERE id=%s',(version,)).fetchone()[0],0)
            self.assertEqual(conn.execute('SELECT count(*) FROM tl.catalog_stops WHERE version=%s',(version,)).fetchone()[0],0)

    def test_real_app_login_has_no_bypass_and_admin_credentials_are_rejected(self):
        with psycopg.connect(self.app_url) as conn: assert_app_role(conn)
        with psycopg.connect(DB_URL) as conn, self.assertRaises(PermissionError): assert_app_role(conn)
        with psycopg.connect(self.worker_url) as conn, self.assertRaises(PermissionError): assert_app_role(conn)

    def test_owner_and_tenant_rls_for_actual_login_and_transaction_context_reset(self):
        own=self.ride(); self.ride(user=self.other_user); self.ride(tenant=self.other_tenant)
        with owned_transaction(self.app_url,self.principal,self.tenant) as (conn,identity):
            self.assertEqual(identity[0],self.user)
            self.assertEqual(conn.execute('SELECT id FROM tl.rides').fetchall(),[(own,)])
        with psycopg.connect(self.app_url) as conn:
            self.assertEqual(conn.execute('SELECT id FROM tl.rides').fetchall(),[])
        with self.assertRaises(PermissionError):
            with owned_transaction(self.app_url,self.principal,uuid4()): pass

    def test_commuter_cannot_write_award_or_invoke_worker_function(self):
        ride=self.ride()
        with psycopg.connect(self.app_url) as conn, self.assertRaises(psycopg.errors.InsufficientPrivilege):
            conn.execute('SELECT tl.settle(%s,%s)',(ride,Jsonb(self.decision)))
        with psycopg.connect(self.app_url) as conn, self.assertRaises(psycopg.errors.InsufficientPrivilege):
            conn.execute("INSERT INTO tl.ledger(tenant_id,user_id,ride_id,kind,points,reason) VALUES (%s,%s,%s,'award',999,'attack')",(self.tenant,self.user,ride))

    def test_concurrent_award_retries_credit_once(self):
        ride=self.ride()
        with ThreadPoolExecutor(max_workers=12) as pool: ids=list(pool.map(self.settle,[ride]*12))
        self.assertEqual(len(set(ids)),1)
        with psycopg.connect(DB_URL) as conn:
            self.assertEqual(conn.execute('SELECT count(*),sum(points) FROM tl.ledger WHERE ride_id=%s',(ride,)).fetchone(),(1,10))

    def test_concurrent_different_rides_respect_gross_daily_cap(self):
        rides=[self.ride() for _ in range(15)]
        with ThreadPoolExecutor(max_workers=12) as pool: list(pool.map(self.settle,rides))
        with psycopg.connect(DB_URL) as conn:
            self.assertEqual(conn.execute('SELECT sum(points),count(*) FROM tl.ledger WHERE tenant_id=%s',(self.tenant,)).fetchone(),(100,15))

    def test_conflicting_retry_cannot_rewrite_decision(self):
        ride=self.ride(); self.settle(ride)
        with self.assertRaises(psycopg.Error): self.settle(ride,{**self.decision,'score':'90.00'})

    def test_active_ride_and_test_evidence_in_production_rejected_atomically(self):
        with self.assertRaises(psycopg.Error): self.settle(self.ride(status='active'))
        with psycopg.connect(DB_URL) as conn: conn.execute("UPDATE tl.tenants SET kind='production' WHERE id=%s",(self.tenant,))
        ride=self.ride()
        with self.assertRaises(psycopg.Error): self.settle(ride)
        with psycopg.connect(DB_URL) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM tl.verifications WHERE ride_id=%s',(ride,)).fetchone()[0],0)

    def test_invalid_contract_and_rail_rewards_fail_closed(self):
        for change in ({'policy_version':None},{'test_only':None},{'score':'NaN'},{'tier':5},{'reward_percent':999},{'leaderboard_eligible':False}):
            with self.subTest(change=change),self.assertRaises(psycopg.Error): self.settle(self.ride(),{**self.decision,**change})
        ride=self.ride()
        with psycopg.connect(DB_URL) as conn: conn.execute("UPDATE tl.rides SET mode='rail' WHERE id=%s",(ride,))
        with self.assertRaises(psycopg.Error): self.settle(ride,{**self.decision,'mode':'rail'})
        self.settle(ride,{**self.decision,'mode':'rail','status':'probable','score':'79.00','tier':1,'reward_percent':50,'leaderboard_eligible':False})
        with psycopg.connect(DB_URL) as conn:
            self.assertEqual(conn.execute('SELECT points FROM tl.ledger WHERE ride_id=%s',(ride,)).fetchone()[0],0)

    def test_reversal_concurrency_is_exact_negative_and_immutable(self):
        award=self.settle(self.ride())
        def reverse(_):
            with psycopg.connect(self.worker_url) as conn: return conn.execute('SELECT tl.reverse_award(%s,%s)',(award,'TEST_VECTOR:review')).fetchone()[0]
        with ThreadPoolExecutor(max_workers=8) as pool: ids=list(pool.map(reverse,range(8)))
        self.assertEqual(len(set(ids)),1)
        with psycopg.connect(DB_URL) as conn:
            self.assertEqual(conn.execute('SELECT sum(points) FROM tl.ledger WHERE tenant_id=%s',(self.tenant,)).fetchone()[0],0)
        for query in ('UPDATE tl.ledger SET points=100 WHERE id=%s','DELETE FROM tl.ledger WHERE id=%s'):
            with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error): conn.execute(query,(award,))
        with psycopg.connect(self.worker_url) as conn,self.assertRaises(psycopg.Error):
            conn.execute('SELECT tl.reverse_award(%s,%s)',(ids[0],'reverse reversal'))
        with psycopg.connect(self.worker_url) as conn,self.assertRaises(psycopg.Error):
            conn.execute('SELECT tl.reverse_award(%s,%s)',(award,'different reason'))

    def test_pings_and_decisions_cannot_be_mutated_and_replay_conflict_rejected(self):
        ride=self.ride(); event=uuid4()
        with psycopg.connect(DB_URL) as conn:
            conn.execute("INSERT INTO tl.pings VALUES (%s,%s,%s,%s,now(),5,ST_GeogFromText('POINT(103.8 1.3)'),%s)",(ride,self.tenant,self.user,event,'a'*64))
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute("UPDATE tl.pings SET payload_sha256=%s WHERE ride_id=%s",('b'*64,ride))
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute("INSERT INTO tl.pings VALUES (%s,%s,%s,%s,now(),5,ST_GeogFromText('POINT(103.9 1.3)'),%s)",(ride,self.tenant,self.user,event,'b'*64))
        self.settle(ride)
        with psycopg.connect(DB_URL) as conn,self.assertRaises(psycopg.Error):
            conn.execute("DELETE FROM tl.verifications WHERE ride_id=%s",(ride,))

    def test_spherical_differential_2000_generated_pairs(self):
        rng=random.Random(8174)
        pairs=[(1.2+rng.random()*.25,103.6+rng.random()*.4,1.2+rng.random()*.25,103.6+rng.random()*.4) for _ in range(1996)]
        pairs += [(0,0,0,0),(0,179.999,0,-179.999),(89.999,0,89.999,90),(1.3,103.8,1.300000001,103.8)]
        with psycopg.connect(DB_URL) as conn:
            radius=conn.execute("SELECT ST_DistanceSphere(ST_MakePoint(0,0),ST_MakePoint(1,0))*180/pi()").fetchone()[0]
            errors=[]
            for a,b,c,d in pairs:
                distance=conn.execute('SELECT ST_DistanceSphere(ST_SetSRID(ST_MakePoint(%s,%s),4326),ST_SetSRID(ST_MakePoint(%s,%s),4326))',(b,a,d,c)).fetchone()[0]
                errors.append(abs(distance-haversine_metres(a,b,c,d,radius=radius)))
        self.assertLess(max(errors),0.001)
        print(json.dumps({'spatial_test_origin':'TEST_VECTOR','pairs':len(pairs),'max_sphere_error_metres':max(errors)}))

    def test_metres_route_quality_and_spheroid_boundary(self):
        route=uuid4(); chord=uuid4()
        with psycopg.connect(DB_URL) as conn:
            for identifier,quality in ((route,'authoritative'),(chord,'stop_sequence_chord')):
                # Quality flag exercises query filtering only; generated coordinates are not a real catalog.
                conn.execute("INSERT INTO tl.route_patterns VALUES (%s,'bus','TEST_VECTOR','outbound','TEST_VECTOR',%s,ST_GeogFromText('LINESTRING(103.8 1.3,103.81 1.3)'))",(identifier,quality))
            distance=conn.execute("SELECT ST_Distance(path,ST_GeogFromText('POINT(103.805 1.301)')) FROM tl.route_patterns WHERE id=%s",(route,)).fetchone()[0]
            self.assertGreater(distance,100); self.assertLess(distance,120)
            self.assertIn(route,[r[0] for r in conn.execute(CORRIDOR_SQL,(103.805,1.301,'bus',103.805,1.301,150))])
            self.assertNotIn(chord,[r[0] for r in conn.execute(CORRIDOR_SQL,(103.805,1.301,'bus',103.805,1.301,150))])
            self.assertNotIn(route,[r[0] for r in conn.execute(CORRIDOR_SQL,(103.805,1.301,'bus',103.805,1.301,100))])
            for metres,expected in ((149,True),(151,False)):
                result=conn.execute("SELECT ST_DWithin(ST_GeogFromText('POINT(103.8 1.3)'),ST_Project(ST_GeogFromText('POINT(103.8 1.3)'),%s,0),150)",(metres,)).fetchone()[0]
                self.assertEqual(result,expected)

    def test_eta_and_capture_time_are_never_position_observation_time(self):
        with psycopg.connect(DB_URL) as conn:
            conn.execute("INSERT INTO tl.arrival_observations(stop_code,service,slot,captured_at,estimated_arrival,position,monitored,raw_sha256,historical) VALUES ('TEST_VECTOR','x','NextBus',now(),now(),ST_GeogFromText('POINT(103.8 1.3)'),true,%s,false)",('c'*64,))
            now=datetime.now(timezone.utc)
            self.assertEqual(conn.execute(POSITION_SQL,(now,now,103.8,1.3,150)).fetchall(),[])

    def test_gist_plan_uses_matching_native_geography_index(self):
        with psycopg.connect(DB_URL) as conn:
            conn.execute("INSERT INTO tl.stops SELECT 'TEST_VECTOR:'||g,'bus','TEST_VECTOR','TEST_VECTOR',ST_SetSRID(ST_MakePoint(103.6+mod(g,100)*.004,1.2+(g/100)*.004),4326)::geography FROM generate_series(1,10000) g ON CONFLICT DO NOTHING")
            conn.execute('ANALYZE tl.stops')
            plan=conn.execute("EXPLAIN (ANALYZE,FORMAT JSON) SELECT code FROM tl.stops WHERE ST_DWithin(location,ST_GeogFromText('POINT(103.8 1.3)'),100)").fetchone()[0]
            self.assertIn('stop_location_gist',json.dumps(plan))
            print(json.dumps({'spatial_test_origin':'TEST_VECTOR','default_planner_gist':True,'plan':plan}))
