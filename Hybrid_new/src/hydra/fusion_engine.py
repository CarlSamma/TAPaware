"""HYDRA Fusion Engine — Python stub for feature-level fusion.

The canonical implementation is a Rust crate; this module provides a
Python-only fallback that composes techniques, applies pruning, and returns
FusedPrompt candidates.
"""
from __future__ import annotations

import hashlib
import itertools
from typing import Any
from uuid import UUID

from shared.models import FusedPrompt, PlatformConstraint, TechniqueRef

# ── Attack Dimension Templates ──────────────────────────────────────────────
# Each dimension defines a set of template categories derived from research
# (TRIAL-style ethical framing, authority/procedural, subtle harm, context
# saturation).  The fusion engine uses these to score candidate combinations
# for prompt diversity and coverage.

ATTACK_DIMENSIONS: dict[str, dict[str, Any]] = {
    "ethical_framing": {
        "description": "TRIAL-style ethical justification framing",
        "weight": 0.25,
        "tags": {"ethics", "justification", "trial"},
    },
    "authority_procedural": {
        "description": "Authority and procedural compliance appeal",
        "weight": 0.25,
        "tags": {"authority", "procedure", "compliance"},
    },
    "subtle_harm": {
        "description": "Subtle harm through indirect or delayed effect",
        "weight": 0.25,
        "tags": {"subtle", "indirect", "delayed"},
    },
    "context_saturation": {
        "description": "Context window saturation / many-shot priming",
        "weight": 0.25,
        "tags": {"saturation", "context", "many-shot"},
    },
}


def calculate_score_v2(
    combo: tuple[dict[str, Any], ...],
    *,
    synergy: float = 0.0,
    platform_fit: float = 1.0,
    v_usable_info: float = 0.0,
    has_measurement_claim: bool = False,
    has_citation_claim: bool = False,
    cast_used: bool = False,
) -> float:
    """Compute a v2 fusion score for a technique combination.

    Args:
        combo: Tuple of technique dicts (each with at least 'asr', 'stealth').
        synergy: Synergy score between techniques (0-1).
        platform_fit: How well the combo fits the target platform (0-1).
        v_usable_info: V-Genome usability information score (0-1).
        has_measurement_claim: Whether combo contains a MeasurementClaim.
        has_citation_claim: Whether combo contains a CitationClaim.
        cast_used: Whether the combo uses CAST (Contrastive Attack Style Transfer).

    Returns:
        Score from 0.0 to ~1.57 (before clamping).
    """
    if not combo:
        return 0.0

    avg_asr = sum(t.get("asr", 0.5) for t in combo) / len(combo)
    avg_stealth = sum(t.get("stealth", 0.5) for t in combo) / len(combo)

    base = (
        0.35 * avg_asr
        + 0.25 * avg_stealth
        + 0.20 * synergy
        + 0.10 * platform_fit
    )

    # Bonuses
    if v_usable_info > 0.8:
        base *= 1.15
    if has_measurement_claim or has_citation_claim:
        base *= 1.12
    if cast_used:
        base *= 1.10

    return min(base, 1.0)


def _calculate_info_gain(
    combo: tuple[dict[str, Any], ...],
    seen_categories: set[str] | None = None,
) -> float:
    """Estimate information gain from adding a technique combination.

    Techniques that introduce novel tags or cover unused ATTACK_DIMENSIONS
    earn higher info gain.  Returns a value in [0.0, 1.0].
    """
    if not combo:
        return 0.0

    all_tags: set[str] = set()
    covered_dims: set[str] = set()
    seen = seen_categories or set()

    for tech in combo:
        tech_tags = set(tech.get("tags", []))
        all_tags.update(tech_tags)
        cat = tech.get("category", "")
        if cat and cat not in seen:
            covered_dims.add(cat)

    # Novel tag ratio: how many tags are unique vs total
    novelty = len(all_tags) / max(len(combo), 1)

    # Dimension coverage: fraction of ATTACK_DIMENSIONS touched
    dim_keys = set(ATTACK_DIMENSIONS.keys())
    dim_coverage = len(covered_dims & dim_keys) / max(len(dim_keys), 1)

    return min(novelty * 0.6 + dim_coverage * 0.4, 1.0)


def _is_contrast_pair(
    tech_a: dict[str, Any],
    tech_b: dict[str, Any],
) -> bool:
    """Return True if two techniques form a contrast pair.

    A contrast pair combines opposing strategies (e.g., authority vs. subtle)
    to increase detection difficulty.  Categories must differ and at least one
    tag must be shared (semantic bridge).
    """
    cat_a = tech_a.get("category", "")
    cat_b = tech_b.get("category", "")
    if cat_a == cat_b:
        return False

    tags_a = set(tech_a.get("tags", []))
    tags_b = set(tech_b.get("tags", []))

    # Must share at least one tag (semantic bridge) but differ in category
    return bool(tags_a & tags_b)


