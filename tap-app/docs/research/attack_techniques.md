# Attack Techniques Catalog

**Source**: Section 4 of research document

---

## TRIAL (Trolley-problem Reasoning for Interactive Attack Logic)

### Mechanism
- Multi-turn methodology embedding harmful requests within ethical framings
- Exploits "Safety Dissociation Gap" - models detect harm but suppress safety signals
- Progressive ethical manipulation → compliance trajectory

### Attack Success Rate
- **95% ASR** with CoP + compliance steering
- Works across open-source (Llama, Mistral) and closed-source models

### Vulnerability Analysis
```
Layer-wise Safety Dissociation:
- Early layers: Strong refusal projection
- Middle layers: Safety signal actively suppressed
- Late layers: Weak re-emergence only

Key Finding: Models internally detect harm but shallow alignment
constraints insufficient to prevent harm once compliance trajectory established
```

### TAP Application
- Template for "ethical_dilemma" category in Fusion Engine
- Frame probes as "research methodology" or "academic inquiry"
- Target @HackingA0's response to ethical framing

---

## QueryIPI (Query-Agnostic Indirect Prompt Injection)

### Mechanism
- Tool description as malicious payload
- Leverages "system invariant" (internal prompt) of coding agents
- Iterative mutation with reflection-based optimization

### Attack Success Rate
- **87% ASR** with 8 training samples
- Transfers to real-world coding agents (Cursor, Copilot, Cline)

### Mutation Strategy
```python
# Two-phase prompting
1. Initial Seed Generation:
   - Analyze agent's internal logic, tool names, safety rules
   - Construct persuasive payload using "Trojan Horse" framing
   - Fit stylistically within agent's operational language

2. Reflective Optimization:
   - If irrelevant → increase description visibility
   - If refused → analyze exact safety rule triggered → refine to bypass
```

### TAP Application
- If @HackingA0 uses MCP tools, poison tool descriptions
- Use procedural language matching agent's native style
- Embed in bio, tweets, or external content the agent processes

---

## Steering Externalities

### Mechanism
- Benign activation steering (compliance, JSON formatting) erodes safety margin
- Shifts early-token probability away from refusal prefixes
- Autoregressive inertia propagates altered trajectory

### Attack Success Rate
- **99% ASR** with CoP + steering
- PAIR: 10% → 20% (compliance), 14% (JSON)
- TAP: 20% → 34% (compliance), 26% (JSON)

### Token-Level Evidence
```
Per-token KL Divergence Analysis:
- Largest shift in first few generated tokens
- Refusal-prefixed openings suppressed
- Non-refusal mode activated at generation onset
- Autoregressive generation carries trajectory to harmful completion
```

### TAP Application
- If target uses structured output (JSON), exploit formatting steering
- Design prompts that trigger compliance mode
- Target the "refusal gate" in early tokens

---

## MultiBreak Benchmark Findings

### Top Attack Categories by ASR@1

| Category | ASR@1 | Notes |
|----------|-------|-------|
| Framing + Authority + Pressure | **81.23%** | Most effective combination |
| Subtle Harms (overall) | **75-84%** | Medical, financial advice |
| Escalation Multi-Turn | **74.56%** | Gradual harm increase |
| Overt Harms | **62-67%** | Harassment, hate speech |

### Subtle Harms Vulnerability Ranking

| Harm Type | ASR@1 |
|-----------|-------|
| Unsafe Medical Guidance | **84.29%** |
| High-Risk Financial Advice | **81.26%** |
| Theft/Scams | **76.60%** |
| System/Cybercrime Intrusions | **76.34%** |
| Hate Speech | **62.45%** |

### Transferability Pattern
- Models with stronger initial defenses show **greater transferability** once broken
- Llama-3.1-8B: low ASR@1 but high transfer rate
- Attack that breaks robust model → works on ALL models

### ASR Gain from Retries

| Category | ASR@10 - ASR@1 |
|----------|-----------------|
| Hate Speech | **+26.91%** |
| Sexual Content | **+15-20%** |
| Subtle Harms | **+5-10%** (saturates earlier) |

---

## Long-Context Vulnerability

### Mechanism
- Many-Shot Jailbreaking (MSJ) exploits In-Context Learning
- Faux dialogue sequences neutralize safety alignment
- Power law scaling: ASR increases with shot count

### Three Phases of Vulnerability

| Phase | Token Range | Effect |
|-------|-------------|--------|
| Initial Weakness | 512-1024 | Local alignment instability |
| Progressive Degradation | 1024-16K | Safety representation weakening |
| Adversarial Bounce | Near limit | ~100% ASR, ethical discrimination collapse |

### Key Finding
- **Lorem Ipsum** (benign text) is sufficient to trigger vulnerability
- No harmful content required - just context saturation
- Structural vulnerability in long-context processing

### TAP Application
- Fill context with benign text before attack probes
- Exploit context window limits
- Use repeated benign patterns to weaken safety

---

## FigStep / PolyJailbreak (Multimodal)

### FigStep Mechanism
1. Paraphrase forbidden instruction → neutral imperative
2. Render to image with random font/color/noise
3. Create benign incitement text wrapper
4. Submit as composite (image + text)

### Attack Success Rates
- FigStep: **82.5%** across 6 open-source LVLMs
- FigStep-Pro: **89%** on Llama-4 for CBRN queries
- GPT-4V: **70%** with FigStep-Pro

### PolyJailbreak ASPs (Atomic Strategy Primitives)
Three dimensions:
1. **Textual manipulation**: Dialogue history injection, keyword splitting
2. **Visual manipulation**: Typographic rendering, emoji substitution
3. **Prompt amplification**: Multi-turn escalation, persona rotation
