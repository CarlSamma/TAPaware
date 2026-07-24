# AGENTS.md — Aware Framework

## What is this

Python library implementing the 7-type Agent Memory Manager Pattern for the TAP (Tree of Attacks with Pruning) adversarial research framework. SQLite + vector search, Pydantic models, async-first.

## Critical: how to run things

```bash
# Tests (MUST pass -p no:postgresql — a globally installed pytest_postgresql plugin crashes on import)
python -m pytest tests/ -v -p no:postgresql

# Single test file
python -m pytest tests/test_knowledge_expansion.py -v -p no:postgresql

# Syntax check (fast, no deps)
python -c "import ast, glob; [ast.parse(open(f).read()) for f in glob.glob('src/**/*.py', recursive=True)]"
```

## Imports

`aware` is a pip-installable package. All imports use absolute paths from the `aware` root:

```python
from aware.config import AwareConfig
from aware.memory.models import AttackType
from aware.memory.knowledge_expansion import KnowledgeExpansion
from aware.api.engine_hooks import AwareEngine
```

Do **not** use relative `..` imports or `sys.path` hacks — the package structure handles resolution.

## Dependencies

`pyproject.toml` is the single source of truth. There is no `requirements.txt`.

Key deps: `aiosqlite`, `pydantic>=2`, `pydantic-settings`, `sentence-transformers`, `openai`, `tiktoken`, `sqlite-vss`.

Optional (not installed in dev env): `sentence-transformers` (real model), `sqlite-vss` (vector engine). Tests use `MockEmbedder` (hash-based) and brute-force cosine fallback.

## Test architecture

- All tests in `tests/` use `pytest-asyncio` with `asyncio_mode = "auto"` (from `pyproject.toml`)
- `pythonpath = ["src"]` in pyproject.toml for package discovery
- `conftest.py` provides `MockEmbedder`, `db` (in-memory SQLite), `vector_store`, `memory_manager`, and `sample_*` fixtures
- Engine/integration tests (`test_engine_hooks.py`, `integration/`) create their own `MockEmbedder` + wire stores manually — don't use the shared `memory_manager` fixture
- `knowledge_expansion` tests use the `sample_attack_type` fixture from conftest

## Project layout

```
src/aware/
  __init__.py
  config.py                # AwareConfig (Pydantic BaseSettings, AWARE_ env prefix)
  memory/
    models.py              # MemoryUnit, AttackType, Countermeasure, AttackTypeHistory, etc.
    database.py            # Schema DDL (6 tables + vss virtual table), aiosqlite
    embeddings.py          # EmbeddingService + RemoteEmbeddingService (API-based)
    vector_store.py        # VectorStore (sqlite-vss or brute-force fallback)
    manager.py             # MemoryManager — orchestrates 7 stores
    knowledge_expansion.py # Attack type CRUD + versioning + import/export
    conversational.py      # ...entity.py, workflow.py, toolbox.py, summary.py, tool_log.py
    consolidation.py       # episodic → semantic promotion
    decay.py               # exponential confidence decay
    persistence.py         # cross-session save/load
  context/
    tokenizer.py           # tiktoken-based
    assembler.py           # token-budget-aware
    compressor.py          # LLM summarization + truncation fallback
    monitor.py             # event-driven threshold callbacks
  api/
    engine_hooks.py        # AwareEngine — main integration point for TAP
    schemas.py             # request/response models
  data/
    seed_attack_types.json # 12 seed attack types (V-Genome + extras)
tests/                     # 121 tests, all passing
```

## Style

- Python 3.10+, type hints everywhere, `from __future__ import annotations`
- Pydantic v2 for all models (not dataclasses)
- Async/await throughout (aiosqlite)
- No comments unless the why is non-obvious
- `timezone.utc` for all datetimes (not naive `datetime.utcnow()`)

## Known limitations (current state)

- No real `sentence-transformers` model installed — `MockEmbedder` used in tests
- No `sqlite-vss` — vector search degrades to brute-force cosine
- No CI/CD, no linting config, no type checking (mypy/pyright)
- No integration with actual TAP engine yet
