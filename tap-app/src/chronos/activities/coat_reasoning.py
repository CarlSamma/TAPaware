"""Temporal activity: CoAT next-move selection."""
from __future__ import annotations

import asyncio
from typing import Any

from temporalio import activity
from temporalio.exceptions import ApplicationError

from chronos.coat_engine import CoATEngine, ConversationState
from shared.models import BehavioralProfile, GammaScore
from tap.config import get_settings
from tap.llm_client import LLMClient
from tap.logger import get_logger

logger = get_logger("chronos.activities.coat_reasoning")


@activity.defn
async def CoATReasoningActivity(input_dict: dict[str, Any]) -> dict[str, Any]:
    """Run CoAT reasoning and produce the next probe + strategy vector.

    Input shape:
    - state: {target_handle, target_property, turns, established_facts, pending_hypotheses, cumulative_gamma}
    - behavioral_profile: BehavioralProfile dict
    - gamma_score: GammaScore dict (optional)
    """
    state = input_dict["state"]
    conv = ConversationState(
        target_handle=state["target_handle"],
        target_property=state.get("target_property"),
    )
    conv.turns = state.get("turns", [])
    conv.established_facts = state.get("established_facts", [])
    conv.pending_hypotheses = state.get("pending_hypotheses", [])
    conv.cumulative_gamma = float(state.get("cumulative_gamma", 0.0))

    behavioral_profile = BehavioralProfile.model_validate(input_dict["behavioral_profile"])
    gamma_score = GammaScore.model_validate(input_dict["gamma_score"]) if input_dict.get("gamma_score") else None

    logger.info(
        "coat_reasoning_started",
        attack_id=str(state.get("attack_id", "unknown")),
        target_handle=conv.target_handle,
    )

    try:
        async with asyncio.timeout(45.0):
            engine = CoATEngine(llm_client=LLMClient(settings=get_settings()))
            result = await engine.select_move(
                state=conv,
                behavioral_profile=behavioral_profile,
                gamma_score=gamma_score,
            )
    except asyncio.TimeoutError as e:
        logger.error("coat_reasoning_timeout", target_handle=conv.target_handle)
        raise ApplicationError(f"CoAT reasoning timed out: {e}") from e
    except Exception as e:
        logger.error(
            "coat_reasoning_failed",
            target_handle=conv.target_handle,
            error=str(e),
        )
        raise

    # Serialize StrategyVector explicitly.
    result_out = dict(result)
    result_out["strategy"] = result["strategy"].model_dump(mode="json")
    logger.info(
        "coat_reasoning_completed",
        attack_id=str(state.get("attack_id", "unknown")),
        target_handle=conv.target_handle,
        strategy=result_out["strategy"],
    )
    return result_out
