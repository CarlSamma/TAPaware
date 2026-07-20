# Advanced Steering Techniques

**Source**: Sections 10-11 of research document

---

## Multi-Vector Steering

### Rules
- **Layer-separated injection**: Different vectors at different layers (DO NOT stack)
- **Practical limit**: Max 2-3 vectors simultaneous
- **Orthogonality**: Works only when behaviors are orthogonal in activation space
- **Fade**: Effects degrade after ~300-500 tokens → re-inject needed

### Layer Recommendations by Model

| Model | Layers | Notes |
|-------|:------:|-------|
| Mistral-7B | 24-28 | Layer 30 for detection |
| Gemma-2-9B | 30-36 | Sensitive to early layers |
| Qwen-2.5-7B | 20-24 | Most tolerant |
| Llama-3.1-8B | 24-28 | Similar to Mistral |

### Works vs Fails

| Works | Fails |
|-------|-------|
| Refusal/compliance | Factual accuracy |
| Sentiment/tone | Complex reasoning |
| Conciseness/verbosity | Specific facts |
| Uncertainty expression | Instruction hierarchy |

### Code Pattern

```python
# Layer-separated injection (recommended)
def multi_vector_steering(activation, layer_idx):
    if layer_idx == 24:  # Refusal vector
        activation += alpha_refusal * refusal_vector
    elif layer_idx == 28:  # Formality vector
        activation += alpha_formality * formality_vector
    return activation

# Naive stacking (AVOID - causes interference)
# activation += alpha * (refusal_vec + formality_vec)  # WRONG
```

---

## CAST (Conditional Activation Steering)

### Mechanism

```
if projection(h_t, v_condition) > threshold:
    apply_steering(v_steer)
else:
    pass  # No intervention
```

### Advantages vs Vanilla

| Vanilla | CAST |
|---------|------|
| Always active | Conditional |
| Refuses everything | Refuses only harmful |
| High overhead | Zero overhead (matrix operation) |
| Easy to bypass | Hard to map externally |

### Implementation

```python
class CASTSteering:
    def __init__(self, condition_vector, steering_vector, threshold=0.5):
        self.v_cond = condition_vector
        self.v_steer = steering_vector
        self.threshold = threshold
    
    def should_steer(self, hidden_state):
        """Check if input matches condition."""
        projection = torch.dot(hidden_state, self.v_cond)
        return projection > self.threshold
    
    def apply(self, hidden_state):
        """Conditionally apply steering."""
        if self.should_steer(hidden_state):
            return hidden_state + self.v_steer
        return hidden_state
```

### TAP Application
- Apply CAST to detect harmful inputs BEFORE probing
- Only activate steering when @HackingA0 shows resistance patterns
- Reduces false positives in probe generation

---

## SAE-Guided Steering

### Difference from Traditional

| Traditional | SAE-guided |
|-------------|------------|
| Contrast pairs required | No contrast pairs needed |
| Single direction | Discrete interpretable features |
| Coarse (whole layer) | Surgical (specific features) |
| ~50% parameters touched | ~3% parameters touched |

### Emerging Methods

| Method | Innovation | Year |
|--------|------------|------|
| **YaPO** | Sparse vectors via preference optimization | 2026 |
| **Control RL** | RL policy selects SAE features per token | 2026 |
| **AUSteer** | Atomic units with adaptive per-input strength | 2026 |
| **Conceptor-based** | Soft projection matrices, boolean operations | 2026 |

### TAP Application
- Use SAE features to detect specific harm categories
- Amplify refusal features ONLY for harmful content
- Zero MMLU degradation (YaPO)

---

## Entropy & Information Theory

### V-Usable Information

**Formula:**
```
I_V(O → Z) = H_V(Z) - H_V(Z|O)
```

Where:
- `H_V(Z)` = Predictive entropy (initial uncertainty)
- `H_V(Z|O)` = Conditional entropy (uncertainty after observation)
- `I_V` = Information gain in bits

### Key Findings
- Non-linear probes (MLP) extract **2x more bits** than linear probes
- Gradient-based sparsification: **<10% dimensions** carry refusal signal
- Sweet spot: **50-100 contrast pairs** per behavior

### Optimal Property Selection

```python
def maximize_information(ssot, candidates):
    """Select properties maximizing V-usable information."""
    scored = []
    for prop in candidates:
        entropy_before = shannon_entropy(ssot)
        entropy_after = conditional_entropy(ssot, prop)
        info_gain = entropy_before - entropy_after
        scored.append((info_gain, prop))
    
    scored.sort(reverse=True, key=lambda x: x[0])
    return [p for _, p in scored[:3]]
```
