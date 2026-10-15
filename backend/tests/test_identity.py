"""Generated cryptographic test vectors; no external identity-provider proof."""
import asyncio
import json
import time
import unittest
from cryptography.hazmat.primitives.asymmetric import rsa
import httpx
import jwt
from backend.app.identity import AuthenticationFailed, OIDCVerifier


class IdentityChecks(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        self.jwk=json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(self.key.public_key()))
        self.jwk.update(kid='test-key',alg='RS256',use='sig')
        self.requests=[]
        def handler(request):
            self.requests.append(str(request.url))
            return httpx.Response(200,json={'keys':[self.jwk]})
        self.verifier=OIDCVerifier(issuer='https://issuer.example',audience='transportlah-test',
                                  jwks_url='https://issuer.example/jwks',client=httpx.AsyncClient(transport=httpx.MockTransport(handler)))

    async def asyncTearDown(self): await self.verifier.close()

    def token(self,changes=None,*,key=None,headers=None):
        claims={'iss':'https://issuer.example','aud':'transportlah-test','sub':'TEST_VECTOR:user',
                'iat':int(time.time())-1,'exp':int(time.time())+60,'roles':['super_admin'],'tenant':'attacker'}
        claims.update(changes or {})
        return jwt.encode(claims,key or self.key,algorithm='RS256',headers=headers or {'kid':'test-key'})

    async def test_signature_validated_but_role_and_tenant_claims_ignored(self):
        principal=await self.verifier.verify(self.token())
        self.assertEqual(principal.subject,'TEST_VECTOR:user')
        self.assertFalse(hasattr(principal,'roles')); self.assertFalse(hasattr(principal,'tenant'))
        await self.verifier.verify(self.token())
        self.assertEqual(len(self.requests),1)

    async def test_wrong_signature_issuer_audience_expiry_and_future_issuance_fail(self):
        for changes in ({'iss':'https://attacker.example'},{'aud':'other'},{'exp':int(time.time())-5},
                        {'iat':int(time.time())+120},{'sub':''},{'exp':'9999999999'},{'iat':True}):
            with self.subTest(changes=changes), self.assertRaises(AuthenticationFailed):
                await self.verifier.verify(self.token(changes))
        with self.assertRaises(AuthenticationFailed): await self.verifier.verify(self.token(key=self.other))

    async def test_missing_expiration_and_unsigned_tokens_fail(self):
        claims={'iss':'https://issuer.example','aud':'transportlah-test','sub':'TEST_VECTOR:u','iat':int(time.time())}
        signed=jwt.encode(claims,self.key,algorithm='RS256',headers={'kid':'test-key'})
        unsigned=jwt.encode(claims,key=None,algorithm='none',headers={'kid':'test-key'})
        for token in (signed,unsigned,'garbage','x'*16385):
            with self.assertRaises(AuthenticationFailed): await self.verifier.verify(token)

    async def test_token_key_urls_are_ignored_and_unknown_kids_refresh_is_bounded(self):
        await self.verifier.verify(self.token(headers={'kid':'test-key','jku':'https://attacker.example/jwks'}))
        unknown=self.token(headers={'kid':'unknown'})
        results=await asyncio.gather(*(self.verifier.verify(unknown) for _ in range(20)),return_exceptions=True)
        self.assertTrue(all(isinstance(r,AuthenticationFailed) for r in results))
        self.assertEqual(self.requests,['https://issuer.example/jwks'])

    async def test_key_fetch_failure_is_closed(self):
        self.verifier.client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(503)))
        with self.assertRaises(AuthenticationFailed): await self.verifier.verify(self.token())

    def test_insecure_issuer_or_symmetric_algorithm_configuration_rejected(self):
        for opts in ({'issuer':'http://issuer.example'},{'jwks_url':'http://issuer.example/jwks'},{'algorithms':('HS256',)}):
            config={'issuer':'https://issuer.example','audience':'x','jwks_url':'https://issuer.example/jwks',**opts}
            with self.assertRaises(ValueError): OIDCVerifier(**config)
