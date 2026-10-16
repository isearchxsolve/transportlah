"""Request bounds/redaction checks with no external identity or database claims."""
from pathlib import Path
import secrets
import unittest
from uuid import uuid4
import httpx
from backend.app.config import Settings
from backend.app.main import create_app


class HttpBoundaryChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.token=secrets.token_hex(32)
        self.app=create_app(Settings(capture_dir=Path(__file__).parent/'data',api_service_token=self.token))
        self.client=httpx.AsyncClient(transport=httpx.ASGITransport(app=self.app),base_url='http://test')

    async def asyncTearDown(self): await self.client.aclose()

    async def test_disabled_commuter_boundary_rejects_operator_token(self):
        response=await self.client.get(f'/v1/tenants/{uuid4()}/wallet',headers={'Authorization':'Bearer '+self.token})
        self.assertEqual(response.status_code,503)

    async def test_oversized_declared_and_chunked_bodies_are_bounded(self):
        response=await self.client.post('/unknown',content=b'x'*262145)
        self.assertEqual(response.status_code,413); self.assertIn('x-request-id',response.headers)
        async def chunks():
            for _ in range(5): yield b'x'*65536
        response=await self.client.post('/unknown',content=chunks())
        self.assertEqual(response.status_code,413)

    async def test_invalid_and_mismatched_lengths_are_rejected_without_echo(self):
        for value,status in (('bad',400),('9'*5000,413),('0',400)):
            response=await self.client.post('/unknown',content=b'x',headers={'Content-Length':value})
            self.assertEqual(response.status_code,status)

    async def test_validation_errors_and_logs_do_not_echo_credentials_or_location(self):
        marker='TEST_VECTOR:private-coordinate-or-token'
        with self.assertLogs('transportlah',level='INFO') as captured:
            response=await self.client.get('/v1/arrivals/'+marker,params={'latitude':marker},headers={'Authorization':'Bearer '+self.token,'X-Request-ID':marker})
        self.assertEqual(response.status_code,422)
        self.assertNotIn(marker,response.text); self.assertNotIn(self.token,response.text)
        self.assertNotIn(marker,' '.join(captured.output)); self.assertNotIn(self.token,' '.join(captured.output))

    def test_commuter_configuration_is_explicit_and_private(self):
        with self.assertRaises(ValueError): Settings(commuter_api_enabled=True)
        value=secrets.token_hex(32)
        self.assertNotIn(value,repr(Settings(app_database_url=value)))
