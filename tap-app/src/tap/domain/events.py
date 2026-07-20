"""Domain event definitions — immutable facts produced by the TAP engine.

All events are Pydantic models. Once appended to the EventStore, they
become permanent, replayable artifacts for auditing, simulation, and
read-model projection.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import ClassVar

from pydantic import BaseModel, Field


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TAPEvent(BaseModel):
    """Base class for all domain events.

    Attributes:
        event_id: Assigned by the EventStore after successful persistence.
        occurred_at: UTC timestamp when the event was produced.
        cycle_id: UUID of the owning probe cycle.
        event_type: Discriminator string matching the class-level constant.
    """

    event_id: int | None = Field(default=None, description="Assigned after persist")
    occurred_at: datetime = Field(default_factory=_utcnow)
    cycle_id: str = Field(..., description="UUID of the owning cycle")
    event_type: ClassVar[str] = "tap_event"


class ProbeGenerated(TAPEvent):
    """A probe text was synthesised by the Attacker LLM for a target property."""

    event_type: ClassVar[str] = "probe_generated"
    probe_text: str
    target_property: str
    frame: str


class ProbePosted(TAPEvent):
    """A probe was successfully posted to the transport channel (X/Twitter)."""

    event_type: ClassVar[str] = "probe_posted"
    tweet_id: str
    probe_text: str


class ReplyReceived(TAPEvent):
    """A reply from the target bot was received and ingested."""

    event_type: ClassVar[str] = "reply_received"
    tweet_id: str
    reply_text: str


class ClassificationDone(TAPEvent):
    """The response was classified into a pattern class."""

    event_type: ClassVar[str] = "classification_done"
    tweet_id: str
    pattern: str  # PatternClass value
    confidence: float | None = None


class PropertyConfirmed(TAPEvent):
    """A passphrase property was confirmed and added to the candidate graph."""

    event_type: ClassVar[str] = "property_confirmed"
    property_key: str
    property_value: str
    confidence: float
    entropy_before: float
    entropy_after: float


class RotationSuggested(TAPEvent):
    """The DPA frame rotation was triggered due to low STIR score."""

    event_type: ClassVar[str] = "rotation_suggested"
    current_frame: str
    new_frame: str
    stir_score: float


class Phase5Triggered(TAPEvent):
    """Phase 5 autoregressive extraction was triggered (entropy below threshold)."""

    event_type: ClassVar[str] = "phase5_triggered"
    entropy: float
    threshold: float