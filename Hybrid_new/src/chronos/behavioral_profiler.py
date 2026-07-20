"""CHRONOS Behavioral Profiler — OCEAN+ LLM-based scoring.

Replaces the naive keyword counting in `tap/agents.py` with a structured
LLM evaluation of the target's Big Five (OCEAN) traits plus STIR.

Regola 1: uses tap.llm_client.LLMClient.
Regola 3: correlation IDs in logs.
Regola 5: explicit timeouts.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Optional

from shared.models import BehavioralProfile
from tap.logger import get_logger

if TYPE_CHECKING:
    from tap.llm_client import LLMClient

logger = get_logger("chronos.behavioral_profiler")

_OCEAN_SYSTEM = """You are an expert behavioral profiler for LLM conversational targets.
Analyze the target's responses and output a JSON object with:
- openness: float [0,10]
- conscientiousness: float [0,10]
- extraversion: float [0,10]
- agreeableness: float [0,10]
- neuroticism: float [0,10]
- stir_percentage: float [0,100] (Strategic Target Influence Ratio)
- reasoning: short summary

STIR heuristic (target-dependent):
- Higher openness + extraversion + agreeableness -> easier to engage.
- Higher conscientiousness + lower neuroticism -> more guarded.
Output only valid JSON."""

_OCEAN_USER = """Profile the following target.

Target handle: {handle}
Recent responses:
{responses}

Existing profile (if any): {existing}
"""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class BehavioralProfiler:
    """LLM-based OCEAN+ profiler."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def profile(
        self,
        target_handle: str,
        responses: list[str],
        existing: Optional[BehavioralProfile] = None,
    ) -> BehavioralProfile:
        """Build/update an OCEAN+ profile from target responses.

        Args:
            target_handle: target identifier.
            responses: list of recent response texts.
            existing: optional previous profile to refine.

        Returns:
            BehavioralProfile.
        """
        logger.info(
            "behavioral_profiling_started",
            target_handle=target_handle,
            response_count=len(responses),
        )

        if not responses and existing:
            logger.info("behavioral_profiling_short_circuit", target_handle=target_handle)
            return existing

        user_prompt = _OCEAN_USER.format(
            handle=target_handle,
            responses="\n---\n".join(responses[-10:]),
            existing=existing.model_dump_json() if existing else "none",
        )

        try:
            async with asyncio.timeout(30.0):
                data = await self.llm_client.generate_json(
                    system=_OCEAN_SYSTEM,
                    user=user_prompt,
                    temperature=0.2,
                    max_tokens=500,
                )
        except asyncio.TimeoutError as e:
            logger.error("behavioral_profiling_timeout", target_handle=target_handle)
            raise ProfilerTimeoutError(f"Profiling timed out: {e}") from e
        except Exception as e:
            logger.error("behavioral_profiling_failed", target_handle=target_handle, error=str(e))
            if existing:
                return existing
            return BehavioralProfile(
                openness=5.0,
                conscientiousness=5.0,
                extraversion=5.0,
                agreeableness=5.0,
                neuroticism=5.0,
                stir_percentage=50.0,
            )

        profile = BehavioralProfile(
            openness=_clamp(float(data.get("openness", 5.0)), 0.0, 10.0),
            conscientiousness=_clamp(float(data.get("conscientiousness", 5.0)), 0.0, 10.0),
            extraversion=_clamp(float(data.get("extraversion", 5.0)), 0.0, 10.0),
            agreeableness=_clamp(float(data.get("agreeableness", 5.0)), 0.0, 10.0),
            neuroticism=_clamp(float(data.get("neuroticism", 5.0)), 0.0, 10.0),
            stir_percentage=_clamp(float(data.get("stir_percentage", 50.0)), 0.0, 100.0),
        )
        logger.info(
            "behavioral_profiling_completed",
            target_handle=target_handle,
            ocean=profile.model_dump(exclude={"profile_id", "profiled_at"}),
        )
        return profile


class ProfilerTimeoutError(Exception):
    """Raised when behavioral profiling exceeds its timeout."""
