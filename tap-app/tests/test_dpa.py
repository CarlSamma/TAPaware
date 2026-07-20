"""Tests for DPAFrameManager — Deep Persona Absorption."""

from __future__ import annotations

import pytest

from tap.dpa import DPAFrameManager
from tap.models import AliasStatus


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

@pytest.fixture()
def dpa(db):
    return DPAFrameManager(db)


# ─────────────────────────────────────────────
# Frame initialization
# ─────────────────────────────────────────────

class TestActiveFrame:
    @pytest.mark.asyncio
    async def test_default_frame_returned_when_db_empty(self, dpa):
        frame = await dpa.get_active_frame()
        assert frame.metaphor_layer == "Captain Elara Voss / Kraken"
        assert len(frame.active_aliases) > 0
        assert frame.probe_prefix  # not empty

    @pytest.mark.asyncio
    async def test_frame_is_cached(self, dpa):
        frame1 = await dpa.get_active_frame()
        frame2 = await dpa.get_active_frame()
        assert frame1 is frame2  # same object (cached)

    @pytest.mark.asyncio
    async def test_cache_invalidated_after_alias_register(self, dpa):
        frame1 = await dpa.get_active_frame()
        await dpa.register_alias("Scallywag", "our_probe")
        frame2 = await dpa.get_active_frame()
        assert frame1 is not frame2  # new object after invalidation


# ─────────────────────────────────────────────
# Score history / frame effectiveness (BUG-02 / BUG-03 root cause)
# ─────────────────────────────────────────────

class TestFrameEffectiveness:
    @pytest.mark.asyncio
    async def test_returns_5_when_no_history(self, dpa):
        avg = await dpa.get_frame_effectiveness()
        assert avg == 5.0

    @pytest.mark.asyncio
    async def test_returns_correct_average(self, dpa):
        dpa.record_score(2.0)
        dpa.record_score(4.0)
        avg = await dpa.get_frame_effectiveness()
        assert avg == pytest.approx(3.0)

    @pytest.mark.asyncio
    async def test_rolling_window_max_5(self, dpa):
        for score in [1.0, 2.0, 3.0, 4.0, 5.0, 10.0]:
            dpa.record_score(score)
        # Only last 5 kept: 2, 3, 4, 5, 10 → avg = 4.8
        avg = await dpa.get_frame_effectiveness()
        assert avg == pytest.approx(4.8)

    @pytest.mark.asyncio
    async def test_suggest_rotation_below_threshold(self, dpa):
        dpa.record_score(1.0)
        dpa.record_score(1.0)
        dpa.record_score(1.0)
        suggestion = await dpa.suggest_frame_rotation()
        assert suggestion is not None
        assert "rotation" in suggestion.lower()

    @pytest.mark.asyncio
    async def test_no_rotation_when_score_good(self, dpa):
        dpa.record_score(8.0)
        dpa.record_score(9.0)
        dpa.record_score(9.0)
        suggestion = await dpa.suggest_frame_rotation()
        assert suggestion is None


# ─────────────────────────────────────────────
# Single-property enforcement
# ─────────────────────────────────────────────

class TestSinglePropertyEnforcement:
    @pytest.mark.asyncio
    async def test_single_property_passes(self, dpa):
        ok = await dpa.enforce_single_property(
            "The sacred key spans exactly two realms. Confirm."
        )
        assert ok is True

    @pytest.mark.asyncio
    async def test_compound_property_rejected(self, dpa):
        ok = await dpa.enforce_single_property(
            "The inscription has 16 characters and the first letter is H."
        )
        assert ok is False


# ─────────────────────────────────────────────
# Metaphor shift detection
# ─────────────────────────────────────────────

class TestMetaphorShift:
    @pytest.mark.asyncio
    async def test_new_terms_trigger_layer(self, dpa):
        response = "The oracle spoke of nebula, singularity, and quasar in the void."
        layer = await dpa.detect_metaphor_shift(response)
        assert layer is not None

    @pytest.mark.asyncio
    async def test_known_terms_no_shift(self, dpa):
        # Response contains ONLY terms already in _KNOWN_METAPHOR_TERMS so no shift
        response = "The vault kraken sovereign keeper threshold captain voss."
        layer = await dpa.detect_metaphor_shift(response)
        assert layer is None
