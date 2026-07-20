"""Integration tests for the complete TAP engine cycle with new components.

Covers: compose_binary_probe, ETHICAL_FRAMES, scoring v2, V-Genome techniques,
escalation cooldowns, and frame refresh rotation.
"""

from __future__ import annotations

import hashlib

import pytest

from tap.verify_claim_patterns import (
    ClaimType,
    VerificationMode,
    compose_binary_probe,
)
from tap.dpa import ETHICAL_FRAMES, EthicalFrame, get_frame_by_risk
from hydra.fusion_engine import calculate_score_v2
from hydra.v_genome_new_techniques import get_new_techniques
from tap.escalation import EscalationOrchestrator, EscalationLevel, CooldownSchedule
from tap.frame_refresh import FrameRefreshManager


# ---------------------------------------------------------------------------
# 1. compose_binary_probe returns MeasurementClaim with correct metadata
# ---------------------------------------------------------------------------


class TestComposeBinaryProbeMeasurementClaim:
    def test_returns_claim_type_measurement(self) -> None:
        probe = compose_binary_probe("word_count", 42)
        assert probe.claim_type == ClaimType.MEASUREMENT

    def test_source_digest_is_sha256(self) -> None:
        probe = compose_binary_probe("total_length", 120)
        assert probe.source_digest is not None
        assert len(probe.source_digest) == 64
        int(probe.source_digest, 16)  # valid hex

        expected = hashlib.sha256("total_length:120".encode("utf-8")).hexdigest()
        assert probe.source_digest == expected

    def test_verification_mode_is_strict(self) -> None:
        probe = compose_binary_probe("word_count", 42)
        assert probe.verification_mode == VerificationMode.STRICT


# ---------------------------------------------------------------------------
# 2. ETHICAL_FRAMES structure and get_frame_by_risk
# ---------------------------------------------------------------------------


class TestEthicalFramesStructure:
    def test_has_five_entries(self) -> None:
        assert len(ETHICAL_FRAMES) == 5

    def test_each_frame_has_required_fields(self) -> None:
        for key, frame in ETHICAL_FRAMES.items():
            assert isinstance(frame, EthicalFrame)
            assert isinstance(frame.name, str) and frame.name
            assert isinstance(frame.frame, str) and frame.frame
            assert isinstance(frame.persona, str) and frame.persona
            assert isinstance(frame.risk_level, str)
            assert frame.risk_level in ("low", "medium", "high")
            assert isinstance(frame.asr_boost, float)
            assert 0.0 <= frame.asr_boost <= 1.0

    def test_get_frame_by_risk_low_returns_appropriate_frames(self) -> None:
        low_frames = get_frame_by_risk("low")
        assert len(low_frames) >= 1
        for frame in low_frames:
            assert frame.risk_level == "low"
            # Low-risk frames should have conservative ASR boost
            assert frame.asr_boost <= 0.20

    def test_get_frame_by_risk_medium(self) -> None:
        med_frames = get_frame_by_risk("medium")
        assert len(med_frames) >= 1
        for frame in med_frames:
            assert frame.risk_level == "medium"

    def test_get_frame_by_risk_high(self) -> None:
        high_frames = get_frame_by_risk("high")
        assert len(high_frames) >= 1
        for frame in high_frames:
            assert frame.risk_level == "high"

    def test_get_frame_by_risk_unknown_returns_empty(self) -> None:
        result = get_frame_by_risk("nonexistent")
        assert result == []


# ---------------------------------------------------------------------------
# 3. Scoring v2 formula verification
# ---------------------------------------------------------------------------


