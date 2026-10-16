"""TEST_VECTOR mutations and HTTP stubs; original capture is never changed.

Stubbed LIVE_NETWORK executions test client behavior, not a real LTA handshake.
"""
import asyncio
from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path
import unittest
import httpx
from backend.app.models import parse_arrivals
from backend.app.transport import CapturedResponse,CaptureTransport,LiveTransport,SourceUnavailable,raw_hash
from backend.app.ingestion import ArrivalService
from backend.app.permissions import permits

DATA=Path(__file__).parent/'data'
ORIGINAL=json.loads((DATA/'lta_stop44009_service190_20261010.json').read_text())


def mutated_capture(raw):
    return CapturedResponse(raw,datetime.fromisoformat(ORIGINAL['captured_at_utc']),raw_hash(raw),'OFFLINE_FIXTURE','190')


class TelemetryEdges(unittest.TestCase):
    def test_monitoring_variants_empty_fields_and_uncertain_position(self):
        for value,expected in ((1,True),('1',True),(0,False),('0',False),('',None),(None,None),(True,None),(2,None)):
            raw=deepcopy(ORIGINAL['raw']); candidate=raw['Services'][0]['NextBus']
            candidate.update(Monitored=value,EstimatedArrival='',Latitude='',Longitude='')
            parsed=parse_arrivals(mutated_capture(raw)).services[0].candidates[0]
            self.assertIs(parsed.monitored,expected)
            self.assertIsNone(parsed.estimated_arrival); self.assertIsNone(parsed.location); self.assertIsNone(parsed.position_observed_at)

    def test_absent_service_and_candidates_are_unavailable_without_invention(self):
        raw={'BusStopCode':'44009','Services':[]}
        self.assertEqual(parse_arrivals(mutated_capture(raw)).services,())
        raw=deepcopy(ORIGINAL['raw']); raw['Services'][0]['NextBus']=None
        result=parse_arrivals(mutated_capture(raw),requested_service='190')
        self.assertEqual([c.slot for c in result.services[0].candidates],['NextBus2','NextBus3'])
        self.assertEqual(parse_arrivals(mutated_capture(raw),requested_service='999').services,())

    def test_malformed_payloads_scope_and_invalid_timestamps_fail_conservatively(self):
        for raw in ({'BusStopCode':'bad','Services':[]},{'BusStopCode':'44009','Services':'bad'},
                    {'BusStopCode':'44009','Services':[{'ServiceNo':''}]},
                    {'BusStopCode':'44009','Services':[{'ServiceNo':'190','NextBus':'bad'}]}):
            with self.assertRaises(SourceUnavailable): parse_arrivals(mutated_capture(raw),'44009','190')
        raw=deepcopy(ORIGINAL['raw']); raw['Services'][0]['NextBus']['EstimatedArrival']='2026-10-16T01:00:00'
        candidate=parse_arrivals(mutated_capture(raw)).services[0].candidates[0]
        self.assertIsNone(candidate.estimated_arrival); self.assertIn('arrival_timezone_missing',candidate.quality_flags)
        with self.assertRaises(SourceUnavailable): parse_arrivals(mutated_capture(ORIGINAL['raw']),'09048','190')

    def test_nonfinite_and_boolean_coordinates_remain_unavailable(self):
        for latitude in ('NaN','inf',True,91):
            raw=deepcopy(ORIGINAL['raw']); raw['Services'][0]['NextBus'].update(Latitude=latitude,Longitude='103.8')
            self.assertIsNone(parse_arrivals(mutated_capture(raw)).services[0].candidates[0].location)

    def test_roles_are_action_specific_and_unknown_roles_cannot_escalate(self):
        self.assertTrue(permits(['commuter'],'wallet.read'))
        self.assertFalse(permits(['campaign_manager'],'fraud.review'))
        self.assertTrue(permits(['campaign_manager'],'campaign.manage'))
        self.assertTrue(permits(['fraud_reviewer'],'audit.read'))
        self.assertFalse(permits(['fraud_reviewer'],'memberships.manage'))
        self.assertTrue(permits(['super_admin'],'memberships.manage'))
        self.assertFalse(permits(['attacker'],'wallet.read'))


class TransportEdges(unittest.IsolatedAsyncioTestCase):
    async def source(self,handler):
        source=LiveTransport('TEST_VECTOR:fake-key')
        await source._client.aclose()
        source._client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
        return source

    async def test_both_transports_use_the_same_parser_without_payload_drift(self):
        calls=[]
        def handler(request):
            calls.append((request.url.path,dict(request.url.params)))
            return httpx.Response(200,json=ORIGINAL['raw'])
        live=await self.source(handler)
        try:
            response=await live.fetch('44009','190')
            replay=await CaptureTransport(DATA).fetch('44009','190')
            self.assertEqual(response.raw,replay.raw); self.assertEqual(response.raw_sha256,replay.raw_sha256)
            a=parse_arrivals(response,'44009','190'); b=parse_arrivals(replay,'44009','190')
            self.assertEqual(a.services,b.services)
            self.assertNotEqual(a.source,b.source); self.assertFalse(a.is_historical_replay); self.assertTrue(b.is_historical_replay)
            self.assertEqual(calls,[('/ltaodataservice/v3/BusArrival',{'BusStopCode':'44009','ServiceNo':'190'})])
        finally: await live.close()

    async def test_http_rejection_timeout_malformed_body_and_size_limits_never_fallback(self):
        responses=[httpx.Response(401),httpx.Response(500),httpx.Response(200,content=b'not json'),
                   httpx.Response(200,json=[]),httpx.Response(200,content=b'x'*(2*1024*1024+1))]
        for response in responses:
            source=await self.source(lambda request:response)
            try:
                with self.assertRaises(SourceUnavailable): await source.fetch('44009','190')
            finally: await source.close()
        def timeout(request): raise httpx.ReadTimeout('TEST_VECTOR:do-not-expose-key')
        source=await self.source(timeout)
        try:
            with self.assertRaises(SourceUnavailable) as error: await source.fetch('44009','190')
            self.assertNotIn('do-not-expose',str(error.exception))
        finally: await source.close()

    async def test_retry_after_is_bounded_and_invalid_values_never_become_nan(self):
        for value,expected in (('0',20),('99999',300),('45',45),('NaN',20),('inf',20),('bad',20)):
            source=await self.source(lambda r:httpx.Response(429,headers={'Retry-After':value}))
            try:
                with self.assertRaises(SourceUnavailable) as error: await source.fetch('44009','190')
                self.assertEqual(error.exception.retry_after,expected)
            finally: await source.close()

    async def test_failure_does_not_refresh_cache_or_claim_a_success(self):
        calls=[]
        def handler(request): calls.append(request); return httpx.Response(503)
        source=await self.source(handler); service=ArrivalService(source,cache_ttl=.01,min_poll_interval=.02)
        try:
            for _ in range(2):
                with self.assertRaises(SourceUnavailable): await service.get('44009','190')
            self.assertEqual(len(calls),2); self.assertIsNone(service.last_success_at)
            self.assertEqual(service.metrics['source_failures'],2); self.assertEqual(service.metrics['cache_hits'],0)
        finally: await source.close()
