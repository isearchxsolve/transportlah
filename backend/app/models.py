"""Arrival candidates are not a single-vehicle trajectory or passenger proof."""

from datetime import datetime
import math
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .transport import CapturedResponse, SourceUnavailable


class FrozenModel(BaseModel):
    model_config = ConfigDict(frozen=True)


class Location(FrozenModel):
    latitude: float
    longitude: float


class ArrivalCandidate(FrozenModel):
    slot: Literal["NextBus", "NextBus2", "NextBus3"]
    estimated_arrival: datetime | None
    monitored: bool | None
    location: Location | None
    position_observed_at: datetime | None = None
    origin_code: str | None
    destination_code: str | None
    visit_number: str | None
    load: str | None
    vehicle_type: str | None
    feature: str | None
    quality_flags: tuple[str, ...]


class ServiceArrivals(FrozenModel):
    service_no: str
    operator: str | None
    candidates: tuple[ArrivalCandidate, ...]


class Arrivals(FrozenModel):
    bus_stop_code: str
    services: tuple[ServiceArrivals, ...]
    source: Literal["LIVE_NETWORK", "OFFLINE_FIXTURE"]
    source_captured_at: datetime
    raw_sha256: str
    is_historical_replay: bool
    provenance: str
    source_snapshot_age_seconds: float = 0.0
    snapshot_fresh: bool = False
    cache_hit: bool = False


def optional_string(value):
    return str(value) if value not in (None, "") else None


def parse_arrivals(capture: CapturedResponse, requested_stop=None, requested_service=None):
    raw = capture.raw
    stop = raw.get("BusStopCode")
    services = raw.get("Services")
    if not isinstance(stop, str) or not stop.isdigit() or len(stop) != 5 or not isinstance(services, list):
        raise SourceUnavailable("LTA arrival response has an invalid stop/services structure", status_code=502)
    if requested_stop is not None and stop != requested_stop:
        raise SourceUnavailable("LTA response stop differs from the requested stop", status_code=502)
    parsed_services = []
    for service in services:
        if not isinstance(service, dict) or not isinstance(service.get("ServiceNo"), str):
            raise SourceUnavailable("LTA service entry is malformed", status_code=502)
        if requested_service and service["ServiceNo"] != requested_service:
            continue
        candidates = []
        for slot in ("NextBus", "NextBus2", "NextBus3"):
            candidate = service.get(slot)
            if candidate is None:
                continue
            if not isinstance(candidate, dict):
                raise SourceUnavailable("LTA arrival candidate is malformed", status_code=502)
            flags = ["position_observation_time_not_provided"]
            eta = None
            value = candidate.get("EstimatedArrival")
            if value:
                try:
                    eta = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                    if eta.tzinfo is None:
                        eta = None
                        flags.append("arrival_timezone_missing")
                except ValueError:
                    flags.append("invalid_arrival_timestamp")
            else:
                flags.append("arrival_unavailable")
            value = candidate.get("Monitored")
            monitored = True if value in (1, "1") else False if value in (0, "0") else None
            if monitored is False:
                flags.append("schedule_based_estimate")
            elif monitored is None:
                flags.append("monitoring_status_unavailable")
            location = None
            try:
                latitude = float(candidate["Latitude"])
                longitude = float(candidate["Longitude"])
                if math.isfinite(latitude) and math.isfinite(longitude) and -90 <= latitude <= 90 and -180 <= longitude <= 180 and (latitude, longitude) != (0.0, 0.0):
                    location = Location(latitude=latitude, longitude=longitude)
            except (KeyError, ValueError, TypeError):
                pass
            if location is None:
                flags.append("unavailable_location")
            candidates.append(ArrivalCandidate(
                slot=slot, estimated_arrival=eta, monitored=monitored, location=location,
                origin_code=optional_string(candidate.get("OriginCode")),
                destination_code=optional_string(candidate.get("DestinationCode")),
                visit_number=optional_string(candidate.get("VisitNumber")),
                load=optional_string(candidate.get("Load")),
                vehicle_type=optional_string(candidate.get("Type")),
                feature=optional_string(candidate.get("Feature")), quality_flags=tuple(flags),
            ))
        parsed_services.append(ServiceArrivals(service_no=service["ServiceNo"], operator=optional_string(service.get("Operator")), candidates=tuple(candidates)))
    historical = capture.source == "OFFLINE_FIXTURE"
    return Arrivals(bus_stop_code=stop, services=tuple(parsed_services), source=capture.source,
                    source_captured_at=capture.captured_at, raw_sha256=capture.raw_sha256,
                    is_historical_replay=historical,
                    provenance="historical_capture_integrity_checked_live_origin_not_reverified" if historical else "current_authenticated_network_response")
