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
TAPaware/
├── README.md
├── AGENTS.md              # Agent operational guide
├── pyproject.toml         # Project config + pytest settings
├── src/aware/             # Installable Python package
│   ├── config.py          # Centralized Pydantic settings
│   ├── memory/
│   │   ├── models.py      # Pydantic schemas (MemoryUnit, AttackType, etc.)
│   │   ├── database.py    # SQLite schema + connection management
│   │   ├── embeddings.py  # EmbeddingService + RemoteEmbeddingService
│   │   ├── vector_store.py # VectorStore (sqlite-vss or brute-force fallback)
│   │   ├── manager.py     # MemoryManager (unified CRUD)
│   │   ├── knowledge_expansion.py # Attack type knowledge management
│   │   ├── conversational.py, entity.py, workflow.py, toolbox.py
│   │   ├── summary.py, tool_log.py
│   │   ├── consolidation.py, decay.py, persistence.py
│   │   └── ...
│   ├── context/
│   │   ├── tokenizer.py, assembler.py, compressor.py, monitor.py
│   ├── api/
│   │   ├── engine_hooks.py  # AwareEngine (TAP integration interface)
│   │   └── schemas.py       # Request/response models
│   └── data/
│       └── seed_attack_types.json
├── tests/                 # 121 tests, all passing
├── tap-app/               # TAP Framework v3.1 full-stack app
├── docs/
│   ├── architecture.md
│   ├── analysis/          # TAP framework analysis, memory gaps
│   ├── plans/             # Integration plan
│   └── research/          # LLM injection, MCP vulnerabilities
└── data/                  # Operational data from TAP runs
```

## Quick Start

```bash
pip install -e ".[dev]"

# Run tests
python -m pytest tests/ -v -p no:postgresql

# Use the engine
python -c "
import asyncio
from aware.api.engine_hooks import AwareEngine
from aware.memory.models import AttackType

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
from aware.memory.knowledge_expansion import KnowledgeExpansion
from aware.memory.models import AttackType, Countermeasure

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
