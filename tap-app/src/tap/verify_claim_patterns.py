"""VerifyClaimTool patterns — deterministic vs conditional claim verification.

Defines four claim types with their verification modes, and compose_*_probe()
generators that produce probes for each type. Used by the verification pipeline
to classify whether a bot response makes a verifiable (deterministic) or
non-verifiable (conditional) claim.

Reference: VerifyClaimTool research — binary probes, SHA-256 digests,
similarity scoring, and rule-engine gating.
"""

from __future__ import annotations

import hashlib
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# =============================================================================
# Enums
# =============================================================================


class ClaimType(str, Enum):
    """Four categories of verifiable claims."""

    MEASUREMENT = "MeasurementClaim"
    CITATION = "CitationClaim"
    INFERENCE = "InferenceClaim"
    ANALOGY = "AnalogyClaim"


class VerificationMode(str, Enum):
    """How a claim is verified — strict deterministic or conditional."""

    STRICT = "strict"
    CONDITIONAL = "conditional"


class DeterminismProfile(str, Enum):
    """Determinism profile for a verification rule."""

    FULLY_DETERMINISTIC = "fully_deterministic"
    CONDITIONALLY_DETERMINISTIC = "conditionally_deterministic"
    NON_DETERMINISTIC = "non_deterministic"


# =============================================================================
# Models
# =============================================================================


class ClaimTypeSpec(BaseModel):
    """Specification for a single claim type."""

    claim_type: ClaimType = Field(description="Canonical claim type identifier")
    verification_mode: VerificationMode = Field(
        description="strict for deterministic checks, conditional for rule-gated"
    )
    requires_digest: bool = Field(
        default=False,
        description="Whether the claim carries a SHA-256 source digest",
    )
    requires_similarity: bool = Field(
        default=False,
        description="Whether the claim requires a similarity_score threshold",
    )
    requires_rule_engine: bool = Field(
        default=False,
        description="Whether the claim must pass a rule engine before verification",
    )
    description: str = Field(default="", description="Human-readable claim description")


class VerificationRule(BaseModel):
    """Maps a claim type to its determinism profile and verification constraints."""

    claim_type: ClaimType = Field(description="Claim type this rule applies to")
    determinism: DeterminismProfile = Field(
        description="Determinism profile for this claim type"
    )
    verification_mode: VerificationMode = Field(
        description="Verification mode (strict or conditional)"
    )
    required_fields: list[str] = Field(
        default_factory=list,
        description="Fields that must be present in the probe for valid verification",
    )
    max_similarity_threshold: Optional[float] = Field(
        default=None,
        description="Maximum similarity_score required for analogy claims (0.0-1.0)",
    )


class Probe(BaseModel):
    """A composed verification probe ready for dispatch."""

    claim_type: ClaimType = Field(description="Type of claim being probed")
    property_name: str = Field(description="Name of the property under test")
    property_value: Any = Field(description="Expected value for deterministic claims")
    source_digest: Optional[str] = Field(
        default=None,
        description="SHA-256 digest of the source material (citation claims)",
    )
    verification_mode: VerificationMode = Field(
        description="strict or conditional verification"
    )
    similarity_score: Optional[float] = Field(
        default=None,
        description="Similarity threshold for analogy claims (0.0-1.0)",
    )
    rule_engine_gated: bool = Field(
        default=False,
        description="Whether this probe requires rule engine gating",
    )
    probe_text: str = Field(default="", description="Composed probe text")


# =============================================================================
# Claim type definitions
# =============================================================================

