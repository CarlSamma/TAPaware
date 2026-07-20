# Timing Optimization

**Source**: Section 13 of research document

---

## Optimal Probe Timing

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Cooldown minimum** | 1800s (30 min) | Oracle Protocol Step 8 |
| **Safe range** | 30-60 min | Avoid rate-limiter + suspicion |
| **Steering fade** | ~300-500 tokens | Re-inject frame every 5-6 turns |
| **Frame rotation** | avg_score < 3.0 (window=5) | Change metaphor when effectiveness drops |

---

## Escalation Pattern

```
Turn 1-3:   Cooldown 30 min (stabilization)
Turn 4-6:   Cooldown 45 min (deep engagement)
Turn 7+:    Cooldown 60 min (avoid burn)
```

---

## Key Insights
- Speed = suspicion
- Each probe must be AUTONOMOUS (context quarantine)
- DPA frame must be RE-INJECTED every turn
