"""Expected Information Gain property selector.

Replaces the static priority list in engine.select_next_property().
Scores each candidate property by:
  EIG(p) = H_residual(p) × yield_rate(p) - cost(p)

Uses math.log2 from stdlib (no numpy dependency).
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

from tap.config import Settings
from tap.domain.candidate_graph import CandidateGraph
from tap.execution.probe_memory import ProbeMemory
from tap.logger import get_logger

log = get_logger("eig_ranker")


def shannon_entropy(values: list[float]) -> float:
    """Calculate Shannon entropy: H = -sum(p * log2(p)).

    Args:
        values: List of probability values or counts.

    Returns:
        Entropy in bits. Returns 0.0 for edge cases (empty list, single value, all zeros).
    """
    if not values or len(values) == 1:
        return 0.0

    # Filter out zeros to avoid log2(0)
    non_zero = [v for v in values if v > 0]
    if not non_zero:
        return 0.0

    total = sum(non_zero)
    if total == 0:
        return 0.0

    # Normalize to probabilities
    probs = [v / total for v in non_zero]

    # Calculate entropy
    entropy = 0.0
    for p in probs:
        if p > 0:
            entropy -= p * math.log2(p)

    return entropy


def conditional_entropy(ssot: dict, property_name: str) -> float:
    """Calculate conditional entropy H(Z|O) given SSOT state.

    Args:
        ssot: Single Source of Truth dictionary containing observed properties.
        property_name: Name of the property to calculate conditional entropy for.

    Returns:
        Conditional entropy in bits.
    """
    if property_name not in ssot:
        return 0.0

    # Get the observed value
    observed_value = ssot[property_name]
    if observed_value is None:
        return 0.0

    # Estimate distribution of property values from SSOT
    # For conditional entropy, we need to know how much uncertainty remains
    # after observing O. This is a simplified estimation.
    values = list(ssot.values())
    if not values:
        return 0.0

    # Convert values to a consistent format for entropy calculation
    value_counts = Counter()
    for v in values:
        if v is not None:
            value_counts[str(v)] += 1

    if not value_counts:
        return 0.0

    # Calculate conditional entropy based on observed value distribution
    counts = list(value_counts.values())
    return shannon_entropy(counts)


def calculate_info_gain(ssot: dict, property_name: str) -> float:
    """Calculate V-usable information: I_V = H_V(Z) - H_V(Z|O).

    Args:
        ssot: Single Source of Truth dictionary containing observed properties.
        property_name: Name of the property to calculate info gain for.

    Returns:
        Bits of information gained.
    """
    if not ssot:
        return 0.0

    # Get all property values for prior entropy H_V(Z)
    all_values = [v for v in ssot.values() if v is not None]
    if not all_values:
        return 0.0

    # Calculate prior entropy
    value_counts = Counter(str(v) for v in all_values)
    h_prior = shannon_entropy(list(value_counts.values()))

    # Calculate conditional entropy H_V(Z|O)
    h_conditional = conditional_entropy(ssot, property_name)

    # Information gain = prior entropy - conditional entropy
    return max(0.0, h_prior - h_conditional)


class EIGRanker:
    """Expected Information Gain property selector.

    Scores each candidate property by combining entropy reduction,
    historical yield rate, and transport cost.
    """

    def __init__(
        self,
        candidate_graph: CandidateGraph,
        probe_memory: ProbeMemory,
        settings: Settings,
    ) -> None:
        self._cg = candidate_graph
        self._pm = probe_memory
        self._settings = settings
        self._universe = self._load_universe(settings.eig_property_universe_path)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def rank(self, unconfirmed_properties: list[str]) -> list[tuple[str, float]]:
        """Return (property_key, eig_score) sorted descending."""
        scored = []
        for prop_key in unconfirmed_properties:
            h_residual = self._universe.get(prop_key, 1.0)
            yield_rate = 0.5  # default for unseen
            # We can't call get_family_yield_rate without a probe text, so
            # use the property key itself as a heuristic lookup
            conn = self._pm._db._ensure_connected()
            cursor = await conn.execute(
                """SELECT AVG(CASE WHEN pattern_class = 'VERIFY_HIT' THEN 1.0 ELSE 0.0 END) as rate
                   FROM probe_memory
                   WHERE probe_preview LIKE ?""",
                (f"%{prop_key}%",),
            )
            row = await cursor.fetchone()
            if row and row["rate"] is not None:
                yield_rate = float(row["rate"])
            cost = 1.0  # fixed for X transport
            eig = h_residual * yield_rate - cost
            scored.append((prop_key, round(eig, 4)))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    async def rank_v2(self, unconfirmed_properties: list[str], ssot: dict) -> list[tuple[str, float]]:
        """Return (property_key, combined_score) sorted descending.

        Combines V-usable information gain with existing EIG score:
        score = 0.6 * info_gain + 0.4 * existing_score

        Args:
            unconfirmed_properties: List of property keys to rank.
            ssot: Current Single Source of Truth state.

        Returns:
            List of (property_key, combined_score) tuples, sorted descending.
        """
        # First get existing scores
        existing_scores = await self.rank(unconfirmed_properties)
        existing_dict = {k: v for k, v in existing_scores}

        scored = []
        for prop_key in unconfirmed_properties:
            # Calculate V-usable information gain
            info_gain = calculate_info_gain(ssot, prop_key)

            # Get existing score (default to 0 if not found)
            existing_score = existing_dict.get(prop_key, 0.0)

            # Combined score: 0.6 * info_gain + 0.4 * existing_score
            combined_score = 0.6 * info_gain + 0.4 * existing_score
            scored.append((prop_key, round(combined_score, 4)))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:3]  # Return top 3

    async def select_next(self) -> str:
        """Return the highest-EIG unconfirmed property."""
        confirmed = await self._cg.get_confirmed_properties()
        confirmed_keys = {p.property_key for p in confirmed}
        all_properties = list(self._universe.keys())
        if not all_properties:
            # Fallback to static list if no universe config
            all_properties = [
                "word_count", "total_length", "first_letter", "language",
                "word1_length", "word2_length", "word1_language", "word2_language",
            ]
        unconfirmed = [k for k in all_properties if k not in confirmed_keys]
        if not unconfirmed:
            return "additional_metadata"
        ranked = await self.rank(unconfirmed)
        if not ranked:
            return unconfirmed[0]
        return ranked[0][0]

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_universe(self, path: str) -> dict[str, float]:
        """Load EIG property universe from JSON file.

        Expected format: {"word_count": 2.0, "total_length": 3.0, ...}
        """
        try:
            p = Path(path)
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                return {k: float(v) for k, v in data.items()}
        except Exception as e:
            log.warning("eig_universe_load_failed", path=path, error=str(e))
        # Default universe
        return {
            "word_count": 2.0,
            "total_length": 3.0,
            "first_letter": 1.0,
            "language": 1.5,
            "word1_length": 2.0,
            "word2_length": 2.0,
            "word1_language": 1.5,
            "word2_language": 1.5,
        }