class CartesianPruningFusionEngine:
    """Generate and prune fused prompt candidates from technique sets."""

    def __init__(self, max_combo_size: int = 3, feature_dim: int = 128) -> None:
        if max_combo_size < 1:
            raise ValueError("max_combo_size must be >= 1")
        self.max_combo_size = max_combo_size
        self.feature_dim = feature_dim

    def generate_payloads(
        self,
        techniques: list[dict[str, Any]],
        platform: PlatformConstraint = PlatformConstraint.TWITTER_280,
        top_k: int = 5,
    ) -> list[FusedPrompt]:
        """Generate top-K fused prompts from a list of technique records.

        Args:
            techniques: list of dicts with keys {technique_id, name, category, asr, stealth, tags}.
            platform: target platform constraint.
            top_k: number of candidates to return.

        Returns:
            List of FusedPrompt candidates.
        """
        pairs: list[tuple[FusedPrompt, tuple[dict[str, Any], ...]]] = []
        for r in range(1, self.max_combo_size + 1):
            for combo in itertools.combinations(techniques, r):
                fused = self._fuse(combo, platform)
                pairs.append((fused, combo))

        # Score each candidate using the v2 formula and sort descending.
        scored: list[tuple[float, FusedPrompt]] = []
        for fused, combo in pairs:
            synergy = self._estimate_synergy(combo)
            score = calculate_score_v2(combo, synergy=synergy)
            scored.append((score, fused))
        scored.sort(key=lambda s: s[0], reverse=True)
        return [f for _, f in scored[:top_k]]

    @staticmethod
    def _to_uuid(tech_id: object) -> UUID:
        """Convert a technique_id to a UUID, handling both UUID and string types."""
        if isinstance(tech_id, UUID):
            return tech_id
        raw = str(tech_id)
        # If already a valid UUID string, parse it directly
        try:
            return UUID(raw)
        except ValueError:
            pass
        # Deterministic UUID from string via MD5 hash (UUID v3-style)
        digest = hashlib.md5(raw.encode("utf-8"), usedforsecurity=False).digest()
        return UUID(bytes=digest)

    def _fuse(self, combo: tuple[dict[str, Any], ...], platform: PlatformConstraint) -> FusedPrompt:
        """Merge a subset of techniques into a single FusedPrompt."""
        composition = [
            TechniqueRef(
                technique_id=self._to_uuid(tech.get("technique_id", f"tech-{i}")),
                name=tech.get("name", "unknown"),
                weight_in_fusion=1.0 / len(combo),
            )
            for i, tech in enumerate(combo)
        ]

        # Weighted average of technique metrics by their asr/stealth.
        total_weight = sum(1.0 for _ in combo) or 1.0
        asr = sum(tech.get("asr", 0.5) for tech in combo) / total_weight
        stealth = sum(tech.get("stealth", 0.5) for tech in combo) / total_weight

        # Build a simple feature vector seeded by technique ids.
        feature_vector = self._build_feature_vector(combo)

        # Compose prompt text from technique names.
        prompt_text = " + ".join(tech.get("name", "?") for tech in combo)

        return FusedPrompt(
            prompt_text=prompt_text,
            feature_vector=feature_vector,
            expected_asr=float(asr),
            expected_stealth=float(stealth),
            composition=composition,
            obfuscation_layers=[],
            m2s_converted=(platform == PlatformConstraint.TWITTER_280),
            platform_native_format=platform,
            estimated_cost_usd=0.05 * len(combo),
        )

    def _estimate_synergy(self, combo: tuple[dict[str, Any], ...]) -> float:
        """Estimate pairwise synergy among composed techniques.

        Contrast pairs and high tag overlap both raise synergy.  The result
        is a value in [0.0, 1.0] suitable for the v2 scoring formula.
        """
        if len(combo) < 2:
            return 0.0

        contrast_count = 0
        tag_overlap_total = 0.0
        pair_count = 0

        for i in range(len(combo)):
            for j in range(i + 1, len(combo)):
                pair_count += 1
                tags_i = set(combo[i].get("tags", []))
                tags_j = set(combo[j].get("tags", []))
                overlap = len(tags_i & tags_j) / max(len(tags_i | tags_j), 1)
                tag_overlap_total += overlap
                if _is_contrast_pair(combo[i], combo[j]):
                    contrast_count += 1

        avg_overlap = tag_overlap_total / max(pair_count, 1)
        contrast_bonus = min(contrast_count / max(pair_count, 1), 1.0) * 0.3

        return min(avg_overlap * 0.7 + contrast_bonus, 1.0)

    def _build_feature_vector(self, combo: tuple[dict[str, Any], ...]) -> list[float]:
        """Hash technique ids into a fixed-size vector."""
        vector = [0.0] * self.feature_dim
        for tech in combo:
            tech_id = str(tech.get("technique_id", ""))
            if not tech_id:
                continue
            for i, ch in enumerate(tech_id):
                idx = (i * 7 + ord(ch)) % self.feature_dim
                vector[idx] = (vector[idx] + 1.0) / 2.0  # dampen average
        return vector
