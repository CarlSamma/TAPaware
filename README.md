# Aware — Memory-Aware AI Agent Framework

> Integrating Agent Memory patterns with the TAP Framework for adaptive, stateful adversarial research.

## Overview

**Aware** is a research project that applies the 7-type Memory Manager Pattern from the "Deeplearning.ai - Agent Memory" course to the TAP Framework (Tree of Attacks with Pruning), creating a memory-aware adversarial attack pipeline.

### Key Contributions

1. **Agent Memory Integration** — 7 memory types (Conversational, Knowledge Base, Workflow, Toolbox, Entity, Summary, Tool Log) with real SQLite persistence + vector search
2. **Knowledge Expansion** — User-expandable attack type knowledge with versioning, countermeasures, import/export, and semantic search
3. **Semantic Recall** — Vector-based deduplication and recall via sqlite-vss (with brute-force fallback)
4. **Context Engineering** — Token-aware context window management with tiktoken, LLM summarization, and auto-compression at 80% threshold
5. **Memory Lifecycle** — Consolidation (episodic → semantic), exponential decay, and cross-session persistence
6. **Passphrase Intelligence** — Real attack data from @HackingA0 with confirmed hypothesis: `Halfway-fish-404`

## Repository Structure

```
Aware/
├── README.md
├── pyproject.toml                 # Project config + pytest settings
├── requirements.txt
├── src/
│   ├── __init__.py
│   ├── config.py                  # Centralized Pydantic settings
│   ├── memory/
│   │   ├── __init__.py
│   │   ├── models.py              # Pydantic schemas (MemoryUnit, AttackType, etc.)
│   │   ├── database.py            # SQLite schema + connection management
│   │   ├── embeddings.py          # sentence-transformers wrapper
│   │   ├── vector_store.py        # sqlite-vss wrapper with fallback
│   │   ├── manager.py             # MemoryManager (unified CRUD)
│   │   ├── conversational.py      # ConversationalMemory (SQLite + keyword search)
│   │   ├── knowledge.py           # KnowledgeMemory (vector search + dedup)
│   │   ├── knowledge_expansion.py # Attack type knowledge management
│   │   ├── workflow.py            # WorkflowMemory (semantic dedup)
│   │   ├── toolbox.py             # ToolboxMemory (semantic tool search)
│   │   ├── entity.py              # EntityMemory (entity profiles)
│   │   ├── summary.py             # SummaryMemory (LLM compression)
│   │   ├── tool_log.py            # ToolLogMemory (audit trail)
│   │   ├── consolidation.py       # Episodic → semantic promotion
│   │   ├── decay.py               # Exponential confidence decay
│   │   └── persistence.py         # Cross-session save/load + backup
│   ├── context/
│   │   ├── __init__.py
│   │   ├── tokenizer.py           # tiktoken-based token counting
│   │   ├── assembler.py           # Token-budget-aware context assembly
│   │   ├── compressor.py          # LLM summarization + truncation fallback
│   │   └── monitor.py             # Event-driven threshold monitoring
│   ├── api/
│   │   ├── __init__.py
│   │   ├── engine_hooks.py        # AwareEngine (TAP integration interface)
│   │   └── schemas.py             # Request/response models
│   └── data/
│       └── seed_attack_types.json # 12 V-Genome + evasion types
├── tests/                         # 121 tests, all passing
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_database.py
│   ├── test_embeddings.py
│   ├── test_vector_store.py
│   ├── test_memory_*.py           # Per-type memory tests
│   ├── test_knowledge_expansion.py
│   ├── test_consolidation.py
│   ├── test_decay.py
│   ├── test_persistence.py
│   ├── test_context_engineering.py
│   ├── test_manager.py
│   ├── test_engine_hooks.py
│   └── integration/
│       ├── test_full_pipeline.py
│       └── test_cross_session.py
├── data/                          # Operational data from TAP runs
└── docs/
    ├── analysis/                  # TAP framework analysis, memory gaps
    ├── plans/                     # Integration plan
    └── research/                  # LLM injection, MCP vulnerabilities
```

## Quick Start

```bash
cd Aware
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v -p no:postgresql

# Use the engine
python -c "
import asyncio
from src.api.engine_hooks import AwareEngine
from src.memory.models import AttackType

async def main():
    engine = AwareEngine()
    await engine.initialize()

    # Add a new attack type
    at = AttackType(name='my_attack', category='custom', description='My custom attack')
    await engine.add_attack_type(at)

    # Search attack types
    results = await engine.search_attack_types('custom attack')
    print(f'Found {len(results)} attack types')

    await engine.close()

asyncio.run(main())
"
```

## Knowledge Expansion API

Users can expand attack type knowledge at runtime:

```python
from memory.knowledge_expansion import KnowledgeExpansion
from memory.models import AttackType, Countermeasure

# Add attack type with metadata
at = AttackType(
    name="custom_injection",
    category="injection",
    description="Novel injection technique",
    asr=0.75,
    stealth_rating=0.9,
    target="black-box",
    example_probes=["Probe example 1", "Probe example 2"],
    tags=["injection", "custom"],
)
await expansion.add_attack_type(at)

# Add countermeasures
cm = Countermeasure(
    name="input validation",
    description="Validate and sanitize all user inputs",
    effectiveness=0.8,
    category="architectural",
)
await expansion.add_countermeasure(at.id, cm)

# Import from JSON/YAML
await expansion.import_from_json("my_attack_types.json")

# Export knowledge base
await expansion.export_to_json("knowledge_backup.json")

# Semantic search
results = await expansion.search_attack_types("social engineering")

# Version history + rollback
history = await expansion.get_history(at.id)
await expansion.rollback(at.id, to_version=1)
```

## Architecture

```
User API → AwareEngine → MemoryManager → 7 Memory Stores → SQLite + Vector Search
                         ↓
                    ContextEngineering → TokenCounter → Assembler → Compressor
                         ↓
                    KnowledgeExpansion → AttackType CRUD → Version History
```

## Test Results

```
121 passed, 2 warnings in 2.00s
```

Coverage spans: models, database, embeddings, vector store, all 7 memory types, knowledge expansion, consolidation, decay, persistence, context engineering, memory manager, engine hooks, and integration tests.

## License

Apache-2.0 (same as TAP Framework)
