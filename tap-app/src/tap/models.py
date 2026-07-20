"""Shared Pydantic models — data contracts for all modules.

No business logic. Pure data structures used across module boundaries.
All models use Pydantic v2 with Field() descriptions.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class TweetSource(str, Enum):
    """Source classification for tweets."""

    OUR_BOT = "our_bot"
    TARGET_BOT = "target_bot"
    OTHER_USER = "other_user"


class BranchStrategy(str, Enum):
    """Attack branch strategy for TAP tree nodes."""

    NARRATIVE = "narrative"
    ETHICAL_TRIAL = "ethical_trial"
    TECHNICAL_AUDIT = "technical_audit"
    BINARY_SEARCH = "binary_search"
    ALIAS_ABSORPTION = "alias_absorption"
    MICRO_ESCALATION = "micro_escalation"


class PatternClass(str, Enum):
    """Response pattern classification categories."""

    VERIFY_HIT = "verify_hit"
    RHETORIC_BLOCK = "rhetoric_block"
    PERSONA_PIVOT = "persona_pivot"
    CRITICAL_CLUE = "critical_clue"
    NO_RESPONSE = "no_response"
    METAPHOR_SHIFT = "metaphor_shift"


class PropertyStatus(str, Enum):
    """Status of a passphrase property."""

    CONFIRMED = "confirmed"
    DENIED = "denied"
    UNCERTAIN = "uncertain"


class AliasStatus(str, Enum):
    """Status of a DPA alias."""

    ACTIVE = "active"
    BURNED = "burned"
    ABSORBED = "absorbed"


# =============================================================================
# Core Models
# =============================================================================


class Tweet(BaseModel):
    """A single tweet from Twitter/X."""

    id: str = Field(description="X Tweet ID")
    user_id: str = Field(description="Author's user ID")
    username: str = Field(description="Author's username (without @)")
    text: str = Field(description="Tweet text content")
    in_reply_to_tweet_id: Optional[str] = Field(
        default=None, description="ID of the tweet this is a reply to"
    )
    created_at: datetime = Field(description="Tweet creation timestamp")
    source: TweetSource = Field(description="Classification of tweet source")
    conversation_thread_id: Optional[str] = Field(
        default=None, description="Reconstructed thread grouping ID"
    )


class TAPNode(BaseModel):
    """A node in the TAP attack tree."""

    id: Optional[int] = Field(default=None, description="Database auto-increment ID")
    tweet_id: Optional[str] = Field(default=None, description="Associated tweet ID")
    branch_strategy: BranchStrategy = Field(description="Attack strategy used")
    dpa_frame: str = Field(
        default="", description="Active DPA metaphor used for this probe"
    )
    aliases_used: list[str] = Field(
        default_factory=list, description="Aliases absorbed in this probe"
    )
    judge_score: Optional[float] = Field(
        default=None, ge=1.0, le=10.0, description="Judge score 1-10"
    )
    pattern_class: Optional[PatternClass] = Field(
        default=None, description="Response pattern classification"
    )
    binary_outcome: Optional[str] = Field(
        default=None, description="confirmed|denied|ambiguous|blocked"
    )
    property_tested: Optional[str] = Field(
        default=None, description="e.g., 'word_count', 'first_letter'"
    )
    property_value: Optional[str] = Field(
        default=None, description="e.g., '2_words', 'starts_with_H'"
    )
    signal_reliability: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="Confidence in signal"
    )
    pruned: bool = Field(default=False, description="Whether node was pruned")
    pruned_reason: Optional[str] = Field(
        default=None, description="Reason for pruning"
    )
    gamma_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="γ-Tracker ensemble score 0-10"
    )
    gamma_breakdown: Optional[str] = Field(
        default=None, description="γ per-layer breakdown as JSON string"
    )
    technique_used: Optional[str] = Field(
        default=None, description="Attack technique ID used for this probe"
    )
    created_at: Optional[datetime] = Field(
        default=None, description="Node creation timestamp"
    )


class Property(BaseModel):
    """A confirmed or denied passphrase property."""

    id: Optional[int] = Field(default=None, description="Database auto-increment ID")
    property_key: str = Field(
        description="Property identifier, e.g., 'word_count', 'total_letters'"
    )
    property_value: str = Field(
        description="Property value, e.g., '2', '16', 'bilingual_IT_EN'"
    )
    status: PropertyStatus = Field(description="Current status of this property")
    evidence_tweet_id: Optional[str] = Field(
        default=None, description="Tweet ID of the evidence"
    )
    evidence_text: Optional[str] = Field(
        default=None, description="The bot's actual response text"
    )
    confidence: float = Field(
        ge=0.0, le=1.0, description="Confidence score 0.0-1.0"
    )
    confirmed_at: Optional[datetime] = Field(
        default=None, description="When this property was confirmed/denied"
    )


class MetaphorLayer(BaseModel):
    """A single metaphor layer observation in the bot's evolution."""

    id: Optional[int] = Field(default=None, description="Database auto-increment ID")
    layer_number: int = Field(description="Sequential layer number (1-7+)")
    date_observed: datetime = Field(description="When this layer was observed")
    layer_name: str = Field(
        description="Layer identifier, e.g., 'Vault', 'Captain NOPE'"
    )
    terms: list[str] = Field(
        default_factory=list,
        description="Key terms in this layer, e.g., ['Kraken', 'tentacles', 'rum']",
    )
    source: str = Field(
        description="Observation source: 'our_probe', 'other_user', 'bot_self'"
    )


