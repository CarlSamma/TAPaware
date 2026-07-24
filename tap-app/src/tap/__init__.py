"""TAP Framework v3.1 — Tree of Attacks with Pruning.

1-bit-per-probe semantic extraction framework for adversarial security research
on LLM-based conversational agents.
"""

__version__ = "3.1.0"

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
