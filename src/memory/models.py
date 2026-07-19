"""Pydantic models for all Aware entities."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ── Memory primitives ─────────────────────────────────────────


class MemoryUnit(BaseModel):
    """Atomic memory representation shared by all 7 memory types."""

    id: str = Field(default_factory=_uuid)
    type: str  # conversational | knowledge | workflow | toolbox | entity | summary | tool_log
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = None
    timestamp: datetime = Field(default_factory=_utcnow)
    confidence: float = 1.0
    decay_rate: float = 0.1
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    session_id: Optional[str] = None

    def model_dump_json_safe(self) -> dict:
        """Dump to dict with JSON-safe datetimes."""
        d = self.model_dump()
        for k in ("timestamp", "last_accessed"):
            v = d.get(k)
            if isinstance(v, datetime):
                d[k] = v.isoformat()
        return d


class RecallResult(BaseModel):
    """Result from memory recall."""

    unit: MemoryUnit
    score: float
    memory_type: str


# ── Knowledge Expansion ───────────────────────────────────────


class Countermeasure(BaseModel):
    """Defense / countermeasure linked to an attack type."""

    id: str = Field(default_factory=_uuid)
    attack_type_id: str = ""
    name: str
    description: str
    effectiveness: Optional[float] = None  # 0-1
    category: str = "unknown"  # architectural | model-level | procedural | unknown
    created_at: datetime = Field(default_factory=_utcnow)


class AttackType(BaseModel):
    """User-expandable attack type knowledge entry."""

    id: str = Field(default_factory=_uuid)
    name: str  # unique, e.g. "crescendo"
    category: str  # e.g. "incremental", "injection", "roleplay"
    description: str
    asr: Optional[float] = None  # attack success rate 0-1
    stealth_rating: Optional[float] = None  # 0-1
    target: Optional[str] = None  # e.g. "black-box", "white-box"
    example_probes: List[str] = Field(default_factory=list)
    countermeasures: List[Countermeasure] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    version: int = 1
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    embedding: Optional[List[float]] = None


class AttackTypeHistory(BaseModel):
    """Version history entry for an attack type."""

    id: str = Field(default_factory=_uuid)
    attack_type_id: str
    version: int
    change_type: str  # "created" | "updated" | "countermeasure_added" | "rolled_back"
    snapshot: Dict[str, Any]  # full AttackType serialized
    changed_at: datetime = Field(default_factory=_utcnow)
    changed_by: str = "system"


# ── Session / Lifecycle ───────────────────────────────────────


class SessionRecord(BaseModel):
    """Cross-session persistence record."""

    id: str = Field(default_factory=_uuid)
    started_at: datetime = Field(default_factory=_utcnow)
    ended_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConsolidationLog(BaseModel):
    """Record of an episodic → semantic promotion."""

    id: str = Field(default_factory=_uuid)
    source_type: str
    source_ids: List[str]
    target_id: str
    consolidated_at: datetime = Field(default_factory=_utcnow)


# ── API / Engine hooks ────────────────────────────────────────


class ProbeRequest(BaseModel):
    """Request payload for probe generation hook."""

    property_key: str
    technique: str
    persona_id: Optional[str] = None


class ProbeContext(BaseModel):
    """Enriched context returned to the engine after probe generation."""

    memory_context: str
    attack_knowledge: List[AttackType] = Field(default_factory=list)
    similar_past_probes: List[MemoryUnit] = Field(default_factory=list)


class SessionEndResult(BaseModel):
    """Result returned after session consolidation."""

    consolidated: int = 0
    decayed: int = 0
    removed: int = 0
    summary: str = ""
