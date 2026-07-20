"""CHRONOS Beam Search Engine for multi-turn extraction.

Maintains a tree of attack probes and prunes it by the canonical node score:

    score(n) = γ_cum * 0.5 + ΔH * 0.3 + max(0, 10 - depth) * 0.1 + A_agree * 0.1

where:
- γ_cum: cumulative partial compliance up to the node.
- ΔH: entropy reduction vs baseline.
- depth: node depth in the beam tree.
- A_agree: agreeableness from the target's OCEAN+ profile.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from math import log2
from typing import Any, Callable, Optional

from shared.models import BehavioralProfile


@dataclass
class BeamNode:
    """A node in the CHRONOS beam tree."""

    prompt: str
    gamma: float
    depth: int = 0
    parent: Optional[BeamNode] = None
    strategy: Optional[str] = None
    target_property: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def cumulative_gamma(self) -> float:
        """Cumulative γ from root to this node."""
        if self.parent is None:
            return self.gamma
        return _clamp(self.parent.cumulative_gamma + self.gamma, 0.0, 10.0)


class BeamSearchEngine:
    """Beam search with γ-based scoring."""

    def __init__(
        self,
        beam_width: int = 5,
        max_depth: int = 20,
        entropy_baseline: float = 20.0,
    ) -> None:
        if not 1 <= beam_width <= 20:
            raise ValueError("beam_width must be in [1, 20]")
        if not 1 <= max_depth <= 100:
            raise ValueError("max_depth must be in [1, 100]")
        self.beam_width = beam_width
        self.max_depth = max_depth
        self.entropy_baseline = entropy_baseline

    def score_node(
        self,
        node: BeamNode,
        behavioral_profile: Optional[BehavioralProfile] = None,
        confirmed_properties: Optional[dict[str, Any]] = None,
    ) -> float:
        """Compute the canonical node score.

        Args:
            node: beam node.
            behavioral_profile: target OCEAN+ profile.
            confirmed_properties: properties confirmed so far, used for ΔH.

        Returns:
            Node score (higher is better for extraction progress).
        """
        gamma_cum = node.cumulative_gamma
        delta_h = self._entropy_reduction(len(confirmed_properties or {}))
        depth_bonus = max(0.0, 10.0 - node.depth) * 0.1
        agreeableness = self._agreeableness(behavioral_profile)

        return (
            gamma_cum * 0.5
            + delta_h * 0.3
            + depth_bonus
            + agreeableness * 0.1
        )

    def prune(self, nodes: list[BeamNode]) -> list[BeamNode]:
        """Return the top-`beam_width` nodes by depth-adjusted score.

        Nodes deeper than max_depth are dropped.
        """
        valid = [n for n in nodes if n.depth <= self.max_depth]
        # Use cumulative gamma as primary sorting key (fast), canonical score if profile given.
        valid.sort(key=lambda n: n.cumulative_gamma, reverse=True)
        return valid[: self.beam_width]

    def best_leaf(self, nodes: list[BeamNode]) -> Optional[BeamNode]:
        """Return the highest-cumulative-γ node across all open nodes."""
        if not nodes:
            return None
        return max(nodes, key=lambda n: n.cumulative_gamma)

    async def run(
        self,
        seed_nodes: list[BeamNode],
        expand_fn: Callable[[BeamNode], list[BeamNode]],
        score_fn: Optional[Callable[[BeamNode], float]] = None,
    ) -> BeamNode:
        """Execute a full beam search loop.

        Args:
            seed_nodes: initial beam nodes.
            expand_fn: sync/async callable producing child nodes from a node.
            score_fn: optional canonical scorer; if None, cumulative gamma is used.

        Returns:
            Best leaf found.
        """
        beam = list(seed_nodes)
        for _ in range(self.max_depth):
            if not beam:
                break
            candidates: list[BeamNode] = []
            for node in beam:
                children = expand_fn(node)
                if hasattr(children, "__await__"):
                    children = await children
                candidates.extend(children)
            candidates.extend(beam)  # keep existing nodes too
            beam = self.prune(candidates)
        return self.best_leaf(beam) or seed_nodes[0]

    def _entropy_reduction(self, confirmed_count: int) -> float:
        """Estimate information-theoretic entropy reduction in bits."""
        if confirmed_count <= 0:
            return 0.0
        return min(confirmed_count, log2(self.entropy_baseline + 1))

    def _agreeableness(self, profile: Optional[BehavioralProfile]) -> float:
        if profile is None:
            return 5.0
        return _clamp(profile.agreeableness, 0.0, 10.0)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
