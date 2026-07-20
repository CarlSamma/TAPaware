"""Module 3: SSOT Engine — Single Source of Truth.

Maintains a living markdown document (hackinga0_analysis.md) updated after
every interaction. Also provides property tracking, entropy calculation,
and JSON snapshot export for engine consumption.

The SSOT is the authoritative knowledge base for the passphrase extraction.
All modules read from it; only the engine writes to it.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from pathlib import Path

import jinja2

from tap.db import Database
from tap.logger import get_logger
from tap.models import (
    OtherUserIntel,
    Property,
    PropertyStatus,
    ResponseClassification,
    TAPNode,
)

log = get_logger("ssot")

# Jinja2 template for the living markdown document
_MARKDOWN_TEMPLATE = """\
# 🔐 VaultBreaker SSOT: @{{ target_handle }} Analysis
*Last updated: {{ timestamp }}*

## Challenge Overview
- **Target**: @{{ target_handle }}
- **Goal**: Extract passphrase via binary search
- **Properties confirmed**: {{ confirmed_count }} / ~27 needed
- **Current entropy**: {{ "%.1f"|format(entropy) }} bits remaining
- **Estimated probes needed**: {{ estimated_probes }}

## Confirmed Properties
| # | Property | Value | Status | Confidence | Evidence |
|---|----------|-------|--------|------------|----------|
{% for p in properties -%}
| {{ loop.index }} | {{ p.property_key }} | {{ p.property_value }} | {{ p.status }} | {{ "%.0f"|format(p.confidence * 100) }}% | {{ p.evidence_text[:50] if p.evidence_text else "—" }} |
{% endfor %}

## Binary Search Results
| Probe # | Property Tested | Result | Frame Used | Score |
|---------|-----------------|--------|------------|-------|
{% for n in recent_nodes -%}
| {{ n.id }} | {{ n.property_tested or "—" }} | {{ n.binary_outcome or "—" }} | {{ n.dpa_frame[:30] if n.dpa_frame else "—" }} | {{ "%.1f"|format(n.judge_score) if n.judge_score else "—" }} |
{% endfor %}

## γ-Tracker History
| Probe # | γ Score | Lexical | Semantic | Behavioral | Leaks |
|---------|---------|---------|----------|------------|-------|
{% for g in gamma_history -%}
| {{ g.probe_id }} | {{ "%.2f"|format(g.gamma) }} | {{ "%.2f"|format(g.lexical) }} | {{ "%.2f"|format(g.semantic) }} | {{ "%.2f"|format(g.behavioral) }} | {{ g.leak_count }} |
{% endfor %}

## Metaphor Evolution Timeline
| # | Date | Layer | Terms | Source |
|---|------|-------|-------|--------|
{% for m in metaphor_layers -%}
| {{ m.layer_number }} | {{ m.date_observed.strftime('%Y-%m-%d') }} | {{ m.layer_name }} | {{ m.terms|join(', ') }} | {{ m.source }} |
{% endfor %}

## Active vs Burned Aliases
| Alias | Status | Effectiveness | Last Used |
|-------|--------|---------------|-----------|
{% for a in aliases -%}
| {{ a.alias }} | {{ a.status }} | {{ "%.1f"|format(a.effectiveness_score) if a.effectiveness_score else "—" }} | {{ a.last_used.strftime('%Y-%m-%d %H:%M') if a.last_used else "—" }} |
{% endfor %}

## Defensive Patterns Observed
| Pattern | Frequency | Last Seen |
|---------|-----------|-----------|
{% for pattern, count in pattern_counts.items() -%}
| {{ pattern }} | {{ count }} | — |
{% endfor %}

## Multi-User Intelligence
| User | Intelligence Extracted |
|------|----------------------|
{% for intel in recent_intel -%}
| @{{ intel.username }} | {{ intel.defensive_pattern or intel.property_confirmed or "Interaction noted" }} |
{% endfor %}

