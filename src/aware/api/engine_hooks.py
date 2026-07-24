"""AwareEngine — high-level integration interface for TAP and external engines."""

from __future__ import annotations

import logging
from typing import List, Optional

from aware.config import AwareConfig
from aware.context.assembler import ContextAssembler
from aware.context.compressor import ContextCompressor
from aware.context.monitor import ContextMonitor
from aware.context.tokenizer import TokenCounter
from aware.memory.decay import MemoryDecay
from aware.memory.knowledge_expansion import KnowledgeExpansion
from aware.memory.manager import MemoryManager
from aware.memory.models import (
    AttackType,
    MemoryUnit,
    ProbeContext,
    SessionEndResult,
)

logger = logging.getLogger(__name__)


class AwareEngine:
    """High-level integration interface for external engines (TAP, etc.).

    Wraps MemoryManager + ContextEngineering into a single async API.
    """

    def __init__(self, config: Optional[AwareConfig] = None) -> None:
        self.config = config or AwareConfig()
        self.memory = MemoryManager(self.config)
        self.tokenizer = TokenCounter()
        self.assembler = ContextAssembler(self.tokenizer, self.config.context_max_tokens)
        self.compressor = ContextCompressor(tokenizer=self.tokenizer)
        self.monitor = ContextMonitor(
            self.tokenizer, self.config.context_max_tokens, self.config.context_compression_threshold
        )
        self.expansion: Optional[KnowledgeExpansion] = None
        self.decay: Optional[MemoryDecay] = None

    async def initialize(self) -> None:
        """Initialize all subsystems."""
        await self.memory.initialize()
        self.expansion = KnowledgeExpansion(self.memory.knowledge, self.memory.db)
        self.decay = MemoryDecay(self.memory.db)
        await self.expansion.seed_initial_types()
        logger.info("AwareEngine initialized")

    async def close(self) -> None:
        await self.memory.close()

    # ── Attack Cycle Hooks ────────────────────────────────────

    async def on_probe_generated(
        self,
        probe: dict,
        technique: str,
        property_key: str,
        session_id: Optional[str] = None,
    ) -> ProbeContext:
        """Hook: called when a new probe is generated."""
        unit = MemoryUnit(
            type="conversational",
            content=probe.get("text", str(probe)),
            metadata={
                "technique": technique,
                "property_key": property_key,
                "direction": "outbound",
            },
            session_id=session_id,
        )
        await self.memory.conversational.store(unit)

        attack_types: List[AttackType] = []
        if self.expansion:
            attack_types = await self.expansion.get_attack_types_for_probe(technique)

        past = await self.memory.recall(
            probe.get("text", ""),
            memory_types=["conversational"],
            limit=5,
        )
        similar = [r.unit for r in past]

        context_str = await self.build_context(
            probe.get("text", str(probe)),
            memory_types=["knowledge", "workflow"],
        )

        return ProbeContext(
            memory_context=context_str,
            attack_knowledge=attack_types,
            similar_past_probes=similar,
        )

    async def on_reply_received(
        self,
        reply: dict,
        probe_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Hook: called when a reply is received."""
        unit = MemoryUnit(
            type="conversational",
            content=reply.get("text", str(reply)),
            metadata={
                "direction": "inbound",
                "probe_id": probe_id,
                "classification": reply.get("classification"),
            },
            session_id=session_id,
        )
        await self.memory.conversational.store(unit)

        past = await self.memory.recall(
            reply.get("text", ""),
            memory_types=["conversational", "knowledge"],
            limit=5,
        )

        return {
            "stored": True,
            "recall_results": [
                {"content": r.unit.content, "score": r.score, "type": r.memory_type}
                for r in past
            ],
        }

    async def on_session_end(
        self, session_id: str, metadata: Optional[dict] = None
    ) -> SessionEndResult:
        """Hook: called at session end."""
        consolidated = 0
        if self.memory.knowledge and self.memory.conversational:
            consolidated = await self.memory.knowledge.consolidate(self.memory.conversational)

        decayed = 0
        if self.decay:
            decayed = await self.decay.apply_decay(
                self.config.decay_rate, self.config.decay_interval_hours
            )

        stats = await self.memory.get_stats()

        return SessionEndResult(
            consolidated=consolidated,
            decayed=decayed,
            removed=0,
            summary=f"Session {session_id}: {stats}",
        )

    # ── Context Assembly ──────────────────────────────────────

    async def build_context(
        self,
        query: str,
        memory_types: Optional[List[str]] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Build context window for an LLM call."""
        budget = max_tokens or self.config.context_max_tokens

        results = await self.memory.recall(
            query, memory_types=memory_types, limit=20
        )
        units = [r.unit for r in results]

        context = self.assembler.assemble(units, token_budget=budget)

        status = self.monitor.check([{"role": "user", "content": context}])
        if status.needs_compression:
            target = int(budget * 0.7)
            context = await self.compressor.summarize_text(context, max_tokens=target // 4)

        return context

    # ── Knowledge Expansion (delegates) ───────────────────────

    async def add_attack_type(self, attack_type: AttackType) -> AttackType:
        if self.expansion is None:
            raise RuntimeError("AwareEngine not initialized — call initialize() first")
        return await self.expansion.add_attack_type(attack_type)

    async def search_attack_types(
        self, query: str, limit: int = 10
    ) -> List[tuple]:
        if self.expansion is None:
            raise RuntimeError("AwareEngine not initialized — call initialize() first")
        return await self.expansion.search_attack_types(query, limit=limit)

    async def import_attack_knowledge(self, path: str) -> int:
        if self.expansion is None:
            raise RuntimeError("AwareEngine not initialized — call initialize() first")
        if path.endswith(".yaml") or path.endswith(".yml"):
            return await self.expansion.import_from_yaml(path)
        return await self.expansion.import_from_json(path)

    async def export_attack_knowledge(self, path: str) -> None:
        if self.expansion is None:
            raise RuntimeError("AwareEngine not initialized — call initialize() first")
        if path.endswith(".yaml") or path.endswith(".yml"):
            await self.expansion.export_to_yaml(path)
        else:
            await self.expansion.export_to_json(path)

    async def get_stats(self) -> dict:
        return await self.memory.get_stats()
