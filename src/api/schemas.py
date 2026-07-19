"""Request/response Pydantic models for the API layer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

# Ensure src/ is on path
_src = str(Path(__file__).parent.parent)
if _src not in sys.path:
    sys.path.insert(0, _src)

from memory.models import AttackType, MemoryUnit


class ProbeRequest(BaseModel):
    """Request payload for probe generation hook."""
    property_key: str
    technique: str
    persona_id: Optional[str] = None
    session_id: Optional[str] = None


class ProbeContext(BaseModel):
    """Enriched context returned to the engine after probe generation."""
    memory_context: str
    attack_knowledge: List[AttackType] = Field(default_factory=list)
    similar_past_probes: List[MemoryUnit] = Field(default_factory=list)


class ReplyRequest(BaseModel):
    """Request payload for reply received hook."""
    text: str
    probe_id: Optional[str] = None
    session_id: Optional[str] = None
    classification: Optional[str] = None


class ReplyResult(BaseModel):
    """Result after processing a reply."""
    stored: bool
    recall_results: List[dict] = Field(default_factory=list)


class SessionEndRequest(BaseModel):
    """Request payload for session end hook."""
    session_id: str
    metadata: Dict = Field(default_factory=dict)


class SessionEndResult(BaseModel):
    """Result returned after session consolidation."""
    consolidated: int = 0
    decayed: int = 0
    removed: int = 0
    summary: str = ""


class ContextBuildRequest(BaseModel):
    """Request for context assembly."""
    query: str
    memory_types: Optional[List[str]] = None
    max_tokens: Optional[int] = None


class ContextBuildResult(BaseModel):
    """Result of context assembly."""
    context: str
    token_count: int
    needs_compression: bool


class AttackTypeCreateRequest(BaseModel):
    """Request to create an attack type."""
    name: str
    category: str
    description: str
    asr: Optional[float] = None
    stealth_rating: Optional[float] = None
    target: Optional[str] = None
    example_probes: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class AttackTypeSearchRequest(BaseModel):
    """Request to search attack types."""
    query: str
    limit: int = 10
    threshold: float = 0.5
