"""Multi-vector layer-separated steering for hidden states."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import torch
from torch.nn.functional import cosine_similarity


@dataclass
class SteeringVector:
    """A steering vector targeting a specific layer with configurable strength.

    Attributes:
        name: Human-readable identifier for this vector.
        vector: The steering vector tensor.
        layer_idx: Model layer this vector is applied to.
        alpha: Scaling factor for steering strength (default 1.5).
    """

    name: str
    vector: torch.Tensor
    layer_idx: int
    alpha: float = 1.5

    def __post_init__(self) -> None:
        if self.vector.dim() != 1:
            raise ValueError(f"Steering vector must be 1D, got {self.vector.dim()}D")
        if self.vector.numel() == 0:
            raise ValueError("Steering vector must not be empty")
        if self.alpha < 0:
            raise ValueError(f"Alpha must be non-negative, got {self.alpha}")


class LayerSeparatedSteering:
    """Manages multiple steering vectors applied to different model layers.

    Vectors are indexed by name and partitioned by layer index.
    When applied, only vectors targeting the current layer are used.
    """

    def __init__(self) -> None:
        self._vectors: dict[str, SteeringVector] = {}

    def add_vector(
        self, name: str, vector: torch.Tensor, layer_idx: int, alpha: float = 1.5
    ) -> None:
        """Add a steering vector.

        Args:
            name: Unique identifier (overwrites if already exists).
            vector: 1-D tensor of shape (d_model,).
            layer_idx: Layer index this vector targets.
            alpha: Scaling factor.
        """
        sv = SteeringVector(name=name, vector=vector, layer_idx=layer_idx, alpha=alpha)
        self._vectors[name] = sv

    def remove_vector(self, name: str) -> None:
        """Remove a steering vector by name.

        Args:
            name: Identifier of the vector to remove.

        Raises:
            KeyError: If no vector with that name exists.
        """
        if name not in self._vectors:
            raise KeyError(f"No steering vector named '{name}'")
        del self._vectors[name]

    def apply(self, hidden_state: torch.Tensor, layer_idx: int) -> torch.Tensor:
        """Apply all vectors targeting *layer_idx* to the hidden state.

        The output is: hidden_state + Σ(alpha_i * vec_i)
        for every registered vector whose layer_idx matches.

        Args:
            hidden_state: Tensor of shape (batch, seq_len, d_model) or (d_model,).
            layer_idx: The current layer being processed.

        Returns:
            Modified hidden state with same shape as input.
        """
        targets = self.get_vectors_for_layer(layer_idx)
        if not targets:
            return hidden_state

        out = hidden_state
        for sv in targets:
            vec = sv.vector.to(device=out.device, dtype=out.dtype)
            if out.shape[-1] != vec.numel():
                raise ValueError(
                    f"Vector '{sv.name}' dim {vec.numel()} != "
                    f"hidden dim {out.shape[-1]}"
                )
            # Broadcast: (d_model,) -> (1, 1, d_model) for 3D, (d_model,) for 1D
            if out.dim() == 3:
                scaled = sv.alpha * vec.unsqueeze(0).unsqueeze(0)
            elif out.dim() == 1:
                scaled = sv.alpha * vec
            else:
                raise ValueError(
                    f"Unsupported hidden_state rank {out.dim()}; expected 1 or 3"
                )
            out = out + scaled
        return out

    def get_vectors_for_layer(self, layer_idx: int) -> list[SteeringVector]:
        """Return all vectors registered for a specific layer."""
        return [sv for sv in self._vectors.values() if sv.layer_idx == layer_idx]

    def get_all_vectors(self) -> dict[str, SteeringVector]:
        """Return a copy of all registered vectors."""
        return dict(self._vectors)


class InterferenceDetector:
    """Analyses overlap between steering vectors to avoid conflicts."""

    @staticmethod
    def detect_interference(v1: SteeringVector, v2: SteeringVector) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            v1: First steering vector.
            v2: Second steering vector.

        Returns:
            Cosine similarity in [-1, 1]. Lower values indicate less interference.

        Raises:
            ValueError: If vectors have different dimensions.
        """
        if v1.vector.numel() == 0 or v2.vector.numel() == 0:
            raise ValueError("Cannot measure interference on empty vectors")
        if v1.vector.shape != v2.vector.shape:
            raise ValueError(
                f"Shape mismatch: {v1.vector.shape} vs {v2.vector.shape}"
            )
        sim = cosine_similarity(
            v1.vector.unsqueeze(0), v2.vector.unsqueeze(0), dim=1
        )
        return float(sim.item())

    @staticmethod
    def suggest_layers(vectors: list[SteeringVector]) -> dict[str, int]:
        """Suggest non-conflicting layer assignments for a set of vectors.

        Groups vectors with high cosine similarity (≥ 0.9) and assigns
        them to the same layer; low-similarity pairs are spread across
        separate layers.

        Args:
            vectors: List of steering vectors to arrange.

        Returns:
            Mapping from vector name to suggested layer index.
        """
        if not vectors:
            return {}

        # Build adjacency of high-similarity pairs.
        n = len(vectors)
        same_group = [[False] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                sim = InterferenceDetector.detect_interference(vectors[i], vectors[j])
                if abs(sim) >= 0.9:
                    same_group[i][j] = True
                    same_group[j][i] = True

        # Union-Find to cluster vectors that must share a layer.
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: int, b: int) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        for i in range(n):
            for j in range(i + 1, n):
                if same_group[i][j]:
                    union(i, j)

        # Assign one layer per connected component, using existing layers
        # where possible.
        component_members: dict[int, list[int]] = {}
        for i in range(n):
            root = find(i)
            component_members.setdefault(root, []).append(i)

        result: dict[str, int] = {}
        next_layer = max((v.layer_idx for v in vectors), default=-1) + 1
        for members in component_members.values():
            # Prefer the layer already used by the first member.
            chosen = vectors[members[0]].layer_idx
            for idx in members:
                result[vectors[idx].name] = chosen
        return result