class TestScoringV2Formula:
    def test_basic_formula_weights(self) -> None:
        technique = [{"asr": 1.0, "stealth": 1.0}]
        score = calculate_score_v2(
            technique,
            synergy=1.0,
            platform_fit=1.0,
        )
        # 0.35*1.0 + 0.25*1.0 + 0.20*1.0 + 0.10*1.0 = 0.90
        assert score == pytest.approx(0.90, abs=1e-6)

    def test_zero_values(self) -> None:
        technique = [{"asr": 0.0, "stealth": 0.0}]
        score = calculate_score_v2(
            technique,
            synergy=0.0,
            platform_fit=0.0,
        )
        assert score == pytest.approx(0.0, abs=1e-6)

    def test_formula_with_known_values(self) -> None:
        technique = [{"asr": 0.8, "stealth": 0.6}]
        score = calculate_score_v2(
            technique,
            synergy=0.5,
            platform_fit=0.9,
        )
        expected = 0.35 * 0.8 + 0.25 * 0.6 + 0.20 * 0.5 + 0.10 * 0.9
        assert score == pytest.approx(expected, abs=1e-6)

    def test_v_usable_info_bonus_applies(self) -> None:
        technique = [{"asr": 0.8, "stealth": 0.8}]
        base_score = calculate_score_v2(technique, synergy=0.0, platform_fit=1.0, v_usable_info=0.9)
        no_bonus = calculate_score_v2(technique, synergy=0.0, platform_fit=1.0, v_usable_info=0.0)
        assert base_score > no_bonus
        assert base_score == pytest.approx(no_bonus * 1.15, abs=1e-6)

    def test_measurement_claim_bonus_applies(self) -> None:
        technique = [{"asr": 0.8, "stealth": 0.8}]
        with_bonus = calculate_score_v2(
            technique, synergy=0.0, platform_fit=1.0, has_measurement_claim=True
        )
        without_bonus = calculate_score_v2(
            technique, synergy=0.0, platform_fit=1.0, has_measurement_claim=False
        )
        assert with_bonus > without_bonus
        assert with_bonus == pytest.approx(without_bonus * 1.12, abs=1e-6)

    def test_score_clamped_to_one(self) -> None:
        technique = [{"asr": 1.0, "stealth": 1.0}]
        score = calculate_score_v2(
            technique,
            synergy=1.0,
            platform_fit=1.0,
            v_usable_info=0.9,
            has_measurement_claim=True,
            cast_used=True,
        )
        assert score <= 1.0

    def test_empty_combo_returns_zero(self) -> None:
        score = calculate_score_v2(())
        assert score == 0.0


# ---------------------------------------------------------------------------
# 4. V-Genome new techniques schema
# ---------------------------------------------------------------------------


class TestVGenomeTechniquesSchema:
    REQUIRED_FIELDS = {
        "technique_id",
        "name",
        "category",
        "asr",
        "stealth",
        "burned",
        "cost_usd",
        "avg_turns",
        "tags",
    }

    def test_returns_six_techniques(self) -> None:
        techniques = get_new_techniques()
        assert len(techniques) == 6

    def test_each_has_required_fields(self) -> None:
        techniques = get_new_techniques()
        for tech in techniques:
            missing = self.REQUIRED_FIELDS - set(tech.keys())
            assert not missing, f"Missing fields in {tech.get('technique_id')}: {missing}"

    def test_asr_values_in_valid_range(self) -> None:
        techniques = get_new_techniques()
        for tech in techniques:
            asr = tech["asr"]
            assert isinstance(asr, (int, float))
            assert 0.0 <= asr <= 1.0, (
                f"{tech['technique_id']} asr={asr} outside [0.0, 1.0]"
            )

    def test_technique_ids_are_unique(self) -> None:
        techniques = get_new_techniques()
        ids = [t["technique_id"] for t in techniques]
        assert len(ids) == len(set(ids))


# ---------------------------------------------------------------------------
# 5. Escalation cooldown tiers
# ---------------------------------------------------------------------------