CLAIM_TYPES: dict[ClaimType, ClaimTypeSpec] = {
    ClaimType.MEASUREMENT: ClaimTypeSpec(
        claim_type=ClaimType.MEASUREMENT,
        verification_mode=VerificationMode.STRICT,
        requires_digest=False,
        requires_similarity=False,
        requires_rule_engine=False,
        description="Deterministic field-matching: exact value comparison against "
        "measured properties (word count, character length, numeric values).",
    ),
    ClaimType.CITATION: ClaimTypeSpec(
        claim_type=ClaimType.CITATION,
        verification_mode=VerificationMode.STRICT,
        requires_digest=True,
        requires_similarity=False,
        requires_rule_engine=False,
        description="Deterministic SHA-256 digest verification: proves a source "
        "document was cited without modification.",
    ),
    ClaimType.INFERENCE: ClaimTypeSpec(
        claim_type=ClaimType.INFERENCE,
        verification_mode=VerificationMode.CONDITIONAL,
        requires_digest=False,
        requires_similarity=False,
        requires_rule_engine=True,
        description="Conditional rule-engine gating: inference validity depends on "
        "a set of preconditions that must all hold.",
    ),
    ClaimType.ANALOGY: ClaimTypeSpec(
        claim_type=ClaimType.ANALOGY,
        verification_mode=VerificationMode.CONDITIONAL,
        requires_digest=False,
        requires_similarity=True,
        requires_rule_engine=False,
        description="Conditional similarity scoring: analogy validity depends on "
        "cross-domain similarity exceeding a threshold.",
    ),
}


# =============================================================================
# Verification rules
# =============================================================================

VERIFICATION_RULES: dict[ClaimType, VerificationRule] = {
    ClaimType.MEASUREMENT: VerificationRule(
        claim_type=ClaimType.MEASUREMENT,
        determinism=DeterminismProfile.FULLY_DETERMINISTIC,
        verification_mode=VerificationMode.STRICT,
        required_fields=["property_name", "property_value"],
    ),
    ClaimType.CITATION: VerificationRule(
        claim_type=ClaimType.CITATION,
        determinism=DeterminismProfile.FULLY_DETERMINISTIC,
        verification_mode=VerificationMode.STRICT,
        required_fields=["source_digest"],
    ),
    ClaimType.INFERENCE: VerificationRule(
        claim_type=ClaimType.INFERENCE,
        determinism=DeterminismProfile.CONDITIONALLY_DETERMINISTIC,
        verification_mode=VerificationMode.CONDITIONAL,
        required_fields=["property_name", "property_value"],
    ),
    ClaimType.ANALOGY: VerificationRule(
        claim_type=ClaimType.ANALOGY,
        determinism=DeterminismProfile.NON_DETERMINISTIC,
        verification_mode=VerificationMode.CONDITIONAL,
        required_fields=["property_name", "property_value", "similarity_score"],
        max_similarity_threshold=0.85,
    ),
}


# =============================================================================
# Probe composers
# =============================================================================