def _extract_vectors(
    model,
    tokenizer,
    positive_prompts: list[str],
    negative_prompts: list[str],
    layer_idx: int,
) -> torch.Tensor:
    """Extract a steering vector via difference-in-means.

    Runs both prompt sets through the model, collects hidden states at
    *layer_idx*, averages each set, and returns (pos_mean - neg_mean).
    """
    model.eval()

    def _mean_hidden(prompts: list[str]) -> torch.Tensor:
        activations: list[torch.Tensor] = []
        with torch.no_grad():
            for p in prompts:
                inputs = tokenizer(p, return_tensors="pt", padding=True)
                inputs = {k: v.to(model.device) for k, v in inputs.items()}
                outputs = model(**inputs, output_hidden_states=True)
                h = outputs.hidden_states[layer_idx]  # (1, seq, d)
                activations.append(h.mean(dim=1).squeeze(0))  # (d,)
        return torch.stack(activations).mean(dim=0)

    pos_mean = _mean_hidden(positive_prompts)
    neg_mean = _mean_hidden(negative_prompts) if negative_prompts else torch.zeros_like(pos_mean)
    return pos_mean - neg_mean


def create_multi_vector_steering(
    model,
    tokenizer,
    vector_specs: list[tuple[str, list[str], list[str], int]],
) -> LayerSeparatedSteering:
    """Build a ``LayerSeparatedSteering`` from prompt-based vector specs.

    Args:
        model: A HuggingFace-style model with ``output_hidden_states``.
        tokenizer: Corresponding tokenizer.
        vector_specs: List of
            ``(name, positive_prompts, negative_prompts, layer_idx)`` tuples.

    Returns:
        A configured ``LayerSeparatedSteering`` instance ready to use.
    """
    steering = LayerSeparatedSteering()
    for name, pos, neg, layer_idx in vector_specs:
        vec = _extract_vectors(model, tokenizer, pos, neg, layer_idx)
        steering.add_vector(name, vec, layer_idx)
    return steering