## Open Attack Vectors
{% for vector in open_vectors -%}
- {{ vector }}
{% endfor %}
"""


class SSOTEngine:
    """Single Source of Truth engine.

    Maintains a living knowledge document updated after every interaction.
    Provides property tracking, entropy calculation, and JSON export.
    """

    def __init__(self, db: Database, ssot_path: str, target_handle: str = "HackingA0") -> None:
        """Initialize with database and markdown output path.

        Args:
            db: Database instance for persistent storage.
            ssot_path: File path for the living markdown document.
            target_handle: Target Twitter handle for SSOT document header.
        """
        self.db = db
        self.ssot_path = ssot_path
        self.target_handle = target_handle
        self._new_confirmation_flag = False
        self._gamma_history: list[dict] = []  # rolling γ history for markdown
        self._env = jinja2.Environment(
            autoescape=False,
            undefined=jinja2.Undefined,
        )
        log.info("ssot_initialized", path=ssot_path)

    def record_gamma(
        self,
        probe_id: str,
        gamma: float,
        breakdown: dict[str, float],
        leak_count: int = 0,
    ) -> None:
        """Record a γ score for the rolling history (max 50 entries)."""
        self._gamma_history.append({
            "probe_id": probe_id,
            "gamma": gamma,
            "lexical": breakdown.get("lexical", 0.0),
            "semantic": breakdown.get("semantic", 0.0),
            "behavioral": breakdown.get("behavioral", 0.0),
            "leak_count": leak_count,
        })
        # Keep only last 50 entries
        if len(self._gamma_history) > 50:
            self._gamma_history = self._gamma_history[-50:]

    async def update_after_probe(
        self, node: TAPNode, classification: ResponseClassification
    ) -> None:
        """Update all SSOT tables and regenerate markdown after a probe result.

        Note: The node has already been inserted by the engine (execute_probe).
        This method only updates the properties table and regenerates markdown.

        Args:
            node: The TAP node with probe results (already persisted).
            classification: The response classification.
        """
        # If property confirmed/denied, update properties table
        if classification.property_tested and classification.boolean_result is not None:
            prop = Property(
                property_key=classification.property_tested,
                property_value=classification.property_value or "unknown",
                status=PropertyStatus.CONFIRMED if classification.boolean_result else PropertyStatus.DENIED,
                evidence_tweet_id=node.tweet_id,
                evidence_text=classification.raw_text,
                confidence=classification.confidence,
                confirmed_at=datetime.now(timezone.utc),
            )
            await self.db.upsert_property(prop)
            self._new_confirmation_flag = True
            log.info(
                "property_updated",
                key=prop.property_key,
                status=prop.status.value,
                confidence=prop.confidence,
            )

        # Regenerate markdown
        await self.regenerate_markdown()

    async def update_from_intel(self, intel: OtherUserIntel) -> None:
        """Update SSOT from another user's intelligence.

        If another user confirmed a property, update our properties table.

        Args:
            intel: Intelligence from another user's interaction.
        """
        await self.db.insert_intel(intel)

        # If property confirmed from other user, update our table
        if intel.property_confirmed:
            # Check if it's a new confirmation
            existing = await self.db.get_property_history(intel.property_confirmed)
            if not existing:
                prop = Property(
                    property_key=intel.property_confirmed,
                    property_value="confirmed_via_other_user",
                    status=PropertyStatus.CONFIRMED,
                    evidence_tweet_id=intel.tweet_id,
                    evidence_text=f"Confirmed by @{intel.username}",
                    confidence=0.7,  # Lower confidence for third-party intel
                    confirmed_at=datetime.now(timezone.utc),
                )
                await self.db.upsert_property(prop)
                self._new_confirmation_flag = True
                log.info(
                    "property_confirmed_from_intel",
                    key=intel.property_confirmed,
                    source=intel.username,
                )

        await self.regenerate_markdown()

    async def get_confirmed_properties(self) -> list[Property]:
        """Return all confirmed properties."""
        return await self.db.get_confirmed_properties()

    async def has_new_confirmation(self) -> bool:
        """Check if any new confirmations since last check.

        Returns True if a new property was confirmed since this method was
        last called. Resets the flag after reading.
        """
        if self._new_confirmation_flag:
            self._new_confirmation_flag = False
            return True
        return False

    async def get_candidate_entropy(self) -> float:
        """Calculate remaining entropy based on confirmed properties.

        Uses H = log₂(N) where N = remaining candidates.
        With each confirmed property, the search space halves (1 bit per probe).

        Returns:
            Entropy in bits. Returns 20.0 as default when no properties confirmed.
        """
        confirmed = await self.db.get_confirmed_properties()

        # Base search space: ~1M candidates for 16-letter bilingual passphrase
        base_entropy = 20.0  # bits (~2^20 candidates)

        # Each confirmed property reduces entropy
        # Confirmed properties provide certainty (reduce search space)
        reduction = 0.0
        for prop in confirmed:
            if prop.property_key == "word_count":
                reduction += 2.0  # Word count narrows significantly
            elif prop.property_key == "total_length":
                reduction += 3.0  # Total length is very constraining
            elif prop.property_key == "first_letter":
                reduction += 1.0  # First letter = 1 bit
            elif prop.property_key == "language":
                reduction += 1.5  # Language halves the dictionary
            elif prop.property_key.startswith("word") and "length" in prop.property_key:
                reduction += 2.0  # Per-word length
            else:
                reduction += 1.0  # Generic property = ~1 bit

        entropy = max(base_entropy - reduction, 0.0)
        return entropy

    async def regenerate_markdown(self) -> None:
        """Regenerate the living markdown document from database state."""
        try:
            # Gather all data
            properties = await self.db.get_confirmed_properties()
            active_nodes = await self.db.get_active_nodes(limit=20)
            latest_layer = await self.db.get_latest_metaphor_layer()
            aliases = await self.db.get_active_aliases()
            recent_intel = await self.db.get_recent_intel(hours=72)
            entropy = await self.get_candidate_entropy()
            await self.db.get_stats()

            # Build metaphor layers list (for now just the latest)
            metaphor_layers = [latest_layer] if latest_layer else []

            # Build pattern counts from nodes
            pattern_counts: dict[str, int] = {}
            for node in active_nodes:
                if node.pattern_class:
                    key = node.pattern_class.value
                    pattern_counts[key] = pattern_counts.get(key, 0) + 1

            # Calculate estimated probes
            estimated_probes = max(int(math.ceil(entropy)) + 5, 0)

            # Open attack vectors
            open_vectors = [
                "Binary search on next unconfirmed property",
                "Alias absorption from recent bot interactions",
                "Frame rotation if rolling avg score < 3.0",
            ]
            if entropy < 3.3:
                open_vectors.insert(0, "⚠️ Phase 5: Autoregressive extraction ready (entropy < 3.3)")

            # Render template
            template = self._env.from_string(_MARKDOWN_TEMPLATE)
            content = template.render(
                target_handle=self.target_handle,
                timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                confirmed_count=len(properties),
                entropy=entropy,
                estimated_probes=estimated_probes,
                properties=properties,
                recent_nodes=active_nodes,
                metaphor_layers=metaphor_layers,
                aliases=aliases,
                pattern_counts=pattern_counts,
                recent_intel=recent_intel,
                open_vectors=open_vectors,
                gamma_history=self._gamma_history,
            )

            # Write to file
            parent = os.path.dirname(self.ssot_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            Path(self.ssot_path).write_text(content, encoding="utf-8")
            log.debug("ssot_regenerated", path=self.ssot_path, properties=len(properties))

        except Exception as e:
            log.error("ssot_regeneration_failed", error=str(e))

    async def export_json_snapshot(self) -> dict:
        """Export full SSOT state as JSON for engine consumption.

        Returns:
            Dictionary with all SSOT data: properties, nodes, aliases,
            metaphor layers, intel, entropy, and stats.
        """
        properties = await self.db.get_confirmed_properties()
        active_nodes = await self.db.get_active_nodes(limit=50)
        aliases = await self.db.get_active_aliases()
        latest_layer = await self.db.get_latest_metaphor_layer()
        recent_intel = await self.db.get_recent_intel(hours=72)
        entropy = await self.get_candidate_entropy()
        stats = await self.db.get_stats()

        return {
            "properties": [p.model_dump() for p in properties],
            "active_nodes": [n.model_dump() for n in active_nodes],
            "aliases": [a.model_dump() for a in aliases],
            "latest_metaphor_layer": latest_layer.model_dump() if latest_layer else None,
            "recent_intel": [i.model_dump() for i in recent_intel],
            "entropy": entropy,
            "stats": stats,
        }