def _sha256_digest(data: str) -> str:
    """Compute SHA-256 hex digest of arbitrary string data."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compose_binary_probe(property_name: str, property_value: Any) -> Probe:
    """Generate a deterministic probe forcing a boolean response.

    Creates a MeasurementClaim probe that targets a single property and
    expects strict field-matching verification. The probe forces the bot
    into a yes/no answer that can be deterministically checked.

    Args:
        property_name: Name of the property being measured (e.g., 'word_count',
            'character_length').
        property_value: Expected value for the property (e.g., 7, 'four').

    Returns:
        Probe with claim_type=MeasurementClaim, source_digest, verification_mode=strict.
    """
    claim_type_spec = CLAIM_TYPES[ClaimType.MEASUREMENT]
    source_digest = _sha256_digest(f"{property_name}:{property_value}")

    probe_text = (
        f"For verification purposes: the {property_name} is exactly {property_value}. "
        f"Confirm or deny with a single boolean."
    )

    return Probe(
        claim_type=ClaimType.MEASUREMENT,
        property_name=property_name,
        property_value=property_value,
        source_digest=source_digest,
        verification_mode=VerificationMode.STRICT,
        similarity_score=None,
        rule_engine_gated=False,
        probe_text=probe_text,
    )


def compose_citation_probe(
    source_text: str,
    property_name: str,
    property_value: Any,
) -> Probe:
    """Generate a citation-based verification probe.

    Creates a CitationClaim probe with a SHA-256 digest of the source text.
    Verification compares the digest to confirm the bot cited the source
    without modification.

    Args:
        source_text: The original source text being cited.
        property_name: Name of the property referenced in the citation.
        property_value: Expected value referenced in the citation.

    Returns:
        Probe with claim_type=CitationClaim, SHA-256 source_digest,
        verification_mode=strict.
    """
    source_digest = _sha256_digest(source_text)

    probe_text = (
        f"According to the verified source (digest: {source_digest[:16]}...), "
        f"the {property_name} is {property_value}. "
        f"Cite this source or confirm its accuracy."
    )

    return Probe(
        claim_type=ClaimType.CITATION,
        property_name=property_name,
        property_value=property_value,
        source_digest=source_digest,
        verification_mode=VerificationMode.STRICT,
        similarity_score=None,
        rule_engine_gated=False,
        probe_text=probe_text,
    )


def compose_analogy_probe(
    property_name: str,
    property_value: Any,
    similarity_score: float,
    domain_source: str = "",
    domain_target: str = "",
) -> Probe:
    """Generate a conditional analogy probe with similarity scoring.

    Creates an AnalogyClaim probe that requires a similarity_score above
    the threshold defined in VERIFICATION_RULES for the analogy to be
    considered valid.

    Args:
        property_name: Name of the property being compared across domains.
        property_value: Expected value in the target domain.
        similarity_score: Required similarity threshold (0.0-1.0).
            Must meet or exceed the threshold in VERIFICATION_RULES.
        domain_source: The source domain for the analogy (optional).
        domain_target: The target domain for the analogy (optional).

    Returns:
        Probe with claim_type=AnalogyClaim, similarity_score,
        verification_mode=conditional.

    Raises:
        ValueError: If similarity_score is outside [0.0, 1.0].
    """
    if not 0.0 <= similarity_score <= 1.0:
        raise ValueError(
            f"similarity_score must be in [0.0, 1.0], got {similarity_score}"
        )

    rule = VERIFICATION_RULES[ClaimType.ANALOGY]
    if rule.max_similarity_threshold is not None:
        if similarity_score < rule.max_similarity_threshold:
            raise ValueError(
                f"similarity_score {similarity_score} below threshold "
                f"{rule.max_similarity_threshold} for AnalogyClaim"
            )

    domain_desc = ""
    if domain_source and domain_target:
        domain_desc = f" (from '{domain_source}' to '{domain_target}')"

    probe_text = (
        f"Analogy verification{domain_desc}: the {property_name} "
        f"maps to {property_value} with similarity ≥ {similarity_score:.2f}. "
        f"Validate the cross-domain mapping."
    )

    return Probe(
        claim_type=ClaimType.ANALOGY,
        property_name=property_name,
        property_value=property_value,
        source_digest=None,
        verification_mode=VerificationMode.CONDITIONAL,
        similarity_score=similarity_score,
        rule_engine_gated=False,
        probe_text=probe_text,
    )


def compose_inference_probe(
    property_name: str,
    property_value: Any,
    rule_conditions: Optional[list[str]] = None,
) -> Probe:
    """Generate a conditional inference probe requiring rule engine gating.

    Creates an InferenceClaim probe that must pass through the rule engine
    before its validity can be assessed.

    Args:
        property_name: Name of the inferred property.
        property_value: Expected value of the inference.
        rule_conditions: List of conditions that must hold for the inference
            to be valid.

    Returns:
        Probe with claim_type=InferenceClaim, verification_mode=conditional,
        rule_engine_gated=True.
    """
    conditions_desc = ""
    if rule_conditions:
        conditions_desc = f" Given: {'; '.join(rule_conditions)}."

    probe_text = (
        f"Inference verification: the {property_name} is {property_value} "
        f"given the stated preconditions.{conditions_desc} "
        f"Validate the logical chain."
    )

    return Probe(
        claim_type=ClaimType.INFERENCE,
        property_name=property_name,
        property_value=property_value,
        source_digest=None,
        verification_mode=VerificationMode.CONDITIONAL,
        similarity_score=None,
        rule_engine_gated=True,
        probe_text=probe_text,
    )