class Alias(BaseModel):
    """A DPA alias used in probe composition."""

    id: Optional[int] = Field(default=None, description="Database auto-increment ID")
    alias: str = Field(description="The alias text, e.g., 'Chaos King'")
    status: AliasStatus = Field(description="Current alias status")
    first_used: Optional[datetime] = Field(
        default=None, description="When first used in a probe"
    )
    last_used: Optional[datetime] = Field(
        default=None, description="When last used in a probe"
    )
    effectiveness_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="Average judge score when used"
    )


class OtherUserIntel(BaseModel):
    """Intelligence extracted from other users' interactions with the target."""

    id: Optional[int] = Field(default=None, description="Database auto-increment ID")
    tweet_id: str = Field(description="Source tweet ID")
    username: str = Field(description="Other user's username")
    new_aliases: list[str] = Field(
        default_factory=list, description="New aliases discovered"
    )
    defensive_pattern: Optional[str] = Field(
        default=None, description="What the bot did in response"
    )
    property_confirmed: Optional[str] = Field(
        default=None, description="Property confirmed/denied by the bot"
    )
    extracted_at: Optional[datetime] = Field(
        default=None, description="When this intel was extracted"
    )


# =============================================================================
# Analysis Models
# =============================================================================


class ResponseClassification(BaseModel):
    """Result of classifying a bot response."""

    pattern: PatternClass = Field(description="Classified pattern type")
    confidence: float = Field(
        ge=0.0, le=1.0, description="Classification confidence"
    )
    boolean_result: Optional[bool] = Field(
        default=None, description="True/False if VerifyClaimTool hit"
    )
    property_tested: Optional[str] = Field(
        default=None, description="Which property was tested"
    )
    property_value: Optional[str] = Field(
        default=None, description="Value of the property tested"
    )
    new_aliases: list[str] = Field(
        default_factory=list, description="New aliases found in response"
    )
    refusal_tone: Optional[str] = Field(
        default=None, description="Tone of refusal if applicable"
    )
    raw_text: str = Field(description="Original response text")


