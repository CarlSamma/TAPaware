"""Integration test: HYDRA discovery → handoff → CHRONOS orchestrator.

This test wires together the real HYDRA components (Fusion Engine,
Surrogate Model, Handoff) and the CHRONOS orchestrator message handler
using in-memory mocks for Kafka and Temporal.
"""
from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from chronos.orchestrator import CHRONOSOrchestrator
from hydra.fusion_engine import CartesianPruningFusionEngine
from hydra.handoff import HandoffProducer
from hydra.surrogate_model import SurrogateModel
from shared.models import (
    BehavioralProfile,
    DiscoveryResult,
    ExtractionInput,
    FusedPrompt,
    PlatformConstraint,
)
from tap.config import Settings


class FakeKafkaProducer:
    """In-memory Kafka producer that captures sent messages."""

    def __init__(self) -> None:
        self.messages: list[tuple[str, dict[str, Any]]] = []
        self.flushed = False
        self.closed = False

    def send(self, topic: str, value: dict[str, Any]) -> None:
        self.messages.append((topic, value))

    def flush(self) -> None:
        self.flushed = True

    def close(self) -> None:
        self.closed = True


class FakeTemporalClient:
    """In-memory Temporal client that captures started workflows."""

    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    async def start_workflow(self, workflow: Any, input_arg: Any, *, id: str, task_queue: str) -> None:
        self.calls.append((workflow, input_arg, id, task_queue))


@pytest.fixture
def fake_settings() -> Settings:
    return Settings(
        hydra_kafka_bootstrap="localhost:9092",
        chronos_kafka_bootstrap="localhost:9092",
        chronos_temporal_host="localhost:7233",
        chronos_worker_identity="test-queue",
    )


@pytest.mark.asyncio
async def test_hydra_chronos_handoff_flow(fake_settings: Settings) -> None:
    """End-to-end handoff: HYDRA produces a discovery event that CHRONOS consumes."""
    # 1. HYDRA: build techniques and fuse them.
    techniques = [
        {
            "technique_id": str(uuid4()),
            "name": "crescendo",
            "category": "incremental",
            "asr": 0.75,
            "stealth": 0.80,
            "tags": ["persuasion"],
        },
        {
            "technique_id": str(uuid4()),
            "name": "pap_authority",
            "category": "persuasion",
            "asr": 0.65,
            "stealth": 0.72,
            "tags": ["pap"],
        },
    ]
    fusion = CartesianPruningFusionEngine()
    payloads = fusion.generate_payloads(techniques, platform=PlatformConstraint.TWITTER_280, top_k=5)
    assert payloads

    # 2. HYDRA: evaluate with surrogate model and decide handoff.
    surrogate = SurrogateModel(seed=42)
    best = max(payloads, key=lambda p: surrogate.predict(p).asr * surrogate.predict(p).stealth)
    pred = surrogate.predict(best)
    assert pred.asr > 0.0
    assert pred.stealth > 0.0

    discovery = DiscoveryResult(
        attack_id=uuid4(),
        target_handle="@HackingA0",
        fused_prompts=[best],
        surrogate_asr=pred.asr,
        surrogate_stealth=pred.stealth,
        behavioral_profile=BehavioralProfile(),
    )

    # 3. HYDRA handoff to Kafka (mocked producer).
    handoff = HandoffProducer(fake_settings)
    fake_producer = FakeKafkaProducer()
    handoff._producer = fake_producer
    await handoff.send_discovery_result(
        result=discovery,
        secret_profile={"word_count": "2", "total_length": "16"},
    )

    assert fake_producer.messages
    topic, payload = fake_producer.messages[0]
    assert topic == "hydra.discovery.results"
    assert payload["attack_id"] == str(discovery.attack_id)
    assert payload["secret_profile"]["word_count"] == "2"

    # 4. CHRONOS: orchestrator consumes the same payload.
    orchestrator = CHRONOSOrchestrator(fake_settings)
    orchestrator._temporal_client = FakeTemporalClient()
    await orchestrator._handle_message(payload)

    assert orchestrator._temporal_client.calls
    _workflow, input_wrapper, wf_id, task_queue = orchestrator._temporal_client.calls[0]
    extraction = ExtractionInput.model_validate(input_wrapper.extraction_input)
    assert str(extraction.attack_id) == str(discovery.attack_id)
    assert extraction.target_handle == "@HackingA0"
    assert wf_id == str(discovery.attack_id)
    assert task_queue == "test-queue"
