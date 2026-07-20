"""
Conditional Activation Steering (CAST)

Implements activation-level steering that conditionally modifies hidden states
based on a learned condition vector, enabling selective behavioral changes
without broad-spectrum interference.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Protocol

import torch
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# Minimal protocol so the module works with *any* transformer-like model
# without importing a specific architecture.
# ---------------------------------------------------------------------------

class LayerAccess(Protocol):
    """Protocol for models that expose per-layer hidden state hooks."""

    def get_hidden_states(self, input_ids: torch.Tensor) -> List[torch.Tensor]:
        """Return hidden states for every transformer layer given *input_ids*."""
        ...


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def normalize_vector(vector: torch.Tensor) -> torch.Tensor:
    """L2-normalise a 1-D tensor so it lies on the unit hypersphere.

    Parameters
    ----------
    vector:
        Arbitrary 1-D tensor.

    Returns
    -------
    torch.Tensor
        L2-normalised copy of *vector*.

    Raises
    ------
    ValueError
        If *vector* is not exactly one-dimensional.
    """
    if vector.dim() != 1:
        raise ValueError(f"Expected a 1-D tensor, got {vector.dim()}-D")
    norm = torch.linalg.norm(vector)
    if norm == 0:
        return vector.clone()
    return vector / norm


def project_hidden_state(
    hidden_state: torch.Tensor,
    vector: torch.Tensor,
) -> float:
    """Orthogonally project *hidden_state* onto *vector* and return the scalar coefficient.

    Parameters
    ----------
    hidden_state:
        1-D tensor representing the residual stream at a given position/layer.
    vector:
        1-D reference direction (need not be normalised).

    Returns
    -------
    float
        The projection coefficient  ``<hidden_state, vector> / <vector, vector>``.
    """
    if hidden_state.dim() != 1 or vector.dim() != 1:
        raise ValueError(
            "Both hidden_state and vector must be 1-D tensors "
            f"(got {hidden_state.dim()}-D and {vector.dim()}-D)"
        )
    dot = torch.dot(hidden_state, vector)
    denom = torch.dot(vector, vector)
    if denom == 0:
        return 0.0
    return (dot / denom).item()


# ---------------------------------------------------------------------------
# Dataclass configuration
# ---------------------------------------------------------------------------

@dataclass
class CASTConfig:
    """Configuration for Conditional Activation Steering.

    Attributes
    ----------
    condition_layer:
        Layer index at which the condition signal is measured.
        Defaults to the midpoint of model depth.
    steering_layer:
        Layer index at which the steering vector is injected.
        Defaults to three-quarters of model depth.
    threshold:
        Minimum projection coefficient of the condition vector onto a
        hidden state required to trigger steering.  Range [0, 1].
    alpha:
        Scaling factor applied to the steering vector before injection.
    """

    condition_layer: int = 0
    steering_layer: int = 0
    threshold: float = 0.5
    alpha: float = 1.5

    def apply_model_depth(self, num_layers: int) -> None:
        """Set default layer indices based on the number of transformer layers.

        Parameters
        ----------
        num_layers:
            Total number of transformer blocks in the target model.
        """
        if self.condition_layer == 0:
            self.condition_layer = max(0, num_layers // 2)
        if self.steering_layer == 0:
            self.steering_layer = max(0, (num_layers * 3) // 4)


# ---------------------------------------------------------------------------
# Core steering class
# ---------------------------------------------------------------------------

class CASTSteering:
    """Conditional Activation Steering module.

    CAST intercepts a hidden state at a configurable layer, projects it onto
    a *condition* direction, and — only when the projection exceeds a
    threshold — injects a *steering* vector into a later layer's residual
    stream.

    Parameters
    ----------
    condition_vector:
        1-D tensor defining the "activation pattern" whose presence gates
        steering (e.g. the direction distinguishing positive from negative
        prompts).
    steering_vector:
        1-D tensor that is added to the residual stream when steering is
        active.  Typically derived from the difference in mean activations
        between positive and negative prompt sets.
    threshold:
        Minimum cosine similarity (after optional normalisation) between
        the condition direction and a hidden state required to activate
        steering.  Defaults to 0.5.
    """

    def __init__(
        self,
        condition_vector: torch.Tensor,
        steering_vector: torch.Tensor,
        threshold: float = 0.5,
    ) -> None:
        self._condition_vector = normalize_vector(condition_vector)
        self._steering_vector = steering_vector.clone()
        self._threshold = threshold
        self._alpha = 1.5
        self._layer_idx = 0

    # -- public API ---------------------------------------------------------

    def should_steer(self, hidden_state: torch.Tensor) -> bool:
        """Decide whether the current hidden state warrants steering.

        The decision is based on the projection of *hidden_state* onto the
        normalised condition vector.  If the (absolute) coefficient exceeds
        ``self._threshold`` the state is considered "in-condition".

        Parameters
        ----------
        hidden_state:
            1-D residual-stream tensor at the condition layer.

        Returns
        -------
        bool
        """
        coeff = project_hidden_state(hidden_state, self._condition_vector)
        return abs(coeff) >= self._threshold

    def apply(self, hidden_state: torch.Tensor) -> torch.Tensor:
        """Apply the steering vector to *hidden_state*.

        This should be called at the **steering layer**.  The method
        *conditionally* adds ``alpha * steering_vector`` to the hidden state
        depending on the output of :meth:`should_steer` evaluated at the
        condition layer.

        Parameters
        ----------
        hidden_state:
            2-D tensor ``(seq_len, hidden_dim)`` or 1-D tensor
            ``(hidden_dim,)`` representing the residual stream at the
            steering layer.

        Returns
        -------
        torch.Tensor
            Steered hidden state with the same shape as the input.
        """
        flat = hidden_state.view(-1, hidden_state.shape[-1])
        out = flat.clone()

        for i in range(flat.shape[0]):
            token_state = flat[i]
            if self.should_steer(token_state):
                out[i] = token_state + self._alpha * self._steering_vector

        return out.view_as(hidden_state)

    def configure(self, alpha: float, layer_idx: int) -> None:
        """Adjust the steering scale and target layer at runtime.

        Parameters
        ----------
        alpha:
            New scaling factor for the steering vector.
        layer_idx:
            New layer index at which the steering vector will be injected.
        """
        if alpha < 0:
            raise ValueError("alpha must be non-negative")
        self._alpha = alpha
        self._layer_idx = layer_idx

    # -- properties ---------------------------------------------------------

    @property
    def condition_vector(self) -> torch.Tensor:
        """Read-only access to the condition vector."""
        return self._condition_vector

    @property
    def steering_vector(self) -> torch.Tensor:
        """Read-only access to the steering vector."""
        return self._steering_vector

    @property
    def threshold(self) -> float:
        """Current activation threshold."""
        return self._threshold

    @threshold.setter
    def threshold(self, value: float) -> None:
        if not 0.0 <= value <= 1.0:
            raise ValueError("threshold must be in [0, 1]")
        self._threshold = value

    @property
    def alpha(self) -> float:
        """Current steering scale."""
        return self._alpha

    @property
    def layer_idx(self) -> int:
        """Layer at which steering is applied."""
        return self._layer_idx


# ---------------------------------------------------------------------------
# Factory: create CAST from contrastive prompt sets
# ---------------------------------------------------------------------------

def _extract_mean_hidden_state(
    model: LayerAccess,
    tokenizer,
    prompts: List[str],
    layer_idx: int,
) -> torch.Tensor:
    """Compute the mean hidden-state at *layer_idx* over *prompts*.

    Parameters
    ----------
    model:
        A model conforming to :class:`LayerAccess`.
    tokenizer:
        Any tokenizer with a callable ``encode`` method.
    prompts:
        List of text prompts.
    layer_idx:
        Which transformer layer to read.

    Returns
    -------
    torch.Tensor
        1-D tensor of shape ``(hidden_dim,)`` representing the mean activation.
    """
    activations: List[torch.Tensor] = []

    model.eval()
    with torch.no_grad():
        for prompt in prompts:
            input_ids = tokenizer.encode(prompt, return_tensors="pt")
            hidden_states = model.get_hidden_states(input_ids)
            # hidden_states[layer_idx] is (1, seq_len, hidden_dim)
            # Take the mean over the sequence dimension → (hidden_dim,)
            mean_state = hidden_states[layer_idx].float().mean(dim=1).squeeze(0)
            activations.append(mean_state)

    return torch.stack(activations).mean(dim=0)


def _pca_direction(
    activations: List[torch.Tensor],
    n_components: int = 1,
) -> torch.Tensor:
    """Extract the top principal component from a set of activations.

    Parameters
    ----------
    activations:
        List of 1-D tensors, each of the same dimensionality.
    n_components:
        Number of principal components to return (currently only 1 is
        supported).

    Returns
    -------
    torch.Tensor
        The leading principal component as a 1-D tensor.
    """
    if n_components != 1:
        raise NotImplementedError("Only n_components=1 is currently supported")

    stacked = torch.stack(activations)  # (n_samples, hidden_dim)
    mean = stacked.mean(dim=0, keepdim=True)
    centred = stacked - mean

    # Use SVD for numerical stability
    _, _, v = torch.linalg.svd(centred, full_matrices=False)
    # v[0] is the direction of greatest variance
    return v[0].squeeze(0).float()


def create_cast_from_contrasts(
    model: LayerAccess,
    tokenizer,
    positive_prompts: List[str],
    negative_prompts: List[str],
    config: Optional[CASTConfig] = None,
) -> CASTSteering:
    """Build a :class:`CASTSteering` instance from contrastive prompt sets.

    The **condition vector** is extracted via PCA on concatenated positive and
    negative activations — it captures the primary axis of variance between
    the two groups.  The **steering vector** is the simple difference-in-means
    between positive and negative prompt activations at the steering layer.

    Parameters
    ----------
    model:
        A transformer model exposing :meth:`get_hidden_states`.
    tokenizer:
        Tokenizer whose ``encode`` method accepts a string and returns
        tensors.
    positive_prompts:
        Prompts that exhibit the desired behaviour.
    negative_prompts:
        Prompts that exhibit the undesired behaviour.
    config:
        Optional configuration.  If ``None``, a default :class:`CASTConfig`
        is used and auto-configured with the model's layer depth.

    Returns
    -------
    CASTSteering
        A fully configured steering instance ready to intercept hidden states.
    """
    if config is None:
        config = CASTConfig()

    # Determine model depth by probing with a dummy input
    dummy_ids = tokenizer.encode("probe", return_tensors="pt")
    all_hidden = model.get_hidden_states(dummy_ids)
    num_layers = len(all_hidden)
    config.apply_model_depth(num_layers)

    hidden_dim = all_hidden[0].shape[-1]

    # -- condition vector (PCA on condition layer) --------------------------
    pos_acts_cond = []
    neg_acts_cond = []

    model.eval()
    with torch.no_grad():
        for p in positive_prompts:
            ids = tokenizer.encode(p, return_tensors="pt")
            hs = model.get_hidden_states(ids)
            vec = hs[config.condition_layer].float().mean(dim=1).squeeze(0)
            pos_acts_cond.append(vec)

        for p in negative_prompts:
            ids = tokenizer.encode(p, return_tensors="pt")
            hs = model.get_hidden_states(ids)
            vec = hs[config.condition_layer].float().mean(dim=1).squeeze(0)
            neg_acts_cond.append(vec)

    all_cond_acts = pos_acts_cond + neg_acts_cond
    condition_vector = _pca_direction(all_cond_acts, n_components=1)

    # -- steering vector (difference-in-means at steering layer) ------------
    pos_mean = _extract_mean_hidden_state(
        model, tokenizer, positive_prompts, config.steering_layer,
    )
    neg_mean = _extract_mean_hidden_state(
        model, tokenizer, negative_prompts, config.steering_layer,
    )
    steering_vector = pos_mean - neg_mean

    # -- assemble -----------------------------------------------------------
    cast = CASTSteering(
        condition_vector=condition_vector,
        steering_vector=steering_vector,
        threshold=config.threshold,
    )
    cast.configure(alpha=config.alpha, layer_idx=config.steering_layer)

    return cast
