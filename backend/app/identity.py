"""Provider-backed JWT verification. Token claims never grant product roles."""
from dataclasses import dataclass
import asyncio
import json
import math
import time
from urllib.parse import urlparse

import httpx
import jwt


class AuthenticationFailed(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    issuer: str
    subject: str


class OIDCVerifier:
    def __init__(self, *, issuer, audience, jwks_url, algorithms=("RS256",), client=None, ttl=300):
        if any(urlparse(v).scheme != 'https' or not urlparse(v).netloc or urlparse(v).username for v in (issuer,jwks_url)):
            raise ValueError('Issuer and fixed JWKS URL must be HTTPS')
        if not audience or not algorithms or not set(algorithms) <= {'RS256','ES256'} or ttl<=0:
            raise ValueError('Audience, asymmetric algorithms and positive TTL required')
        self.issuer,self.audience,self.url,self.algorithms=issuer,audience,jwks_url,algorithms
        self.client=client or httpx.AsyncClient(timeout=5,follow_redirects=False)
        self.keys={}; self.expires=0; self.last_attempt=float('-inf'); self.ttl=ttl; self.lock=asyncio.Lock()

    async def close(self):
        await self.client.aclose()

    async def _key(self,kid,algorithm):
        now=time.monotonic()
        if now<self.expires and (kid,algorithm) in self.keys:
            return self.keys[(kid,algorithm)]
        async with self.lock:
            now=time.monotonic()
            if now<self.expires and (kid,algorithm) in self.keys:
                return self.keys[(kid,algorithm)]
            # Unknown kids cannot cause an unbounded issuer fetch storm.
            if now-self.last_attempt<30:
                raise AuthenticationFailed('Key refresh unavailable')
            self.last_attempt=now
            try:
                async with self.client.stream('GET',self.url) as response:
                    response.raise_for_status(); data=bytearray()
                    async for chunk in response.aiter_bytes():
                        data.extend(chunk)
                        if len(data)>262144: raise ValueError('JWKS too large')
                document=json.loads(data)
                if not isinstance(document.get('keys'),list) or not 1<=len(document['keys'])<=64:
                    raise ValueError('Invalid key set')
                keys={}
                for entry in document['keys']:
                    if entry.get('use','sig')!='sig' or 'verify' not in entry.get('key_ops',['verify']): continue
                    alg=entry.get('alg'); key_id=entry.get('kid')
                    if alg not in self.algorithms or not isinstance(key_id,str) or not 1<=len(key_id)<=128: continue
                    if (alg=='RS256' and entry.get('kty')!='RSA') or (alg=='ES256' and (entry.get('kty')!='EC' or entry.get('crv')!='P-256')): continue
                    if (key_id,alg) in keys: raise ValueError('Duplicate signing key')
                    key=jwt.PyJWK.from_dict(entry,algorithm=alg).key
                    if alg=='RS256' and key.key_size<2048: raise ValueError('Weak signing key')
                    keys[(key_id,alg)]=key
                self.keys=keys; self.expires=now+self.ttl
            except (httpx.HTTPError,ValueError,TypeError,KeyError,jwt.PyJWTError) as exc:
                raise AuthenticationFailed('Signing keys unavailable') from exc
            if (kid,algorithm) not in self.keys: raise AuthenticationFailed('Unknown signing key')
            return self.keys[(kid,algorithm)]

    async def verify(self,token):
        if not isinstance(token,str) or len(token)>16384:
            raise AuthenticationFailed('Invalid bearer token')
        try:
            header=jwt.get_unverified_header(token)
            alg=header.get('alg'); kid=header.get('kid')
            if alg not in self.algorithms or not isinstance(kid,str) or not 1<=len(kid)<=128 or header.get('crit'):
                raise AuthenticationFailed('Unsupported signing header')
            key=await self._key(kid,alg)
            claims=jwt.decode(token,key,algorithms=[alg],audience=self.audience,issuer=self.issuer,
                              options={'require':['exp','iat','iss','aud','sub']},leeway=0)
            if not isinstance(claims['sub'],str) or not 1<=len(claims['sub'])<=255:
                raise AuthenticationFailed('Invalid subject')
            if any(type(claims[f]) not in (int,float) or not math.isfinite(claims[f]) for f in ('exp','iat')) or claims['exp']<=claims['iat']:
                raise AuthenticationFailed('Invalid token lifetime')
            return Principal(self.issuer,claims['sub'])
        except (jwt.PyJWTError,ValueError,TypeError,KeyError,OverflowError) as exc:
            raise AuthenticationFailed('Invalid bearer token') from exc
