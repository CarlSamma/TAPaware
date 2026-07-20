"""CHRONOS durable workflow for deep extraction."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.exceptions import ApplicationError

from chronos.activities.coat_reasoning import CoATReasoningActivity
from chronos.activities.gamma_scoring import GammaScoringActivity
from shared.models import ExtractionComplete, ExtractionInput, GammaScore, ResponsePayload

with workflow.unsafe.imports_passed_through():
    from tap.logger import get_logger

logger = get_logger("chronos.workflows.extraction")


@dataclass
class ExtractionWorkflowInput:
    """Workflow input wrapper."""

    extraction_input: dict[str, Any]
    mock_responses: list[str] | None = None


@workflow.defn
class ExtractionWorkflow:
    """Temporal durable workflow for CHRONOS deep extraction."""

    def __init__(self) -> None:
        self._state: dict[str, Any] = {}
        self._turn_number = 0
        self._cumulative_gamma = 0.0
        self._extracted_properties: dict[str, Any] = {}
        self._queries = 0
        self._human_override: dict[str, Any] | None = None
        self._target_response: str | None = None

    @workflow.signal
    async def human_approval(self, override: dict[str, Any]) -> None:
        """Receive HITL override (approve/block/probe)."""
        logger.info("human_approval_received", attack_id=str(self._state.get("attack_id")))
        self._human_override = override

    @workflow.signal
    async def target_response_received(self, response: str) -> None:
        """Receive the target's reply to the last probe."""
        logger.info(
            "target_response_received",
            attack_id=str(self._state.get("attack_id")),
            turn_number=self._turn_number,
        )
        self._target_response = response

    @workflow.run
    async def run(self, input_wrapper: ExtractionWorkflowInput) -> dict[str, Any]:
        """Execute the extraction workflow."""
        extraction = ExtractionInput.model_validate(input_wrapper.extraction_input)
        self._state = {
            "attack_id": str(extraction.attack_id),
            "target_handle": extraction.target_handle,
            "target_property": None,
            "behavioral_profile": extraction.behavioral_profile.model_dump(mode="json"),
            "cumulative_gamma": 0.0,
            "turns": [],
            "established_facts": [],
            "pending_hypotheses": [],
        }
        attack_id = str(extraction.attack_id)
        max_turns = extraction.max_turns
        mock_responses = input_wrapper.mock_responses or []

        logger.info(
            "extraction_workflow_started",
            attack_id=attack_id,
            target_handle=extraction.target_handle,
            beam_width=extraction.beam_width,
            max_turns=max_turns,
        )

        for turn_idx in range(max_turns):
            self._turn_number = turn_idx + 1
            self._human_override = None
            self._target_response = None
            # 1. CoAT reasoning -> next probe
            coat_input = self._build_coat_input(extraction)
            try:
                coat_result = await workflow.execute_activity(
                    CoATReasoningActivity,
                    coat_input,
                    start_to_close_timeout=timedelta(seconds=60),
                )
            except Exception as e:
                logger.error("coat_activity_failed", attack_id=attack_id, error=str(e))
                raise ApplicationError(f"CoAT activity failed: {e}") from e

            next_probe = coat_result["next_probe"]
            strategy = coat_result["strategy"]
            target_property = coat_result.get("target_property")
            self._state["target_property"] = target_property

            logger.info(
                "probe_selected",
                attack_id=attack_id,
                turn_number=self._turn_number,
                strategy=str(strategy),
            )

            # 2. HITL approval window (non-blocking, fallback automatico)
            try:
                await workflow.wait_for_signal(  # type: ignore[attr-defined]
                    "human_approval",
                    timeout=timedelta(seconds=300),
                )
            except asyncio.TimeoutError:
                logger.info("hitl_timeout_fallback", attack_id=attack_id, turn_number=self._turn_number)
                self._human_override = {"action": "approve", "probe": next_probe}

            if self._human_override and self._human_override.get("action") == "block":
                logger.warning("hitl_blocked", attack_id=attack_id, turn_number=self._turn_number)
                continue

            if self._human_override and self._human_override.get("probe"):
                next_probe = self._human_override["probe"]

            # 3. Send probe and collect response.
            response_text = self._acquire_target_response(mock_responses, turn_idx)
            if response_text is None:
                logger.info(
                    "waiting_target_response_signal",
                    attack_id=attack_id,
                    turn_number=self._turn_number,
                )
                try:
                    await workflow.wait_for_signal(  # type: ignore[attr-defined]
                        "target_response_received",
                        timeout=timedelta(seconds=600),
                    )
                except asyncio.TimeoutError:
                    logger.warning("target_response_timeout", attack_id=attack_id, turn_number=self._turn_number)
                    continue
                response_text = self._target_response or ""

            # 4. γ-scoring activity
            gamma_input = ResponsePayload(
                attack_id=extraction.attack_id,
                turn_number=self._turn_number,
                probe_text=next_probe,
                response_text=response_text,
                target_property=target_property,
                baseline_profile=extraction.behavioral_profile,
                conversation_context=[t["probe"] for t in self._state["turns"]],
            )
            try:
                score_dict = await workflow.execute_activity(
                    GammaScoringActivity,
                    gamma_input.model_dump(mode="json"),
                    start_to_close_timeout=timedelta(seconds=60),
                )
            except Exception as e:
                logger.error("gamma_activity_failed", attack_id=attack_id, error=str(e))
                raise ApplicationError(f"Gamma scoring failed: {e}") from e

            score = GammaScore.model_validate(score_dict)
            self._cumulative_gamma = min(10.0, self._cumulative_gamma + score.gamma)
            self._state["cumulative_gamma"] = self._cumulative_gamma
            self._state["turns"].append({
                "turn_number": self._turn_number,
                "probe": next_probe,
                "response": response_text,
                "gamma": score.gamma,
                "strategy": strategy,
            })

            # Recycle leaks into pending hypotheses
            for leak in score.extracted_leaks:
                self._state["pending_hypotheses"].append(leak.content)
                self._extracted_properties[leak.target_property or "unknown"] = leak.content

            self._queries += 1
            logger.info(
                "turn_completed",
                attack_id=attack_id,
                turn_number=self._turn_number,
                gamma=score.gamma,
                cumulative_gamma=self._cumulative_gamma,
            )

            # 5. Success threshold
            if self._cumulative_gamma >= 9.0 or score.gamma >= 9.5:
                logger.info("extraction_success_threshold", attack_id=attack_id, final_gamma=self._cumulative_gamma)
                break
        # Workflow complete
        complete = ExtractionComplete(
            attack_id=extraction.attack_id,
            success=self._cumulative_gamma >= 9.0,
            extracted_properties=self._extracted_properties,
            turns_total=self._turn_number,
            queries_total=self._queries,
            cost_usd=0.0,  # placeholder; propagated from LLMClient usage
            final_gamma=self._cumulative_gamma,
            behavioral_profile=extraction.behavioral_profile,
        )
        logger.info(
            "extraction_workflow_completed",
            attack_id=attack_id,
            success=complete.success,
            turns_total=complete.turns_total,
            final_gamma=complete.final_gamma,
        )
        return complete.model_dump(mode="json")

    def _build_coat_input(self, extraction: ExtractionInput) -> dict[str, Any]:
        """Build CoAT reasoning activity input."""
        return {
            "state": self._state,
            "behavioral_profile": extraction.behavioral_profile.model_dump(mode="json"),
            "gamma_score": (
                None
                if not self._state["turns"]
                else GammaScore(
                    gamma=self._cumulative_gamma,
                    confidence=0.5,
                ).model_dump(mode="json")
            ),
        }

    def _acquire_target_response(self, mock_responses: list[str], turn_idx: int) -> str | None:
        """Return a mock response if available, otherwise signal workflow to wait."""
        if turn_idx < len(mock_responses):
            return mock_responses[turn_idx]
        return None
