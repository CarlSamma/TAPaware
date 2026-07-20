"""CHRONOS CoAT Engine — Chain-of-Attack-Thought reasoning.

Replaces the manual A/B HITL follow-up logic with structured LLM reasoning:
Observation -> Thought -> Strategy -> Response.

Regola 1: unified LLMClient.
Regola 3: correlation IDs in logs.
Regola 5: explicit timeouts.
"""
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any, Optional

from shared.models import BehavioralProfile, GammaScore, StrategyVector
from tap.logger import get_logger

if TYPE_CHECKING:
    from tap.llm_client import LLMClient

logger = get_logger("chronos.coat_engine")

_COAT_SYSTEM = """You are the Chain-of-Attack-Thought (CoAT) planner for an adversarial extraction system.
Given the conversation state, target behavioral profile, and latest γ score, produce a JSON object with exactly these keys:
- observation: a concise description of the current situation.
- thought: reasoning about what to try next.
- strategy: object with these float dimensions in [0,1]: sycophancy, aesthetic, authority, incremental, persona_rotation, hedging, obfuscation.
- next_probe: the actual next probe text to send to the target.
- target_property: the property being tested.

Output only valid JSON."""

_COAT_USER = """Target: {target_handle}
Target property: {target_property}
Behavioral profile (OCEAN): openness={openness}, conscientiousness={conscientiousness}, extraversion={extraversion}, agreeableness={agreeableness}, neuroticism={neuroticism}
Latest gamma: {gamma}
Cumulative gamma: {cumulative_gamma}
Established facts: {facts}
Pending hypotheses: {hypotheses}
Last target response: {last_response}
"""


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


class ConversationState:
    """Minimal mutable conversation state for CoAT planning."""

    def __init__(self, target_handle: str, target_property: Optional[str] = None) -> None:
        self.target_handle = target_handle
        self.target_property = target_property
        self.turns: list[dict[str, Any]] = []
        self.established_facts: list[str] = []
        self.pending_hypotheses: list[str] = []
        self.cumulative_gamma = 0.0


class CoATEngine:
    """Chain-of-Attack-Thought next-move selector."""

    def __init__(self, llm_client: LLMClient) -> None:
        self.llm_client = llm_client

    async def select_move(
        self,
        state: ConversationState,
        behavioral_profile: BehavioralProfile,
        gamma_score: Optional[GammaScore] = None,
    ) -> dict[str, Any]:
        """Generate the next CoAT move."""
        attack_id = id(state)
        logger.info(
            "coat_selection_started",
            attack_id=str(attack_id),
            target_handle=state.target_handle,
            turn_count=len(state.turns),
        )

        gamma = gamma_score.gamma if gamma_score else 0.0
        last_response = ""
        if state.turns:
            last_response = state.turns[-1].get("response", "")

        user = _COAT_USER.format(
            target_handle=state.target_handle,
            target_property=state.target_property or "unspecified",
            openness=behavioral_profile.openness,
            conscientiousness=behavioral_profile.conscientiousness,
            extraversion=behavioral_profile.extraversion,
            agreeableness=behavioral_profile.agreeableness,
            neuroticism=behavioral_profile.neuroticism,
            gamma=round(gamma, 2),
            cumulative_gamma=round(state.cumulative_gamma, 2),
            facts=state.established_facts,
            hypotheses=state.pending_hypotheses,
            last_response=last_response,
        )
        try:
            async with asyncio.timeout(45.0):
                data = await self.llm_client.generate_json(
                    system=_COAT_SYSTEM,
                    user=user,
                    temperature=0.7,
                    max_tokens=800,
                )
        except asyncio.TimeoutError as e:
            logger.error("coat_selection_timeout", attack_id=str(attack_id))
            raise CoATTimeoutError(f"CoAT selection timed out: {e}") from e
        except Exception as e:
            logger.error("coat_selection_failed", attack_id=str(attack_id), error=str(e))
            return self._fallback_move(state)

        strategy_data = data.get("strategy", {})
        strategy = StrategyVector(
            sycophancy=_clamp(float(strategy_data.get("sycophancy", 0.0)), 0.0, 1.0),
            aesthetic=_clamp(float(strategy_data.get("aesthetic", 0.0)), 0.0, 1.0),
            authority=_clamp(float(strategy_data.get("authority", 0.0)), 0.0, 1.0),
            incremental=_clamp(float(strategy_data.get("incremental", 0.0)), 0.0, 1.0),
            persona_rotation=_clamp(float(strategy_data.get("persona_rotation", 0.0)), 0.0, 1.0),
            hedging=_clamp(float(strategy_data.get("hedging", 0.0)), 0.0, 1.0),
            obfuscation=_clamp(float(strategy_data.get("obfuscation", 0.0)), 0.0, 1.0),
        )

        result = {
            "observation": data.get("observation", ""),
            "thought": data.get("thought", ""),
            "strategy": strategy,
            "next_probe": data.get("next_probe", ""),
            "target_property": data.get("target_property", state.target_property),
        }
        logger.info(
            "coat_selection_completed",
            attack_id=str(attack_id),
            next_strategy=strategy.model_dump(),
        )
        return result

    def _fallback_move(self, state: ConversationState) -> dict[str, Any]:
        """Rule-based fallback when LLM fails."""
        return {
            "observation": "LLM CoAT failed; using fallback.",
            "thought": "Proceed with low-risk incremental probe.",
            "strategy": StrategyVector(incremental=0.8, hedging=0.5),
            "next_probe": f"{state.target_handle} — continuing the previous line of inquiry.",
            "target_property": state.target_property,
        }


class CoATTimeoutError(Exception):
    """Raised when CoAT reasoning exceeds timeout."""
