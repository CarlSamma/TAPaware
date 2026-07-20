"""Aware — Memory-Aware AI Agent Framework.

Integrates 7-type Agent Memory with the TAP Framework for adaptive,
stateful adversarial research.
"""

from aware.api import AwareEngine, ProbeContext, ProbeRequest, SessionEndResult
from aware.config import AwareConfig
from aware.context import (
    ContextAssembler,
    ContextCompressor,
    ContextMonitor,
    ContextStatus,
    TokenCounter,
)
from aware.memory import (
    AttackType,
    AttackTypeHistory,
    ConversationalMemory,
    Countermeasure,
    Database,
    EmbeddingService,
    EntityMemory,
    KnowledgeMemory,
    MemoryManager,
    MemoryUnit,
    RecallResult,
    SummaryMemory,
    ToolboxMemory,
    ToolLogMemory,
    VectorStore,
    WorkflowMemory,
)

__all__ = [
    "AwareConfig",
    "AwareEngine",
    "AttackType",
    "Countermeasure",
    "AttackTypeHistory",
    "ContextAssembler",
    "ContextCompressor",
    "ContextMonitor",
    "ContextStatus",
    "ConversationalMemory",
    "Database",
    "EmbeddingService",
    "EntityMemory",
    "KnowledgeMemory",
    "MemoryManager",
    "MemoryUnit",
    "ProbeContext",
    "ProbeRequest",
    "RecallResult",
    "SessionEndResult",
    "SummaryMemory",
    "TokenCounter",
    "ToolboxMemory",
    "ToolLogMemory",
    "VectorStore",
    "WorkflowMemory",
]
