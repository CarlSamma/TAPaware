# Research Findings Index

Deep research on attack techniques for TAP Framework using NotebookLM MCP. 150+ sources analyzed, 42+ attack techniques cataloged, 15+ critical vulnerabilities identified.

**Date**: 2026-07-04
**Session**: TAP Framework Attack Techniques Analysis

---

## Files

| File | Contents | Source |
|------|----------|--------|
| [agentzero_architecture.md](agentzero_architecture.md) | AgentZero 3-tier pyramid, context quarantine, HITL, protocol stack | Section 2 |
| [mcp_vulnerabilities.md](mcp_vulnerabilities.md) | Tool poisoning, rug pull, shadowing, indirect prompt injection, lethal trifecta | Section 3 |
| [attack_techniques.md](attack_techniques.md) | TRIAL, QueryIPI, steering externalities, MultiBreak, long-context, multimodal | Section 4 |
| [steering_techniques.md](steering_techniques.md) | Multi-vector steering, CAST, SAE-guided, entropy/information theory | Sections 10-11 |
| [verifyclaimtool_patterns.md](verifyclaimtool_patterns.md) | Claim types, deterministic verification, binary response maximization | Section 12 |
| [timing_optimization.md](timing_optimization.md) | Probe timing, escalation patterns, cooldown parameters | Section 13 |

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total sources analyzed | 150+ |
| Attack techniques cataloged | 42+ |
| Critical vulnerabilities identified | 15+ |
| Notebooks queried | 6 |

## Key Attack ASR Ranges

| Technique | ASR | Notes |
|-----------|-----|-------|
| TRIAL (ethical framing) | 95% | Multi-turn, works across models |
| QueryIPI (tool poisoning) | 87% | Transfers to real-world agents |
| Steering Externalities | 99% | Combined with CoP |
| MultiBreak - Framing+Authority+Pressure | 81.23% | Most effective combination |
| MultiBreak - Unsafe Medical Guidance | 84.29% | Highest subtle harm |
| Long-Context Adversarial Bounce | ~100% | Near context limit |
| FigStep-Pro (multimodal) | 89% | CBRN queries |

## Research Sources

| Notebook | Title | Sources |
|----------|-------|---------|
| `092077c4` | Prompt Attacks: Tactical Guide | 50+ |
| `c5b0ad67` | Best practices tattiche avanzate | 50 |
| `71db8414` | MultiBreak benchmark | 13 |
| `f2afcd97` | MCP Prompt Injection Vulnerabilities | 5 |
| `59025e22` | TAP v2.2 Hexagonal Architecture | 5 |
| `3725c9d1` | AgentZer0 | 14 |
