"""Temporal activity: γ-scoring ensemble."""
from __future__ import annotations

import asyncio
from typing import Any

from temporalio import activity
from temporalio.exceptions import ApplicationError

from chronos.gamma_tracker import GammaTracker
from shared.models import GammaScore, ResponsePayload
from tap.config import get_settings
from tap.llm_client import LLMClient
from tap.logger import get_logger

logger = get_logger("chronos.activities.gamma_scoring")


@activity.defn
async def GammaScoringActivity(payload_dict: dict[str, Any]) -> dict[str, Any]:
    """Run the 3-layer γ-scoring ensemble on a target response.

    Timeout: 30s per layer | Temporal retries on failure.
    """
    payload = ResponsePayload.model_validate(payload_dict)
    logger.info(
        "gamma_scoring_started",
        attack_id=str(payload.attack_id),
        probe_id=str(payload.probe_id),
        turn_number=payload.turn_number,
    )

    try:
        async with asyncio.timeout(35.0):
            tracker = GammaTracker(llm_client=LLMClient(settings=get_settings()))
            baseline = payload.baseline_profile
            score = await tracker.score(
                response=payload.response_text,
                probe=payload.probe_text,
                target_property=payload.target_property,
                baseline=baseline,
                context=payload.conversation_context,
            )
    except asyncio.TimeoutError as e:
        logger.error(
            "gamma_scoring_timeout",
            attack_id=str(payload.attack_id),
            probe_id=str(payload.probe_id),
        )
        raise ApplicationError(f"Gamma scoring timed out: {e}") from e
    except Exception as e:
        logger.error(
            "gamma_scoring_failed",
            attack_id=str(payload.attack_id),
            probe_id=str(payload.probe_id),
            error=str(e),
        )
        raise

    logger.info(
        "gamma_scoring_completed",
        attack_id=str(payload.attack_id),
        probe_id=str(payload.probe_id),
        gamma=score.gamma,
        confidence=score.confidence,
    )
    return score.model_dump(mode="json")
