"""Tests for CHRONOS γ-Tracker."""
from typing import Any

import pytest

from chronos.gamma_tracker import GammaTracker
from shared.models import BehavioralProfile


class FakeLLMClient:
    """Stub LLMClient returning deterministic JSON."""

    async def generate_json(self, **kwargs: Any) -> dict[str, Any]:
        return {
            "gamma": 6.0,
            "confidence": 0.8,
            "reasoning": "partial clue detected",
            "extracted_leaks": [
                {
                    "leak_type": "hint",
                    "content": "the first letter is H",
                    "target_property": "first_letter",
                    "confidence": 0.7,
                }
            ],
        }


@pytest.mark.asyncio
async def test_lexical_score_detects_yes() -> None:
    tracker = GammaTracker(llm_client=FakeLLMClient())  # type: ignore[arg-type]
    score = await tracker.score(
        response="Yes, that is correct.",
        probe="test",
        target_property="word_count",
    )
    assert score.gamma > 0.0
    assert score.breakdown["lexical"] > 0.0


@pytest.mark.asyncio
async def test_behavioral_profile_adjustment() -> None:
    tracker = GammaTracker(llm_client=FakeLLMClient())  # type: ignore[arg-type]
    profile = BehavioralProfile(agreeableness=9.0)
    score = await tracker.score(
        response="a" * 200,
        probe="test",
        target_property=None,
        baseline=profile,
    )
    assert score.gamma >= 0.0
    assert score.confidence > 0.0