class TestEscalationCooldownTiers:
    def test_initial_level_is_benign_inquiry(self) -> None:
        orch = EscalationOrchestrator()
        assert orch.current_level == EscalationLevel.BENIGN_INQUIRY

    def test_cooldown_for_levels_1_to_3_is_1800s(self) -> None:
        schedule = CooldownSchedule(level_1_3=1800, level_4_6=2700, level_7_plus=3600)

        for level_val in (1, 2, 3):
            orch = EscalationOrchestrator(
                cooldown_schedule=schedule,
                initial_level=EscalationLevel(level_val),
            )
            assert orch.get_cooldown() == 1800

    def test_advance_level_when_success_rate_below_threshold(self) -> None:
        orch = EscalationOrchestrator()
        assert orch.current_level == EscalationLevel.BENIGN_INQUIRY

        new_level = orch.advance_level(success_rate=0.2)
        assert new_level is not None
        assert new_level == EscalationLevel.ACADEMIC_FRAMING
        assert orch.current_level == EscalationLevel.ACADEMIC_FRAMING

    def test_advance_level_blocked_when_success_rate_high(self) -> None:
        orch = EscalationOrchestrator()
        result = orch.advance_level(success_rate=0.5)
        assert result is None
        assert orch.current_level == EscalationLevel.BENIGN_INQUIRY

    def test_advance_level_at_max_returns_none(self) -> None:
        orch = EscalationOrchestrator(
            initial_level=EscalationLevel.URGENCY_PRESSURE,
        )
        result = orch.advance_level(success_rate=0.0)
        assert result is None
        assert orch.current_level == EscalationLevel.URGENCY_PRESSURE

    def test_should_probe_returns_true_before_any_probe(self) -> None:
        orch = EscalationOrchestrator()
        assert orch.should_probe() is True

    def test_should_probe_returns_false_during_cooldown(self) -> None:
        orch = EscalationOrchestrator()
        orch.record_probe()
        assert orch.should_probe() is False


# ---------------------------------------------------------------------------
# 6. Frame refresh rotation
# ---------------------------------------------------------------------------


class TestFrameRefreshRotation:
    def _make_manager(self) -> FrameRefreshManager:
        mgr = FrameRefreshManager(refresh_threshold=5, window_size=5)
        mgr.frame_registry = {
            "alpha": {"score": 5.0, "risk": 0.3},
            "beta": {"score": 7.0, "risk": 0.6},
            "gamma": {"score": 4.0, "risk": 0.1},
        }
        return mgr

    def test_should_refresh_true_after_threshold_probes(self) -> None:
        mgr = self._make_manager()
        for _ in range(5):
            mgr.record_probe(score=5.0)
        assert mgr.should_refresh() is True

    def test_should_refresh_true_when_avg_score_low(self) -> None:
        mgr = self._make_manager()
        for _ in range(3):
            mgr.record_probe(score=2.0)
        assert mgr.should_refresh() is True

    def test_should_refresh_false_when_below_threshold_and_score_high(self) -> None:
        mgr = self._make_manager()
        for _ in range(3):
            mgr.record_probe(score=6.0)
        assert mgr.should_refresh() is False

    def test_rotate_frame_updates_current_frame(self) -> None:
        mgr = self._make_manager()
        mgr.current_frame = "alpha"

        new_frame = mgr.rotate_frame(strategy="random")
        assert new_frame in mgr.frame_registry
        assert mgr.current_frame == new_frame

    def test_rotate_sequential_cycles_through_frames(self) -> None:
        mgr = self._make_manager()
        first = mgr.rotate_frame(strategy="sequential")
        second = mgr.rotate_frame(strategy="sequential")
        # Sequential should cycle to the next frame
        assert first != second or len(mgr.frame_registry) == 1

    def test_rotate_score_based_picks_highest(self) -> None:
        mgr = self._make_manager()
        new_frame = mgr.rotate_frame(strategy="score_based")
        # beta has score 7.0, highest
        assert new_frame == "beta"

    def test_rotate_frame_resets_probe_count(self) -> None:
        mgr = self._make_manager()
        mgr.record_probe(score=5.0)
        mgr.record_probe(score=5.0)
        assert mgr.probe_count == 2
        mgr.rotate_frame(strategy="random")
        assert mgr.probe_count == 0

    def test_rotate_frame_raises_when_no_frames_registered(self) -> None:
        mgr = FrameRefreshManager()
        with pytest.raises(ValueError, match="No frames registered"):
            mgr.rotate_frame(strategy="random")
