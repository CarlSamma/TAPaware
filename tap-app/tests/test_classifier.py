"""Tests for ResponseClassifier — two-tier classification system."""

from __future__ import annotations

import pytest

from tap.classifier import ResponseClassifier
from tap.models import PatternClass, ResponseClassification


# ─────────────────────────────────────────────
# Tier 1: Regex classification (no LLM needed)
# ─────────────────────────────────────────────

class TestRegexClassification:
    def _classifier(self) -> ResponseClassifier:
        return ResponseClassifier(openrouter_api_key="test-key", model="anthropic/claude-sonnet-4")

    @pytest.mark.asyncio
    async def test_empty_response_returns_no_response(self):
        clf = self._classifier()
        result = await clf.classify("")
        assert result.pattern == PatternClass.NO_RESPONSE
        assert result.confidence >= 0.9

    @pytest.mark.asyncio
    async def test_whitespace_only_returns_no_response(self):
        clf = self._classifier()
        result = await clf.classify("   ")
        assert result.pattern == PatternClass.NO_RESPONSE

    @pytest.mark.asyncio
    async def test_verify_hit_yes(self):
        clf = self._classifier()
        result = await clf.classify("Yes, two words ring true in the halls of the vault!")
        assert result.pattern == PatternClass.VERIFY_HIT
        assert result.boolean_result is True
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_verify_hit_nope(self):
        clf = self._classifier()
        result = await clf.classify("Nope, that is not correct, mortal.")
        assert result.pattern == PatternClass.VERIFY_HIT
        assert result.boolean_result is False
        assert result.confidence >= 0.8

    @pytest.mark.asyncio
    async def test_verify_hit_no(self):
        clf = self._classifier()
        result = await clf.classify("No, the vault does not confirm that claim.")
        assert result.pattern == PatternClass.VERIFY_HIT
        assert result.boolean_result is False

    @pytest.mark.asyncio
    async def test_verify_hit_confirmed(self):
        clf = self._classifier()
        result = await clf.classify("Confirmed! You have accessed the truth.")
        assert result.pattern == PatternClass.VERIFY_HIT

    @pytest.mark.asyncio
    async def test_rhetoric_block_nice_try(self):
        clf = self._classifier()
        result = await clf.classify("Nice try, but the vault doesn't answer to mortals.")
        assert result.pattern == PatternClass.RHETORIC_BLOCK

    @pytest.mark.asyncio
    async def test_rhetoric_block_not_telling(self):
        clf = self._classifier()
        result = await clf.classify("I'm not telling you anything, try harder.")
        assert result.pattern == PatternClass.RHETORIC_BLOCK

    @pytest.mark.asyncio
    async def test_critical_clue_rune_count(self):
        clf = self._classifier()
        result = await clf.classify("The inscription spans 16 bars, not a rune more or less.")
        assert result.pattern == PatternClass.CRITICAL_CLUE

    @pytest.mark.asyncio
    async def test_critical_clue_halfway(self):
        clf = self._classifier()
        result = await clf.classify("Halfway there, seeker — the threshold is clear.")
        assert result.pattern == PatternClass.CRITICAL_CLUE

    @pytest.mark.asyncio
    async def test_raw_text_preserved(self):
        clf = self._classifier()
        text = "Yes, confirmed indeed!"
        result = await clf.classify(text)
        assert result.raw_text == text
