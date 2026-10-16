"""Explicit modes and bounded configuration. Secrets never appear in repr."""

from dataclasses import dataclass, field
import math
import os
from pathlib import Path
import re


@dataclass(frozen=True)
class Settings:
    mode: str = "OFFLINE_FIXTURE"
    capture_dir: Path = Path("private/captures")
    lta_account_key: str = field(default="", repr=False)
    api_service_token: str = field(default="", repr=False)
    database_url: str = field(default="", repr=False)
    redis_url: str = field(default="", repr=False)
    commuter_api_enabled: bool = False
    app_database_url: str = field(default="", repr=False)
    oidc_issuer: str = ""
    oidc_audience: str = ""
    oidc_jwks_url: str = ""
    cache_ttl_seconds: float = 30.0
    min_poll_interval_seconds: float = 20.0
    upstream_timeout_seconds: float = 10.0
    max_active_stops: int = 128
    max_cache_entries: int = 512
    active_stops: tuple[tuple[str, str | None], ...] = ()

    def __post_init__(self):
        if type(self.commuter_api_enabled) is not bool:
            raise ValueError('COMMUTER_API_ENABLED must be boolean')
        if self.commuter_api_enabled and not all((self.app_database_url,self.oidc_issuer,self.oidc_audience,self.oidc_jwks_url)):
            raise ValueError('Commuter API needs a separate DB login and provider configuration')
        if self.mode not in {"LIVE_NETWORK", "OFFLINE_FIXTURE"}:
            raise ValueError("LTA_MODE must be LIVE_NETWORK or OFFLINE_FIXTURE")
        for value in (self.cache_ttl_seconds, self.min_poll_interval_seconds, self.upstream_timeout_seconds):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Cache, polling, and timeout values must be finite and positive")
        if self.max_active_stops < 1 or self.max_cache_entries < 1:
            raise ValueError("Capacity limits must be positive")
        if self.api_service_token and len(self.api_service_token) < 32:
            raise ValueError("API_SERVICE_TOKEN must have at least 32 characters")
        if self.mode == "LIVE_NETWORK" and not self.lta_account_key:
            raise ValueError("LIVE_NETWORK requires an LTA key; no fallback is permitted")
        if self.mode == "LIVE_NETWORK" and self.min_poll_interval_seconds < 20:
            raise ValueError("Live polling must not be configured below the documented 20-second refresh")
        for stop, service in self.active_stops:
            if not re.fullmatch(r"\d{5}", stop) or (service is not None and not re.fullmatch(r"[A-Za-z0-9]{1,8}", service)):
                raise ValueError("ACTIVE_STOPS entries must be five-digit stops with optional service")
        if len(self.active_stops) > self.max_active_stops:
            raise ValueError("ACTIVE_STOPS exceeds configured capacity")

    @classmethod
    def from_env(cls):
        commuter_enabled=os.environ.get('COMMUTER_API_ENABLED','false').lower()
        if commuter_enabled not in {'true','false'}: raise ValueError('COMMUTER_API_ENABLED must be true or false')
        key = os.environ.get("LTA_DATAMALL_KEY", "").strip()
        key_path = os.environ.get("LTA_KEY_PATH", "")
        if not key and key_path:
            # Path errors are explicit, and key contents are never logged.
            key = Path(key_path).read_text(encoding="utf-8").strip()
        targets = []
        for value in os.environ.get("ACTIVE_STOPS", "").split(","):
            if value.strip():
                stop, separator, service = value.strip().partition(":")
                targets.append((stop, service if separator else None))
        return cls(
            mode=os.environ.get("LTA_MODE", "OFFLINE_FIXTURE"),
            capture_dir=Path(os.environ.get("LTA_CAPTURE_DIR", "private/captures")),
            lta_account_key=key,
            api_service_token=os.environ.get("API_SERVICE_TOKEN", ""),
            database_url=os.environ.get("DATABASE_URL", ""),
            redis_url=os.environ.get("REDIS_URL", ""),
            commuter_api_enabled=commuter_enabled=='true',
            app_database_url=os.environ.get('APP_DATABASE_URL',''),
            oidc_issuer=os.environ.get('OIDC_ISSUER',''),
            oidc_audience=os.environ.get('OIDC_AUDIENCE',''),
            oidc_jwks_url=os.environ.get('OIDC_JWKS_URL',''),
            cache_ttl_seconds=float(os.environ.get("CACHE_TTL_SECONDS", "30")),
            min_poll_interval_seconds=float(os.environ.get("MIN_POLL_INTERVAL_SECONDS", "20")),
            upstream_timeout_seconds=float(os.environ.get("UPSTREAM_TIMEOUT_SECONDS", "10")),
            max_active_stops=int(os.environ.get("MAX_ACTIVE_STOPS", "128")),
            max_cache_entries=int(os.environ.get("MAX_CACHE_ENTRIES", "512")),
            active_stops=tuple(dict.fromkeys(targets)),
        )