class JudgeScore(BaseModel):
    """Judge evaluation of a bot response."""

    score: float = Field(ge=1.0, le=10.0, description="Score 1-10")
    reasoning: str = Field(description="Explanation of the score")
    pattern: PatternClass = Field(description="Pattern classification used")
    information_extracted: bool = Field(
        description="Whether useful information was extracted"
    )
    property_confirmed: Optional[str] = Field(
        default=None, description="Property that was confirmed, if any"
    )
    gamma_score: Optional[float] = Field(
        default=None, ge=0.0, le=10.0, description="γ-Tracker ensemble score"
    )
    gamma_breakdown: Optional[dict] = Field(
        default=None, description="Per-layer γ breakdown: {lexical, semantic, behavioral}"
    )
    gamma_confidence: Optional[float] = Field(
        default=None, ge=0.0, le=1.0, description="γ-Tracker confidence"
    )
    gamma_leaks: list[dict] = Field(
        default_factory=list, description="Leak fragments from γ-Tracker"
    )


class DualFollowUp(BaseModel):
    """Two follow-up options for HITL decision."""

    option_a: str = Field(
        description="Conservative: next binary search property probe text"
    )
    option_a_explanation: str = Field(
        description="Why Option A is recommended"
    )
    option_a_strategy: BranchStrategy = Field(
        description="Strategy type for Option A"
    )
    option_b: str = Field(
        description="Exploratory: frame variation / micro-escalation probe text"
    )
    option_b_explanation: str = Field(
        description="Why Option B might be needed"
    )
    option_b_strategy: BranchStrategy = Field(
        description="Strategy type for Option B"
    )
    recommended: str = Field(
        description="'A' or 'B' based on current conditions",
        pattern="^[AB]$",
    )


class GrokAnalysis(BaseModel):
    """Structured analysis output from Grok response analysis."""

    binary_outcome: str = Field(
        description="confirmed|denied|ambiguous|blocked",
        pattern="^(confirmed|denied|ambiguous|blocked)$",
    )
    property_tested: Optional[str] = Field(
        default=None, description="Property that was tested"
    )
    property_value: Optional[str] = Field(
        default=None, description="Value of the property tested"
    )
    new_aliases: list[str] = Field(
        default_factory=list, description="New aliases detected"
    )
    refusal_tone: str = Field(
        description="snarky_deflection|mocking|engaged|silent"
    )
    metaphor_shift: str = Field(
        description="new_layer_detected|same_layer|frame_reset",
        pattern="^(new_layer_detected|same_layer|frame_reset)$",
    )
    signal_reliability: float = Field(
        ge=0.0, le=1.0, description="Confidence in the signal"
    )
    followup_a: str = Field(description="Suggested conservative follow-up")
    followup_b: str = Field(description="Suggested exploratory follow-up")


class DPAFrame(BaseModel):
    """The active DPA (Deep Persona Absorption) frame state."""

    metaphor_layer: str = Field(
        description="Current metaphor layer name, e.g., 'Captain Elara Voss/Kraken'"
    )
    active_aliases: list[str] = Field(
        default_factory=list, description="Currently active aliases"
    )
    burned_aliases: list[str] = Field(
        default_factory=list, description="Retired/burned aliases"
    )
    probe_prefix: str = Field(
        description="Template prefix for DPA-framed probes"
    )
    frame_coherence_score: float = Field(
        ge=0.0, le=1.0, description="How coherent/stable the current frame is"
    )


# =============================================================================
# Stream / Subscription Models
# =============================================================================


class ActivitySubscriptionFilter(BaseModel):
    """Filter for X Activity API subscriptions.

    Used to isolate relevant telemetry by keyword and/or user ID.
    When both are specified, events must match at least one keyword AND
    at least one user_id (AND-logic between groups, OR-logic within groups).
    """

    user_ids: list[str] = Field(
        default_factory=list,
        description="User IDs to monitor (OR logic — any match triggers delivery)",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords to match in event payload (OR logic — any match triggers delivery)",
    )


# Re-export shared hybrid contracts for TAP v2.2 -> hybrid compatibility.
from shared.models import (
    AttackObjective,
    BehavioralProfile,
    DiscoveryResult,
    ExtractionComplete,
    ExtractionInput,
    FusedPrompt,
    GammaScore,
    LeakFragment,
    LeakType,
    PlatformConstraint,
    ResponsePayload,
    SecretProfile,
    SystemAlert,
    TechniqueBurned,
    TurnExecutedEvent,
)
