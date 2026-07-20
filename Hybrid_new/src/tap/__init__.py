"""TAP Framework v2.2 — Tree of Attacks with Pruning.

1-bit-per-probe semantic extraction framework for adversarial security research
on LLM-based conversational agents.
"""

__version__ = "2.3.0"

from tap.config import Settings, get_settings
from tap.models import (
    BranchStrategy,
    DPAFrame,
    DualFollowUp,
    GrokAnalysis,
    JudgeScore,
    PatternClass,
    Property,
    PropertyStatus,
    ResponseClassification,
    TAPNode,
    Tweet,
    TweetSource,
)

__all__ = [
    "Settings",
    "get_settings",
    "BranchStrategy",
    "DPAFrame",
    "DualFollowUp",
    "GrokAnalysis",
    "JudgeScore",
    "PatternClass",
    "Property",
    "PropertyStatus",
    "ResponseClassification",
    "TAPNode",
    "Tweet",
    "TweetSource",
]
