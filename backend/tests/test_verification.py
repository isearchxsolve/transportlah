"""[TEST VECTOR] Generated evidence tests policy, never real passenger proof."""

from dataclasses import replace
from decimal import Decimal
import unittest

from backend.app.verification import Evidence, Factor, Observation, State, decide, contest_eligible


def vector(**changes):
    factors = {factor: Observation(State.PASSED, Decimal("1")) for factor in Factor}
    return Evidence(factors=factors, provenance="TEST_VECTOR", **changes)


class VerificationPolicyChecks(unittest.TestCase):
    def test_full_generated_bus_evidence_is_tier_two_but_explicitly_test_only(self):
        decision = decide(vector())
        self.assertEqual(decision.raw_score, Decimal("100.00"))
        self.assertEqual(decision.score, Decimal("100.00"))
        self.assertEqual(decision.status, "verified")
        self.assertEqual(decision.tier, 2)
        self.assertTrue(decision.test_only)
        self.assertEqual(decision.reward_percent, 100)

    def test_missing_transit_context_never_renormalizes_other_weights(self):
        packet = vector()
        packet.factors[Factor.TRANSIT_CONTEXT] = Observation(State.UNAVAILABLE)
        decision = decide(packet)
        self.assertEqual(decision.raw_score, Decimal("80.00"))
        self.assertEqual(decision.score, Decimal("79.00"))
        self.assertEqual(decision.status, "probable")
        self.assertEqual(decision.tier, 1)
        self.assertFalse(decision.leaderboard_eligible)
        self.assertEqual(decision.reward_percent, 50)

    def test_rounded_79_point_995_does_not_cross_class_boundary(self):
        packet = vector()
        packet.factors[Factor.TRANSIT_CONTEXT] = Observation(State.PASSED, Decimal("0.00025"))
        packet.factors[Factor.SPEED] = Observation(State.PASSED, Decimal("0.999"))
        decision = decide(packet)
        self.assertEqual(decision.status, "probable")
        self.assertLess(decision.score, Decimal(80))

    def test_contradicted_service_or_direction_is_rejected_even_with_high_score(self):
        for factor in (Factor.SERVICE, Factor.PROGRESSION):
            packet = vector()
            packet.factors[factor] = Observation(State.FAILED)
            result = decide(packet)
            self.assertEqual(result.status, "rejected")
            self.assertEqual(result.score, 0)
            self.assertEqual(result.reward_percent, 0)

    def test_single_ping_and_inactive_lifecycle_are_hard_rejections(self):
        for packet in (vector(unique_pings=1), vector(lifecycle_valid=False), vector(duration_seconds=0)):
            self.assertEqual(decide(packet).status, "rejected")

    def test_high_score_without_validated_corridor_cannot_be_verified(self):
        packet = vector()
        packet.factors[Factor.CORRIDOR] = Observation(State.UNAVAILABLE)
        result = decide(packet)
        self.assertEqual(result.raw_score, 90)
        self.assertEqual(result.status, "probable")
        self.assertEqual(result.tier, 1)

    def test_device_integrity_alone_is_not_an_onboard_proof(self):
        self.assertEqual(decide(vector(device_integrity=True)).tier, 2)
        self.assertEqual(decide(vector(trusted_boarding=True)).tier, 2)
        self.assertEqual(decide(vector(device_integrity=True, trusted_boarding=True)).tier, 3)

    def test_contests_enforce_mode_and_tier_and_disable_test_vectors_in_production(self):
        packet = vector()
        decision = decide(packet)
        self.assertFalse(contest_eligible(decision, required_tier=2, allowed_modes={"bus"}))
        self.assertTrue(contest_eligible(decision, required_tier=2, allowed_modes={"bus"}, test_environment=True))
        self.assertFalse(contest_eligible(decision, required_tier=3, allowed_modes={"bus"}, test_environment=True))
        self.assertFalse(contest_eligible(decision, required_tier=2, allowed_modes={"rail"}, test_environment=True))

    def test_rail_is_probable_until_a_validated_rail_adapter_exists(self):
        result = decide(vector(mode="rail"))
        self.assertEqual(result.status, "probable")
        self.assertEqual(result.tier, 1)
        self.assertFalse(result.leaderboard_eligible)

    def test_manual_claim_is_tier_zero_without_points(self):
        result = decide(vector(unique_pings=0))
        self.assertEqual(result.tier, 0)
        self.assertEqual(result.reward_percent, 0)

    def test_invalid_and_incomplete_internal_evidence_is_not_accepted(self):
        for value in (Decimal("NaN"), Decimal("Infinity"), Decimal("-0.1"), Decimal("1.1")):
            with self.assertRaises(ValueError):
                Observation(State.PASSED, value)
        with self.assertRaises(ValueError):
            Observation(State.UNAVAILABLE, Decimal(1))
        packet = vector()
        del packet.factors[Factor.TRANSIT_CONTEXT]
        with self.assertRaises(ValueError):
            decide(packet)

    def test_origin_is_mandatory_and_not_an_open_ended_string(self):
        with self.assertRaises(ValueError):
            decide(replace(vector(), provenance="UNLABELLED"))
