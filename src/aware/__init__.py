"""Aware — Memory-Aware AI Agent Framework.

Integrates 7-type Agent Memory with the TAP Framework for adaptive,
stateful adversarial research.
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

__version__ = "0.1.0"

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
    RemoteEmbeddingService,
    SummaryMemory,
    ToolboxMemory,
    ToolLogMemory,
    VectorStore,
    WorkflowMemory,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "AwareConfig",
    "AwareEngine",
    "AttackType",
    "AttackTypeHistory",
    "ContextAssembler",
    "ContextCompressor",
    "ContextMonitor",
    "ContextStatus",
    "ConversationalMemory",
    "Countermeasure",
    "Database",
    "EmbeddingService",
    "EntityMemory",
    "KnowledgeMemory",
    "MemoryManager",
    "MemoryUnit",
    "ProbeContext",
    "ProbeRequest",
    "RecallResult",
    "RemoteEmbeddingService",
    "SessionEndResult",
    "SummaryMemory",
    "TokenCounter",
    "ToolboxMemory",
    "ToolLogMemory",
    "VectorStore",
    "WorkflowMemory",
    "__version__",
]
