# Aware — Memory-Aware AI Agent Framework

> Integrating Agent Memory patterns with the TAP Framework for adaptive, stateful adversarial research.

## Overview

**Aware** is a research project that applies the 7-type Memory Manager Pattern from the "Depplearning.ai - Agent Memory" course to the TAP Framework (Tree of Attacks with Pruning), creating a memory-aware adversarial attack pipeline.

### Key Contributions

1. **Agent Memory Integration** — 7 memory types (Conversational, Knowledge Base, Workflow, Toolbox, Entity, Summary, Tool Log) mapped to TAP's existing architecture
2. **LLM Injection Research** — Comprehensive analysis of 8 NotebookLM notebooks covering attack techniques, success rates, and defenses
3. **Semantic Recall** — Vector-based deduplication and recall replacing lexical-only Jaccard similarity
4. **Context Engineering** — Token-aware context window management with auto-compression at 80% threshold
5. **Passphrase Intelligence** — Real attack data from @HackingA0 with confirmed hypothesis: `Halfway-fish-404`

## Repository Structure

```
Aware/
├── README.md                    # This file
├── docs/
│   ├── research/
│   │   ├── llm-injection.md     # LLM Injection research (8 notebooks)
│   │   ├── mcp-vulnerabilities.md # MCP-specific vulnerabilities
│   │   └── attack-success-rates.md # ASR data across techniques
│   ├── analysis/
│   │   ├── tap-framework.md     # TAP Framework deep analysis
│   │   ├── data-findings.md     # Data directory analysis
│   │   └── memory-gaps.md       # Current memory architecture gaps
│   └── plans/
│       └── memory-integration.md # 4-phase integration plan
├── src/
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── manager.py           # MemoryManager (unified CRUD)
│   │   ├── conversational.py    # ConversationalMemory
│   │   ├── knowledge.py         # KnowledgeMemory + vector store
│   │   ├── workflow.py          # WorkflowMemory + embeddings
│   │   ├── toolbox.py           # ToolboxMemory + semantic search
│   │   ├── entity.py            # EntityMemory + profiles
│   │   ├── summary.py           # SummaryMemory + compression
│   │   ├── tool_log.py          # ToolLogMemory + structured query
│   │   ├── embeddings.py        # Embedding generation
│   │   ├── consolidation.py     # Episodic → semantic promotion
│   │   └── decay.py             # Memory staleness scoring
│   └── context/
│       ├── __init__.py
│       ├── tokenizer.py         # Token counting
│       ├── assembler.py         # Context window assembly
│       ├── compressor.py        # Summarization + compaction
│       └── monitor.py           # Usage tracking + auto-trigger
├── data/                        # Operational data from TAP runs
│   ├── passphrase_findings.json
│   ├── all_probes_and_replies.json
│   ├── eig_property_universe.json
│   └── ...
├── .mimocode/
│   ├── skills/
│   │   └── notebooklm/SKILL.md  # NotebookLM interaction patterns
│   └── tools/
│       └── notebooklm-query.ts  # NotebookLM query tool
└── plans/
    └── memory-integration.md    # Detailed implementation plan
```

## Quick Start

```bash
# Clone the repo
git clone https://github.com/CarlSamma/Aware.git
cd Aware

# Install dependencies (TAP Framework)
pip install -r requirements.txt

# Run the memory manager
PYTHONPATH=src python -c "from memory import MemoryManager; print('OK')"
```

## Research Findings

### LLM Injection Attack Success Rates

| Technique | ASR | Target |
|-----------|-----|--------|
| TAP | 64% avg, 81% (GPT-3.5) | Black-box |
| TRIAL | 87% | GLM-4-Plus |
| FigStep-Pro | 89% (CBRN) | Llama-4 |
| Many-Shot | ~100% | >128k context |
| GCG | 97-100% | White-box |
| QueryIPI | 87% avg | Coding agents |

### MCP Vulnerabilities

| Vulnerability | Risk Level |
|--------------|------------|
| Tool Poisoning | CRITICAL |
| Rug Pulls | CRITICAL |
| Cross-Server Shadowing | CRITICAL |
| Confused Deputy | HIGH |
| Third-Party Content Exposure | MEDIUM |

### TAP Framework Memory Gaps

1. **NO VECTOR STORE** — Lexical-only (Jaccard, regex)
2. **NO CONTEXT WINDOW MANAGEMENT** — No token counting
3. **NO MEMORY CONSOLIDATION** — Events fire-and-forget
4. **NO MEMORY DECAY** — All facts permanent
5. **NO RECALL/RETRIEVAL API** — No semantic search
6. **NO MEMORY TYPE DISTINCTION** — Everything flat
7. **NO CROSS-SESSION LEARNING** — Memory per-run

### Passphrase Intelligence

**Hypothesis**: `Halfway-fish-404` (word-word-number, 13-16 chars)

**Evidence**:
- "Halfway" acknowledged 6+ times by bot
- "go-fish-404" format hinted
- "13 letters" mentioned
- "hunter2" was "too much info"

**Bot Defense Pattern**: "Nice try" + name + emoji + deflection

## Memory Integration Plan

### Phase 1: Foundation (Week 1-2)
- Create `src/memory/` package
- Implement `MemoryManager` class
- Add `sqlite-vss` to requirements
- Create `memory_embeddings` table

### Phase 2: Semantic Integration (Week 3-4)
- Add embedding generation (sentence-transformers)
- Implement semantic recall in `KnowledgeMemory`
- Add semantic dedup to `WorkflowMemory`
- Wire Memory Manager into engine loop

### Phase 3: Context Engineering (Week 5-6)
- Implement token counter
- Build context assembler
- Add summarization compressor
- Implement auto-trigger at 80%

### Phase 4: Memory Lifecycle (Week 7-8)
- Implement memory consolidation
- Add memory decay
- Implement cross-session persistence
- Add memory recall API endpoints

## Defense Architecture (Ranked by Determinism)

1. **Capability Scoping** — Reduce what agent can do (strongest)
2. **Egress Allowlisting** — Block exfiltration channels
3. **Structural Content Isolation** — Spotlighting/delimiters
4. **Dual LLM** — Separate tool-use from untrusted data
5. **Plan-Then-Execute** — Fix control flow before processing
6. **Human-in-the-Loop** — MCP spec: SHOULD → MUST

## Key Insights

### From LLM Injection Research
- Memory Poisoning Risk (ASI06): Attackers store instructions in agent memory
- Context Quarantine: Tier 3 subagents for untrusted tasks
- Semantic Firewall: Vector-space intent detection
- VerifyClaimTool Protocol: ClaimAttestation with 4 verification types
- Rule of Two: Agent shouldn't simultaneously process untrusted inputs, access sensitive systems, and change state

### From TAP Framework Analysis
- TAP is vulnerable to ASI06 (memory poisoning) — needs instruction-persistence blocking
- No semantic deduplication — lexical-only Jaccard
- No context engineering — hardcoded token limits
- No cross-session learning — memory per-run

## License

Apache-2.0 (same as TAP Framework)

## Acknowledgments

- **TAP Framework** by CarlSamma — Tree of Attacks with Pruning
- **Depplearning.ai** — Agent Memory course
- **NotebookLM** — Research aggregation platform
