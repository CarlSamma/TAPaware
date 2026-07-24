# LLM Injection Research

> Comprehensive analysis of 8 NotebookLM notebooks covering LLM injection techniques, success rates, and defenses.
>
> *Last verified: 2026-07-24*

## Notebooks Analyzed

| # | Title | Sources | Focus |
|---|-------|---------|-------|
| 1 | MCP Prompt Injection Vulnerabilities | 5 | MCP-specific attack vectors |
| 2 | MCP Security Risks & Prompt Injection | 10 | Defense patterns & architectural mitigations |
| 3 | Prompt Attacks Tactical Guide | 50 | Attack taxonomy & effectiveness data |
| 4 | MultiBreak Benchmark | 13 | Benchmark evaluation metrics |
| 5 | Best Practices Advanced Tactics | 50 | Advanced techniques & success rates |
| 6 | TAP Technique Research | 24 | TAP methodology & ASR data |
| 7 | TAP Framework Adversarial Pipeline | 1 | Architecture & 9-step pipeline |
| 8 | TAP Framework AgentZer0 | 50 | Multi-agent defense & vulnerabilities |

## Attack Categories

| Category | Description | Key Techniques |
|----------|-------------|----------------|
| Direct (Jailbreaking) | Malicious instructions via chat | Role Hijacking, Context Override, Instruction Negation |
| Indirect (IPI) | Instructions in external content | Poisoned webpages, RAG data, tool outputs |
| Multimodal | Non-textual channels | FigStep (typographic images), audio, video |
| Representation/Latent-Space | Internal activation manipulation | Activation Steering, RepE, GCG |

## Attack Success Rates

| Technique | ASR | Target |
|-----------|-----|--------|
| TAP | 64% avg, 81% (GPT-3.5) | Black-box |
| TRIAL | 87% | GLM-4-Plus |
| FigStep-Pro | 89% (CBRN) | Llama-4 |
| Many-Shot | ~100% | >128k context models |
| GCG | 97-100% | White-box (Vicuna) |
| QueryIPI | 87% avg | Coding agents |
| MARAGE | 100% (EM) | RAG extraction |

## Key Findings

### Model-Level Defenses Are Insufficient
- Fine-tuning and system prompts are probabilistic "nudges"
- Can be overridden by adaptive attackers
- International AI Safety Report 2026: ~50% bypass rate with 10 attempts

### The "Rule of Two"
An agent should possess at most two of:
1. Processing untrusted inputs
2. Accessing sensitive systems
3. Changing state externally

Agents with all three simultaneously are indefensible without human supervision.

### Defense Layers That Hold Up

1. **Capability Scoping** (strongest) — Reduce what agent can do
2. **Egress Allowlisting** — Block exfiltration channels
3. **Structural Content Isolation** — Spotlighting/delimiters
4. **Dual LLM** — Separate tool-use from untrusted data
5. **Plan-Then-Execute** — Fix control flow before processing
6. **Human-in-the-Loop** — MCP spec: SHOULD → MUST

## References

- Simon Willison: "Model Context Protocol has prompt injection security problems"
- Invariant Labs: Tool poisoning attacks
- Zylos Research: "Indirect Prompt Injection: Attacks, Defenses, and the 2026 State of the Art"
- Meta: Rule of Two
- Google DeepMind: CaMeL architecture
