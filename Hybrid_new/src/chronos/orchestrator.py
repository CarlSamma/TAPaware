"""CHRONOS orchestrator — Kafka consumer + Temporal workflow starter.

Listens to `hydra.discovery.results` and starts an ExtractionWorkflow
when a vulnerable target is detected.
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from kafka import KafkaConsumer  # type: ignore[import-untyped]
from temporalio.client import Client

from shared.models import BehavioralProfile, ExtractionInput
from tap.config import Settings
from tap.logger import get_logger

logger = get_logger("chronos.orchestrator")

_TOPIC = "hydra.discovery.results"


class CHRONOSOrchestrator:
    """Bridge between HYDRA discovery results and CHRONOS Temporal workflows."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._temporal_client: Client | None = None
        self._consumer: KafkaConsumer | None = None

    async def start(self) -> None:
        """Connect to Temporal and Kafka, then run the consume loop."""
        await self._connect_temporal()
        self._connect_kafka()
        logger.info("chronos_orchestrator_started")

        loop = asyncio.get_event_loop()
        consumer = self._consumer
        assert consumer is not None
        while True:
            msg = await loop.run_in_executor(None, next, consumer)
            if msg is None:
                continue
            try:
                await self._handle_message(msg.value)
            except Exception as e:
                logger.error("orchestrator_message_failed", error=str(e), raw=msg.value)

    async def _connect_temporal(self) -> None:
        async with asyncio.timeout(10.0):
            self._temporal_client = await Client.connect(self.settings.chronos_temporal_host)
        logger.info("temporal_client_connected", host=self.settings.chronos_temporal_host)

    def _connect_kafka(self) -> None:
        self._consumer = KafkaConsumer(
            _TOPIC,
            bootstrap_servers=self.settings.chronos_kafka_bootstrap,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        )

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        """Decode a HYDRA discovery result and start the CHRONOS workflow."""
        attack_id = payload.get("attack_id")
        target_handle = payload.get("target_handle")
        logger.info(
            "discovery_result_received",
            attack_id=str(attack_id),
            target_handle=target_handle,
        )

        behavioral_profile = (
            BehavioralProfile.model_validate(payload["behavioral_profile"])
            if payload.get("behavioral_profile")
            else BehavioralProfile()
        )
        from uuid import UUID, uuid4
        extraction_input = ExtractionInput(
            attack_id=UUID(str(attack_id)) if attack_id else uuid4(),
            target_handle=target_handle or "",
            secret_profile=payload.get("secret_profile", {}),
            fused_payloads=[],
            behavioral_profile=behavioral_profile,
        )

        from chronos.workflows.extraction_workflow import (
            ExtractionWorkflow,
            ExtractionWorkflowInput,
        )

        if self._temporal_client is None:
            raise OrchestratorError("Temporal client not connected")

        async with asyncio.timeout(10.0):
            await self._temporal_client.start_workflow(
                ExtractionWorkflow.run,
                ExtractionWorkflowInput(extraction_input=extraction_input.model_dump(mode="json")),
                id=str(attack_id),
                task_queue=self.settings.chronos_worker_identity,
            )
        logger.info("extraction_workflow_started", attack_id=str(attack_id))


class OrchestratorError(Exception):
    """Domain error for orchestrator failures."""
