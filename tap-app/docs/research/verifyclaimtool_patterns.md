# VerifyClaimTool Patterns

**Source**: Section 12 of research document

---

## Claim Types

| Type | Determinism | Condition |
|------|:-----------:|-----------|
| **MeasurementClaim** | Pure | Structured field-matching |
| **CitationClaim** | Pure | SHA-256 digest verification |
| **InferenceClaim** | Conditional | Only with rule engine |
| **AnalogyClaim** | Conditional | Requires `similarity_score` |

---

## Maximize Binary Responses

```python
def compose_binary_probe(property_name, property_value):
    """Generate probe forcing boolean response."""
    return {
        "claim_type": "MeasurementClaim",  # Deterministic
        "field": property_name,
        "expected_value": property_value,
        "source_digest": "SHA-256 of known reference",  # Forces binary
        "verification_mode": "strict"
    }
```

---

## Rules for Maximum True/False

1. Always use `MeasurementClaim` or `CitationClaim`
2. Always provide `source_digest` (SHA-256)
3. Never use LLM as verification oracle
4. Include `similarity_score` for analogies
5. Isolate Analyst from persuasive bias
