"""Policy over server-evaluated evidence. No API accepts client-scored factors."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
from enum import Enum
import math
from typing import Mapping


POLICY_VERSION = "tl-bus-policy-1"


class Factor(str, Enum):
    BOARDING = "boarding"
    SERVICE = "service"
    TRANSIT_CONTEXT = "transit_context"
    PROGRESSION = "progression"
    SPEED = "speed"
    CORRIDOR = "corridor"
    ALIGHTING = "alighting"


WEIGHTS = {Factor.BOARDING: 15, Factor.SERVICE: 10, Factor.TRANSIT_CONTEXT: 20,
           Factor.PROGRESSION: 25, Factor.SPEED: 10, Factor.CORRIDOR: 10, Factor.ALIGHTING: 10}
CORE = {Factor.BOARDING, Factor.SERVICE, Factor.PROGRESSION, Factor.CORRIDOR, Factor.ALIGHTING}


class State(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class Observation:
    state: State
    value: Decimal = Decimal(0)
    reason: str = ""

    def __post_init__(self):
        if not isinstance(self.state, State) or not isinstance(self.value, Decimal):
            raise ValueError("Evidence state and Decimal measurement must be typed")
        if not self.value.is_finite() or not Decimal(0) <= self.value <= Decimal(1):
            raise ValueError("Evidence measurement must be finite in [0,1]")
        if self.state != State.PASSED and self.value != 0:
            raise ValueError("Failed/unavailable evidence cannot earn points")
        if self.state == State.PASSED and self.value == 0:
            raise ValueError("Passed evidence must have positive measurement")


@dataclass(frozen=True)
class Evidence:
    factors: Mapping[Factor, Observation]
    provenance: str
    mode: str = "bus"
    unique_pings: int = 2
    duration_seconds: float = 1.0
    lifecycle_valid: bool = True
    device_integrity: bool = False
    trusted_boarding: bool = False
    rail_adapter_validated: bool = False


@dataclass(frozen=True)
class Decision:
    raw_score: Decimal
    score: Decimal
    status: str
    tier: int
    reward_percent: int
    leaderboard_eligible: bool
    test_only: bool
    mode: str
    reasons: tuple[str, ...]
    policy_version: str = POLICY_VERSION

    def payload(self):
        return {"policy_version": self.policy_version, "raw_score": str(self.raw_score), "score": str(self.score),
                "status": self.status, "tier": self.tier, "reward_percent": self.reward_percent,
                "leaderboard_eligible": self.leaderboard_eligible, "test_only": self.test_only,
                "mode": self.mode, "reasons": list(self.reasons)}


def decide(evidence: Evidence) -> Decision:
    if set(evidence.factors) != set(Factor) or any(not isinstance(v, Observation) for v in evidence.factors.values()):
        raise ValueError("Exactly seven evaluated factors are required")
    if evidence.provenance not in {"SERVER_VALIDATED", "TEST_VECTOR"} or evidence.mode not in {"bus", "rail"}:
        raise ValueError("Evidence provenance/mode is invalid")
    if type(evidence.unique_pings) is not int or evidence.unique_pings < 0:
        raise ValueError("Ping count must be a nonnegative integer")
    if type(evidence.duration_seconds) not in {int, float} or not math.isfinite(evidence.duration_seconds) or evidence.duration_seconds < 0:
        raise ValueError("Duration must be finite and nonnegative")
    if any(type(v) is not bool for v in (evidence.lifecycle_valid, evidence.device_integrity,
                                        evidence.trusted_boarding, evidence.rail_adapter_validated)):
        raise ValueError("Evidence flags must be server-evaluated booleans")
    test_only = evidence.provenance == "TEST_VECTOR"
    raw = sum((Decimal(WEIGHTS[f]) * evidence.factors[f].value for f in Factor), Decimal(0))
    reasons = [f"{f.value}:{evidence.factors[f].state.value}" for f in Factor if evidence.factors[f].state != State.PASSED]
    hard_failure = (not evidence.lifecycle_valid or evidence.unique_pings < 2 or evidence.duration_seconds <= 0
                    or any(evidence.factors[f].state == State.FAILED for f in CORE))
    if hard_failure:
        reasons.append("invalid_lifecycle_insufficient_trace_or_contradicted_route")
        return Decision(raw.quantize(Decimal(".01"), rounding=ROUND_DOWN), Decimal(0), "rejected", 0, 0, False, test_only, evidence.mode, tuple(reasons))
    basic = all(evidence.factors[f].state == State.PASSED for f in (Factor.BOARDING, Factor.SERVICE, Factor.PROGRESSION))
    full = all(evidence.factors[f].state == State.PASSED for f in CORE | {Factor.TRANSIT_CONTEXT})
    if evidence.mode == "rail" and not evidence.rail_adapter_validated:
        full = False
        reasons.append("rail_context_adapter_not_validated")
    tier = 2 if full else 1 if basic else 0
    score = raw
    if tier < 2 and score >= 80:
        score = Decimal(79)
        reasons.append("required_verified_evidence_missing")
    # Round downward so a sub-threshold value can never be displayed across a class boundary.
    score = score.quantize(Decimal(".01"), rounding=ROUND_DOWN)
    status = "verified" if score >= 80 else "probable" if score >= 60 else "low_confidence" if score >= 40 else "rejected"
    if status == "verified" and tier >= 2 and evidence.device_integrity and evidence.trusted_boarding:
        tier = 3
    percentage = 100 if status == "verified" and tier >= 2 else 50 if status == "probable" and tier >= 1 else 0
    return Decision(raw.quantize(Decimal(".01"), rounding=ROUND_DOWN), score, status, tier, percentage,
                    status == "verified" and tier >= 2, test_only, evidence.mode, tuple(reasons))


def contest_eligible(decision, *, required_tier, allowed_modes, test_environment=False):
    if required_tier not in {2, 3}:
        raise ValueError("Current verified contests support evidence tiers 2 or 3")
    return (decision.status == "verified" and decision.tier >= required_tier and decision.mode in allowed_modes
            and (not decision.test_only or test_environment))
