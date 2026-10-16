"""Ingestion API only. No rider verification, rewards, or production auth claims."""

import asyncio
from contextlib import asynccontextmanager, suppress
import json
import logging
import secrets
import time
from uuid import UUID, uuid4
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import psycopg
from redis.asyncio import Redis

from .config import Settings
from .ingestion import ArrivalService
from .models import Arrivals
from .transport import CaptureTransport, LiveTransport, SourceUnavailable
from .identity import OIDCVerifier,AuthenticationFailed,Principal
from .ownership import UnsafeDatabaseRole
from .user_data import read_user_data,ActionDenied,ResourceMissing
from .http_boundary import BoundedBodyMiddleware


log = logging.getLogger("transportlah")
bearer = HTTPBearer(auto_error=False)


def create_app(settings=None,*,identity_verifier=None):
    if not log.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        log.addHandler(handler)
        log.setLevel(logging.INFO)
        log.propagate = False
    settings = settings or Settings.from_env()
    verifier = (identity_verifier or OIDCVerifier(issuer=settings.oidc_issuer,audience=settings.oidc_audience,
                jwks_url=settings.oidc_jwks_url)) if settings.commuter_api_enabled else None
    transport = LiveTransport(settings.lta_account_key, settings.upstream_timeout_seconds) if settings.mode == "LIVE_NETWORK" else CaptureTransport(settings.capture_dir)
    service = ArrivalService(transport, settings.cache_ttl_seconds, settings.min_poll_interval_seconds, settings.max_active_stops, settings.max_cache_entries)

    @asynccontextmanager
    async def lifespan(app):
        task = asyncio.create_task(service.poll(settings.active_stops, settings.cache_ttl_seconds)) if settings.active_stops else None
        try:
            yield
        finally:
            if task:
                task.cancel()
                with suppress(asyncio.CancelledError):
                    await task
            await transport.close()
            if verifier: await verifier.close()

    app = FastAPI(title="TransportLah ingestion foundation", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.state.arrivals = service
    app.add_middleware(BoundedBodyMiddleware)

    @app.middleware("http")
    async def request_log(request, call_next):
        value = request.headers.get("X-Request-ID", "")
        try:
            request_id = str(UUID(value))
        except (ValueError, AttributeError):
            request_id = str(uuid4())
        started = time.monotonic()
        request.state.request_id=request_id
        try:
            response = await call_next(request)
        except Exception:
            response=JSONResponse(status_code=500,content={'detail':'Internal service failure','request_id':request_id})
        response.headers["X-Request-ID"] = request_id
        # Log only selected metadata, never query strings, credentials, body, GPS, or raw exceptions.
        log.info(json.dumps({"event": "http_request", "request_id": request_id, "method": request.method, "status": response.status_code, "duration_ms": round((time.monotonic() - started) * 1000, 3)}))
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request,error):
        return JSONResponse(status_code=422,content={'detail':[{'loc':list(e['loc']),'type':e['type']} for e in error.errors()],
                            'request_id':request.state.request_id})

    async def commuter(credentials: Annotated[HTTPAuthorizationCredentials | None,Depends(bearer)]):
        if verifier is None: raise HTTPException(503,'Commuter identity is not configured')
        if credentials is None: raise HTTPException(401,'Commuter authorization required',headers={'WWW-Authenticate':'Bearer'})
        try: return await verifier.verify(credentials.credentials)
        except AuthenticationFailed:
            raise HTTPException(401,'Invalid commuter authorization',headers={'WWW-Authenticate':'Bearer'}) from None

    def owner_read(request,tenant_id,principal,action,**kwargs):
        try:
            return read_user_data(settings.app_database_url,principal,tenant_id,action,UUID(request.state.request_id),**kwargs)
        except UnsafeDatabaseRole: raise HTTPException(503,'Commuter database role is unsafe') from None
        except (PermissionError,ResourceMissing): raise HTTPException(404,'Resource not found') from None
        except ActionDenied: raise HTTPException(403,'Action is not permitted') from None
        except psycopg.Error: raise HTTPException(503,'Commuter data is unavailable') from None

    @app.get('/v1/tenants/{tenant_id}/me')
    def me(tenant_id:UUID,request:Request,principal:Annotated[Principal,Depends(commuter)]):
        return owner_read(request,tenant_id,principal,'profile.read')

    @app.get('/v1/tenants/{tenant_id}/rides/{ride_id}')
    def ride(tenant_id:UUID,ride_id:UUID,request:Request,principal:Annotated[Principal,Depends(commuter)]):
        return owner_read(request,tenant_id,principal,'ride.read',resource=ride_id)

    @app.get('/v1/tenants/{tenant_id}/wallet')
    @app.get('/v1/tenants/{tenant_id}/wallet/entries')
    def wallet(tenant_id:UUID,request:Request,principal:Annotated[Principal,Depends(commuter)],
               before:Annotated[int|None,Query(ge=1,le=9223372036854775807)]=None,
               limit:Annotated[int,Query(ge=1,le=100)]=20):
        return owner_read(request,tenant_id,principal,'wallet.read',before=before,limit=limit)

    @app.get('/v1/tenants/{tenant_id}/admin/audit-events')
    def audit_events(tenant_id:UUID,request:Request,principal:Annotated[Principal,Depends(commuter)],
                     before:Annotated[int|None,Query(ge=1,le=9223372036854775807)]=None,
                     limit:Annotated[int,Query(ge=1,le=100)]=20):
        return owner_read(request,tenant_id,principal,'audit.read',before=before,limit=limit)

    async def authorize(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
        if not settings.api_service_token:
            raise HTTPException(503, "Service authorization is not configured")
        if credentials is None or not secrets.compare_digest(credentials.credentials.encode(), settings.api_service_token.encode()):
            raise HTTPException(401, "Service authorization required", headers={"WWW-Authenticate": "Bearer"})

    @app.exception_handler(SourceUnavailable)
    async def unavailable(request, error):
        headers = {"Retry-After": str(int(error.retry_after))} if error.retry_after else None
        return JSONResponse(status_code=error.status_code, content={"detail": str(error)}, headers=headers)

    @app.get("/health")
    async def health():
        return {"status": "alive", "mode": settings.mode, "verification_enabled": False}

    @app.get("/ready")
    async def ready():
        async def postgres_check():
            if not settings.database_url:
                return "not_configured"
            try:
                async with await psycopg.AsyncConnection.connect(settings.database_url, connect_timeout=3) as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute("SELECT PostGIS_Version()")
                        await cursor.fetchone()
                return "reachable_postgis"
            except Exception:
                return "unreachable_or_postgis_missing"

        async def redis_check():
            if not settings.redis_url:
                return "not_configured"
            client = None
            try:
                client = Redis.from_url(settings.redis_url, socket_connect_timeout=3, socket_timeout=3)
                await client.ping()
                return "reachable"
            except Exception:
                return "unreachable"
            finally:
                if client is not None:
                    await client.aclose()

        async def bounded(check):
            try:
                return await asyncio.wait_for(check(), timeout=4)
            except TimeoutError:
                return "timeout"

        pg, redis = await asyncio.gather(bounded(postgres_check), bounded(redis_check))
        source = "live_configured_handshake_unverified" if settings.mode == "LIVE_NETWORK" else "historical_replay_available" if transport.available else "no_capture_available"
        live_succeeded = (settings.mode == "LIVE_NETWORK" and service.last_success_at is not None
                          and time.monotonic() - service.last_success_at <= settings.cache_ttl_seconds
                          and (service.last_failure_at is None or service.last_success_at >= service.last_failure_at))
        source_ready = live_succeeded if settings.mode == "LIVE_NETWORK" else transport.available
        is_ready = pg == "reachable_postgis" and redis == "reachable" and source_ready and bool(settings.api_service_token)
        components = {"postgres": pg, "redis": redis, "transit_source": "live_response_processed" if live_succeeded else source, "service_authorization": "configured" if settings.api_service_token else "not_configured"}
        return JSONResponse(status_code=200 if is_ready else 503, content={"ready": is_ready, "components": components, "verification_enabled": False, "cache_scope": "single_process", "metrics": service.metrics})

    @app.get("/v1/arrivals/{bus_stop_code}", response_model=Arrivals, dependencies=[Depends(authorize)])
    async def arrivals(bus_stop_code: Annotated[str, Path(pattern=r"^\d{5}$")], service_no: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9]{1,8}$")] = None):
        return await service.get(bus_stop_code, service_no)

    @app.get("/v1/arrivals", dependencies=[Depends(authorize)])
    async def multiple_arrivals(bus_stop_codes: Annotated[list[str], Query(min_length=1, max_length=10)], service_no: Annotated[str | None, Query(pattern=r"^[A-Za-z0-9]{1,8}$")] = None):
        import re
        if any(not re.fullmatch(r"\d{5}", stop) for stop in bus_stop_codes):
            raise HTTPException(422, "Every bus stop code must have five digits")
        async def one(stop):
            try:
                return {"bus_stop_code": stop, "status": "ok", "arrivals": (await service.get(stop, service_no)).model_dump(mode="json")}
            except SourceUnavailable as error:
                return {"bus_stop_code": stop, "status": "unavailable", "detail": str(error)}
        return {"results": await asyncio.gather(*(one(stop) for stop in dict.fromkeys(bus_stop_codes)))}

    return app


app = create_app()
