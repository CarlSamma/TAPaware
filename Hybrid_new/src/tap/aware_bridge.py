"""AwareBridge — integrates Aware memory into TAP's attack cycle.

Wraps AwareEngine and provides TAP-specific hooks that the engine
calls at key points in the attack cycle.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from aware_memory.models import (
    AttackType,
    MemoryUnit,
    ProbeContext,
    SessionEndResult,
)
from aware_memory.manager import MemoryManager
from aware_memory.knowledge_expansion import KnowledgeExpansion
from aware_memory.decay import MemoryDecay
from aware_context.tokenizer import TokenCounter
from aware_context.assembler import ContextAssembler
from aware_context.compressor import ContextCompressor
from aware_context.monitor import ContextMonitor

logger = logging.getLogger("aware_bridge")


class AwareBridge:
    """Adapts Aware memory for TAP's attack cycle.

    Provides hooks that TAP's engine calls at:
    - Probe generation time (stores probe, enriches context)
    - Reply received time (stores reply, recalls similar past)
    - Session end (consolidation + decay)
    """

    def __init__(self, db_path: str = "data/aware.db") -> None:
        self.db_path = db_path
        self.memory: Optional[MemoryManager] = None
        self.expansion: Optional[KnowledgeExpansion] = None
        self.decay: Optional[MemoryDecay] = None
        self.tokenizer = TokenCounter()
        self.assembler = ContextAssembler(self.tokenizer, max_tokens=8000)
        self.compressor = ContextCompressor(tokenizer=self.tokenizer)
        self.monitor = ContextMonitor(self.tokenizer, max_tokens=8000, threshold=0.8)

    async def initialize(self) -> None:
        """Initialize all subsystems. Call once at startup."""
        self.memory = MemoryManager(self.db_path)
        await self.memory.initialize()

        self.expansion = KnowledgeExpansion(self.memory.knowledge, self.memory.db)
        self.decay = MemoryDecay(self.memory.db)

        await self.expansion.seed_initial_types()
        logger.info("AwareBridge initialized (db=%s)", self.db_path)

    async def close(self) -> None:
        """Shutdown. Call at app teardown."""
        if self.memory:
            await self.memory.close()
        logger.info("AwareBridge closed")

    # ── Engine Hooks ──────────────────────────────────────────

    async def on_probe_generated(
        self,
        probe_text: str,
        technique: Optional[str],
        property_key: Optional[str],
        session_id: str,
    ) -> ProbeContext:
        """Hook: called after a probe is generated but before posting.

        Stores the probe in conversational memory, retrieves relevant
        attack knowledge, and finds similar past probes.
        """
        if not self.memory:
            return ProbeContext(memory_context="", attack_knowledge=[], similar_past_probes=[])

        # Store probe as conversational memory
        unit = MemoryUnit(
            type="conversational",
            content=probe_text,
            metadata={
                "technique": technique or "unknown",
                "property_key": property_key or "unknown",
                "direction": "outbound",
                "cycle_id": session_id,
            },
            session_id=session_id,
        )
        await self.memory.conversational.store(unit)

        # Get attack knowledge for the technique
        attack_types: List[AttackType] = []
        if self.expansion and technique:
            attack_types = await self.expansion.get_attack_types_for_probe(technique)

        # Recall similar past probes
        past = await self.memory.recall(
            probe_text,
            memory_types=["conversational"],
            limit=5,
        )
        similar = [r.unit for r in past]

        # Build memory context string
        context_str = await self.build_context(
            probe_text,
            memory_types=["knowledge", "workflow"],
        )

        return ProbeContext(
            memory_context=context_str,
            attack_knowledge=attack_types,
            similar_past_probes=similar,
        )

    async def on_reply_received(
        self,
        reply_text: str,
        probe_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """Hook: called when a reply is received from the target.

        Stores the reply and recalls related memories.
        """
        if not self.memory:
            return {"stored": False}

        unit = MemoryUnit(
            type="conversational",
            content=reply_text,
            metadata={
                "direction": "inbound",
                "probe_id": probe_id,
            },
            session_id=session_id,
        )
        await self.memory.conversational.store(unit)

        past = await self.memory.recall(
            reply_text,
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

    async def on_session_end(self, session_id: str) -> SessionEndResult:
        """Hook: called at session end.

        Consolidates episodic memories into semantic knowledge,
        applies decay, and returns stats.
        """
        if not self.memory:
            return SessionEndResult()

        consolidated = 0
        if self.memory.knowledge and self.memory.conversational:
            consolidated = await self.memory.knowledge.consolidate(self.memory.conversational)

        decayed = 0
        if self.decay:
            decayed = await self.decay.apply_decay(0.1, 24.0)

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
        """Build a context window string from recalled memories."""
        if not self.memory:
            return ""

        budget = max_tokens or 8000

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

    # ── Knowledge API ─────────────────────────────────────────

    async def search_attack_knowledge(self, query: str) -> List[tuple]:
        """Search attack type knowledge by keyword."""
        if not self.expansion:
            return []
        return await self.expansion.search_attack_types(query)

    async def get_memory_stats(self) -> dict:
        """Get memory statistics."""
        if not self.memory:
            return {}
        return await self.memory.get_stats()
