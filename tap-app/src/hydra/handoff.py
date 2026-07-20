"""HYDRA Handoff — publish TargetVulnerableDetected to Kafka.

This triggers CHRONOS durable workflows.

Regola 3: correlation IDs in log.
Regola 5: timeouts on external calls.
Regola 8: event sourcing on Kafka (no markdown SSOT).
"""
from __future__ import annotations

import asyncio
import json
from typing import Any

from kafka import KafkaProducer  # type: ignore[import-untyped]

from shared.models import DiscoveryResult
from tap.config import Settings
from tap.logger import get_logger

logger = get_logger("hydra.handoff")

_TOPIC = "hydra.discovery.results"


class HandoffProducer:
    """Async wrapper around kafka-python to handoff vulnerable targets to CHRONOS."""

    def __init__(self, settings: Settings) -> None:
        self.bootstrap = settings.hydra_kafka_bootstrap
        self._producer: KafkaProducer | None = None

    def _ensure_producer(self) -> KafkaProducer:
        """Lazy-init synchronous KafkaProducer."""
        if self._producer is None:
            self._producer = KafkaProducer(
                bootstrap_servers=self.bootstrap,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            )
        return self._producer

    async def send_discovery_result(
        self,
        result: DiscoveryResult,
        secret_profile: dict[str, Any] | None = None,
    ) -> None:
        """Publish a DiscoveryResult (with optional secret profile) to Kafka."""
        producer = self._ensure_producer()
        payload = result.model_dump(mode="json")
        if secret_profile:
            payload["secret_profile"] = secret_profile

        logger.info(
            "handoff_discovery_result",
            attack_id=str(result.attack_id),
            target_handle=result.target_handle,
            topic=_TOPIC,
        )

        loop = asyncio.get_event_loop()
        try:
            async with asyncio.timeout(10.0):
                await loop.run_in_executor(None, producer.send, _TOPIC, payload)
                await loop.run_in_executor(None, producer.flush)
        except asyncio.TimeoutError as e:
            logger.error("handoff_timeout", attack_id=str(result.attack_id))
            raise HandoffError(f"Kafka handoff timed out: {e}") from e

    async def close(self) -> None:
        if self._producer:
            await asyncio.get_event_loop().run_in_executor(None, self._producer.close)
            self._producer = None


class HandoffError(Exception):
    """Domain error for handoff failures."""
