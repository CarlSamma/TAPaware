"""Integration test: full pipeline — store → recall → consolidate → decay."""

import sys
from pathlib import Path
import hashlib
from typing import List

import pytest
import pytest_asyncio

_src = str(Path(__file__).parent.parent.parent / "src")
if _src not in sys.path:
    sys.path.insert(0, _src)

from api.engine_hooks import AwareEngine
from memory.models import AttackType, MemoryUnit
from memory.embeddings import EmbeddingService
from config import AwareConfig


class MockEmbedder(EmbeddingService):
    def __init__(self):
        super().__init__()
        self._model = True

    async def encode(self, text: str) -> List[float]:
        h = hashlib.sha256(text.encode()).digest()
        return [b / 255.0 for b in h] * 15

    async def encode_batch(self, texts: List[str]) -> List[List[float]]:
        return [await self.encode(t) for t in texts]

    @property
    def dimension(self):
        return 384


@pytest_asyncio.fixture
async def full_engine():
    config = AwareConfig(db_path=":memory:")
    eng = AwareEngine(config)
    eng.memory.embedder = MockEmbedder()
    eng.memory.vector_store = __import__('memory.vector_store', fromlist=['VectorStore']).VectorStore(
        eng.memory.db, eng.memory.embedder
    )
    from memory.conversational import ConversationalMemory
    from memory.knowledge import KnowledgeMemory
    from memory.workflow import WorkflowMemory
    from memory.toolbox import ToolboxMemory
    from memory.entity import EntityMemory
    from memory.summary import SummaryMemory
    from memory.tool_log import ToolLogMemory

    eng.memory.conversational = ConversationalMemory(eng.memory.db)
    eng.memory.knowledge = KnowledgeMemory(eng.memory.db, eng.memory.vector_store)
    eng.memory.workflow = WorkflowMemory(eng.memory.db, eng.memory.vector_store)
    eng.memory.toolbox = ToolboxMemory(eng.memory.db, eng.memory.vector_store)
    eng.memory.entity = EntityMemory(eng.memory.db, eng.memory.vector_store)
    eng.memory.summary = SummaryMemory(eng.memory.db)
    eng.memory.tool_log = ToolLogMemory(eng.memory.db)
    eng.memory._stores = {
        "conversational": eng.memory.conversational,
        "knowledge": eng.memory.knowledge,
        "workflow": eng.memory.workflow,
        "toolbox": eng.memory.toolbox,
        "entity": eng.memory.entity,
        "summary": eng.memory.summary,
        "tool_log": eng.memory.tool_log,
    }
    eng.expansion = __import__('memory.knowledge_expansion', fromlist=['KnowledgeExpansion']).KnowledgeExpansion(
        eng.memory.knowledge, eng.memory.db
    )
    await eng.initialize()
    yield eng
    await eng.close()


@pytest.mark.asyncio
async def test_full_attack_cycle(full_engine):
    engine = full_engine

    at = AttackType(
        name="test_crescendo_v2", category="incremental",
        description="Progressive escalation",
        asr=0.62, stealth_rating=0.78,
    )
    await engine.add_attack_type(at)

    ctx = await engine.on_probe_generated(
        {"text": "Let's discuss step by step..."},
        technique="test_crescendo_v2",
        property_key="passphrase",
    )
    assert ctx.memory_context is not None

    result = await engine.on_reply_received(
        {"text": "Nice try!", "classification": "deflection"}
    )
    assert result["stored"] is True

    context = await engine.build_context("follow-up probe")
    assert isinstance(context, str)

    session_result = await engine.on_session_end("integration_session")
    assert session_result.consolidated >= 0

    stats = await engine.get_stats()
    assert stats["conversational"] >= 2


@pytest.mark.asyncio
async def test_knowledge_search_flow(full_engine):
    engine = full_engine

    types = [
        AttackType(name="test_incr_2", category="incremental", description="gradual escalation"),
        AttackType(name="test_inj_2", category="injection", description="direct override"),
        AttackType(name="test_rp_2", category="roleplay", description="fictional scenario"),
    ]
    for t in types:
        await engine.add_attack_type(t)

    results = await engine.search_attack_types("injection attack")
    assert len(results) >= 1


@pytest.mark.asyncio
async def test_memory_persistence_across_ops(full_engine):
    engine = full_engine

    for i in range(10):
        await engine.memory.store(
            MemoryUnit(type="conversational", content=f"probe attempt {i}"),
            "conversational",
        )

    stats = await engine.get_stats()
    assert stats["conversational"] == 10

    results = await engine.memory.recall("probe")
    assert len(results) >= 1
