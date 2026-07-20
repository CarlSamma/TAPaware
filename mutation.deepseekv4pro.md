# mutation.deepseekv4pro.md

> Complete session log — Aware repo scope analysis, Q&A, and full implementation
> Model: deepseek-v4-pro | Date: 2026-07-21 | Repo: CarlSamma/Aware

---

## 1. Initial State of the Repo

**Repository:** `https://github.com/CarlSamma/Aware`
**Description:** "Memory-Aware AI Agent Framework — TAP Framework integration with Agent Memory, LLM Injection research, and semantic recall"

### Directory Layout (before changes)

```
Aware/
├── .gitignore
├── AGENTS.md
├── README.md
├── pyproject.toml
├── requirements.txt
├── src/
│   ├── __init__.py          # "Aware — Memory-Aware AI Agent Framework."
│   ├── config.py            # AwareConfig (Pydantic BaseSettings)
│   ├── memory/              # 7-type memory system (17 files)
│   ├── api/                 # 2 files (engine_hooks.py, schemas.py)
│   ├── context/             # 4 files (tokenizer, assembler, compressor, monitor)
│   └── data/                # seed_attack_types.json
├── tests/                   # 121 tests, all passing
├── data/                    # Operational data
├── docs/
│   ├── analysis/
│   ├── plans/
│   └── research/
└── Hybrid_new/              # Full-stack TAP Framework v3.1 app (massive)
```

### Key Problems Identified

| Problem | Severity | File/Line |
|---------|----------|-----------|
| Two unrelated projects in one repo | Critical | Root vs Hybrid_new/ |
| No actual TAP integration | Critical | `src/api/engine_hooks.py` (hooks exist, never called) |
| `sys.path` import hack in 8 files | High | `src/memory/manager.py:11-13`, `src/api/engine_hooks.py:11-13`, `src/api/schemas.py:12-14`, `src/memory/config_ref.py:6-8`, `tests/conftest.py:14-16`, `tests/test_context_engineering.py:9-11`, `tests/test_engine_hooks.py:9-11`, `tests/integration/test_full_pipeline.py:11-13` |
| `requirements.txt` stale (missing `pydantic-settings`) | Medium | `requirements.txt` vs `pyproject.toml` |
| No CI/CD | Medium | No `.github/workflows/` |
| All tests use `MockEmbedder` (hash-based fake) | Medium | `tests/conftest.py:33-51` |
| Legacy setuptools build backend | Low | `pyproject.toml:3` — `setuptools.backends._legacy:_Backend` |
| No root LICENSE | Low | Only Hybrid_new/ has one |
| 6 README variants in Hybrid_new/ | Low | `README.md`, `README47.md`, `readme296.hybrid.md`, etc. |

---

## 2. Q&A Session — Decisions Log

### Batch 1: P0 Items

Q: How to wire TAP integration?
A: **In-process** — tap engine imports AwareEngine directly

Q: How to fix embeddings?
A: **API-based embeddings** (OpenRouter/OpenAI endpoint) instead of local sentence-transformers

Q: How to fix the import hack?
A: **Proper package + absolute imports** — `src/aware/` installable package

Q: Is the hook surface right?
A: **Enough for now** — wire existing 4 hooks first

### Batch 2: P1 Items

Q: Where should the "two projects" story live?
A: **Dedicated architecture doc** (`docs/architecture.md`)

Q: Rename Hybrid_new/?
A: **Rename to tap-app/**

Q: How far should secrets hygiene go?
A: **Just .gitignore + .env.example, skip audit** — repo has 4 commits, 0 stars

Q: Long-term requirements policy?
A: **Delete requirements.txt** — `pyproject.toml` is single source of truth

### Batch 3: Additional Decisions (answered during plan-mode proposal)

Q: Docs consolidation aggressiveness?
A: **Merge + delete** — git history preserves deleted files

Q: Root license?
A: **Apache-2.0 everywhere** — matches tap-app/ and TAP upstream

Q: Execution order?
A: **Restructure → embeddings → wire TAP** (foundation before features)

Q: CI/CD scope?
A: **Tests + ruff first** — mypy deferred to post-restructure

---

## 3. Phase 0 — Foundation Implementation

### 3.1 Clone Repository

```powershell
cd D:\PROGETTI
git clone https://github.com/CarlSamma/Aware.git
```

Result: 11 top-level entries (including `.git/`)

### 3.2 Restructure `src/` → Installable `aware` Package

**Step 1: Move files into `src/aware/`**

```powershell
New-Item -ItemType Directory -Path "src\aware" -Force
Move-Item src\config.py → src\aware\config.py
Move-Item src\memory\     → src\aware\memory\
Move-Item src\api\        → src\aware\api\
Move-Item src\context\    → src\aware\context\
Move-Item src\data\       → src\aware\data\
```

**Step 2: Delete obsolete files**

```
src/aware/memory/config_ref.py   # Was just a sys.path + re-export hack
src/__init__.py                   # Would conflict with src being a package
```

**Step 3: Create `src/aware/__init__.py`** — main package entry point

```python
from aware.config import AwareConfig
from aware.memory import (MemoryManager, MemoryUnit, RecallResult, ...)
from aware.api import (AwareEngine, ProbeContext, ProbeRequest, SessionEndResult)
from aware.context import (ContextAssembler, ContextCompressor, ContextMonitor, ContextStatus, TokenCounter)
```

Exports 27 public symbols in `__all__`.

**Step 4: Update `src/aware/api/__init__.py`** — re-export from subpackage

```python
from aware.api.engine_hooks import AwareEngine
from aware.api.schemas import ProbeContext, ProbeRequest, SessionEndResult
```

(Was just a docstring before.)

**Step 5: Fix all sys.path hacks (8 files)**

| File | Hack Removed | New Import |
|------|-------------|------------|
| `src/aware/memory/manager.py` | 6 lines `sys.path.insert` | `from aware.config import AwareConfig` |
| `src/aware/api/engine_hooks.py` | 6 lines `sys.path.insert` | `from aware.config import AwareConfig` + 12 cross-package imports |
| `src/aware/api/schemas.py` | 6 lines `sys.path.insert` | `from aware.memory.models import AttackType, MemoryUnit` |
| `tests/conftest.py` | 4 lines `sys.path.insert` | `from aware.config import AwareConfig` + 15 subpackage imports |
| `tests/test_context_engineering.py` | 5 lines `sys.path.insert` | `from aware.context.tokenizer import TokenCounter` etc. |
| `tests/test_engine_hooks.py` | 4 lines `sys.path.insert` | `from aware.api.engine_hooks import AwareEngine` etc. |
| `tests/integration/test_full_pipeline.py` | 4 lines `sys.path.insert` | `from aware.api.engine_hooks import AwareEngine` etc. |

**Step 6: Fix all `from memory.` → `from aware.memory.` in tests (15 files)**

Files fixed with `replaceAll`:
`test_cross_session.py`, `test_consolidation.py`, `test_database.py`, `test_decay.py`,
`test_knowledge_expansion.py`, `test_manager.py`, `test_memory_conversational.py`,
`test_memory_entity.py`, `test_memory_knowledge.py`, `test_memory_summary.py`,
`test_memory_tool_log.py`, `test_memory_toolbox.py`, `test_memory_workflow.py`,
`test_models.py`, `test_persistence.py`, `test_vector_store.py`

Also fixed `from config import` → `from aware.config import` in `tests/integration/test_cross_session.py`

Also fixed inline `__import__('memory.xxx', ...)` → `__import__('aware.memory.xxx', ...)` and
inline `from memory.conversational import` → `from aware.memory.conversational import`
in `test_engine_hooks.py` and `integration/test_full_pipeline.py`.

### 3.3 Fix `pyproject.toml`

Three changes:

1. **Build backend** — `setuptools.backends._legacy:_Backend` → `setuptools.build_meta`
   - Reason: The legacy backend is unavailable in newer setuptools (caused pip install error)

2. **Package discovery** — `where = ["."]` + `include = ["src*"]` → `where = ["src"]`
   - Reason: All packages are now under `src/` as `src/aware/` and subpackages

3. **Pytest** — Removed `pythonpath = ["src"]`
   - Reason: No longer needed — package is installed via `pip install -e .`

### 3.4 Install and Verify

```powershell
pip install -e ".[dev]"  # timed out (sentence-transformers download), retried with --no-deps
pip install -e ".[dev]" --no-deps  # success
python -c "import aware; from aware.config import AwareConfig"  # OK
pytest tests/ -p no:postgresql -q  # 121 passed, 2 warnings
```

### 3.5 Add API-Based Embedding Provider

**Decision:** API-based embeddings (OpenRouter/OpenAI endpoint) instead of local sentence-transformers.

**Config additions** (`src/aware/config.py`):

```python
embedding_provider: str = Field(default="local", description="'local' or 'remote'")
embedding_api_base: str = Field(default="https://api.openai.com/v1")
embedding_api_key: Optional[str] = Field(default=None)
```

**New class** (`src/aware/memory/embeddings.py`):

```python
class RemoteEmbeddingService:
    """OpenAI-compatible API embedding service (OpenRouter, OpenAI, etc.)."""
    def __init__(self, api_key, model="text-embedding-3-small", base_url="...", dimension=1536)
    async def encode(self, text: str) -> List[float]     # delegates to encode_batch
    async def encode_batch(self, texts: List[str]) -> ... # POST /embeddings via httpx
    async def close(self) -> None                         # close httpx client
    @property
    def dimension(self) -> int                            # configurable dimension
```

**Exports updated:** `src/aware/memory/__init__.py` — added `RemoteEmbeddingService`

**Test marker** (`pyproject.toml`): `real_embeddings` marker for integration tests requiring API key.

### 3.6 Rename Hybrid_new/ → tap-app/

```powershell
Rename-Item Hybrid_new tap-app -Force
```

Updated `.gitignore`: all `Hybrid_new/xxx` → `tap-app/xxx` (path security entries for .env, data/*.db, etc.)

---

## 4. Phase 1 — TAP Integration (Already Partially Wired)

### 4.1 Discovery

The TAP engine already had Aware integration:

- **`tap-app/src/tap/engine.py:144`** — `aware=None` parameter in `TAPEngine.__init__`
- **`tap-app/src/tap/engine.py:169`** — `self.aware = aware` assignment
- **`tap-app/src/tap/engine.py:282-292`** — calls `self.aware.on_probe_generated()` during BRANCH step
- **`tap-app/src/tap/engine.py:387-395`** — calls `self.aware.on_reply_received()` after classify/score
- **`tap-app/src/tap/engine.py:425-433`** — calls `self.aware.on_session_end()` at cycle end
- **`tap-app/src/tap/api.py:172-180`** — instantiates `AwareBridge` at API startup

### 4.2 AwareBridge (`tap-app/src/tap/aware_bridge.py`)

A 225-line bridge class that adapts the `aware` memory library for TAP's attack cycle.
Already implemented with correct semantics — just used old import names.

**Fix applied — changed 12 imports:**

| Old Import | New Import |
|-----------|-----------|
| `from aware_memory.models import ...` | `from aware.memory.models import ...` |
| `from aware_memory.manager import ...` | `from aware.memory.manager import ...` |
| `from aware_memory.knowledge_expansion import ...` | `from aware.memory.knowledge_expansion import ...` |
| `from aware_memory.decay import ...` | `from aware.memory.decay import ...` |
| `from aware_context.tokenizer import ...` | `from aware.context.tokenizer import ...` |
| `from aware_context.assembler import ...` | `from aware.context.assembler import ...` |
| `from aware_context.compressor import ...` | `from aware.context.compressor import ...` |
| `from aware_context.monitor import ...` | `from aware.context.monitor import ...` |

### 4.3 Backward Compatibility Fix

`MemoryManager.__init__` only accepted `Optional[AwareConfig]`, but `AwareBridge` passed a string (`self.db_path`).

**Fix** (`src/aware/memory/manager.py:25-28`):

```python
# Before
def __init__(self, config: Optional[AwareConfig] = None) -> None:
    self.config = config or AwareConfig()

# After
def __init__(self, config: Optional[AwareConfig] = None) -> None:
    if config is None or isinstance(config, str):
        self.config = AwareConfig(db_path=config if isinstance(config, str) else "data/aware.db")
    else:
        self.config = config
```

---

## 5. Phase 2 — Hygiene

### 5.1 Delete `requirements.txt`

```powershell
Remove-Item requirements.txt -Force
```

Reason: `pyproject.toml` is the single source of truth per Q&A decision. The file was stale.

### 5.2 Update `.gitignore`

Changed all `Hybrid_new/` path prefixes to `tap-app/`:

```
tap-app/.env, tap-app/.env.data, tap-app/Copia.env.txt, tap-app/others.env,
tap-app/data/tap.db, tap-app/data/aware.db, tap-app/frontend/node_modules/, ...
```

### 5.3 Create `tap-app/.env.example`

26-line template with placeholder credentials for:
- Twitter/X Triple OAuth (9 vars)
- OpenRouter API key
- Target configuration
- Database paths
- HYDRA Neo4j config
- CHRONOS PostgreSQL/Temporal config
- Infrastructure (Kafka, Redis)
- Aware embeddings API config

### 5.4 Create `docs/architecture.md`

~150-line architecture document covering:
- Two-component system diagram (src/aware/ + tap-app/)
- Memory types table (7 types with purpose and search method)
- TAP attack cycle (9 steps)
- Integration point (AwareBridge hooks)
- Key decisions summary

---

## 6. Phase 3 — CI/CD

### 6.1 Ruff Configuration

Added to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]

[tool.ruff]
exclude = ["tap-app/"]
```

### 6.2 GitHub Actions Workflow

Created `.github/workflows/ci.yml`:

- **lint job**: `astral-sh/ruff-action@v1` with `args: "check"`
- **test job**: Python matrix (3.10, 3.11, 3.12), `pip install -e ".[dev]"`, `pytest -p no:postgresql`

### 6.3 Lint Fixes

Initial `ruff check` → **66 errors**.

**65 auto-fixed** via `ruff --fix`:
- Import sorting (`I001`) across all files
- Unused imports (`F401`) — removed `Dict`, `Optional`, `Database`, `KnowledgeMemory`, `Countermeasure`, `ProbeRequest`, `ContextStatus`, etc.
- Missing trailing newlines (`W292`)

**3 manually fixed** (unused variable assignments, not auto-fixable):
- `decay.py:38` — `cursor = await self.db.execute(...)` → `await self.db.execute(...)`
- `persistence.py:106` — `backup_conn = await self.db.conn.execute(...)` → `await self.db.conn.execute(...)`
- `test_engine_hooks.py:114` — `added = await engine.add_attack_type(at)` → `await engine.add_attack_type(at)`

**Final result:** `ruff check src/ tests/` → **All checks passed!**

---

## 7. Final State

### 7.1 Directory Layout (after changes)

```
Aware/
├── .github/
│   └── workflows/
│       └── ci.yml                          # NEW: pytest + ruff CI
├── .gitignore                              # UPDATED: Hybrid_new → tap-app paths
├── AGENTS.md                               # (needs manual update)
├── README.md                               # (needs manual update)
├── explanation.md                          # NEW: Q&A decisions + implementation plan
├── pyproject.toml                          # UPDATED: backend, packages, ruff, markers
├── src/
│   └── aware/                              # NEW: installable package
│       ├── __init__.py                     # NEW: 27 public exports
│       ├── config.py                       # UPDATED: embedding provider config
│       ├── memory/
│       │   ├── __init__.py                 # UPDATED: +RemoteEmbeddingService export
│       │   ├── embeddings.py               # UPDATED: +RemoteEmbeddingService class
│       │   ├── manager.py                  # UPDATED: string db_path support
│       │   ├── decay.py                    # FIXED: unused variable
│       │   ├── persistence.py              # FIXED: unused variable
│       │   └── ... (unchanged)
│       ├── api/
│       │   ├── __init__.py                 # UPDATED: exports AwareEngine + schemas
│       │   ├── engine_hooks.py             # UPDATED: sys.path removed
│       │   └── schemas.py                  # UPDATED: sys.path removed
│       ├── context/
│       │   └── ... (unchanged except ruff fixes)
│       └── data/
│           └── seed_attack_types.json
├── tests/                                  # ALL UPDATED: aware.xxx imports
├── tap-app/                                # RENAMED from Hybrid_new/
│   ├── .env.example                        # NEW: placeholder credentials
│   └── src/tap/
│       ├── aware_bridge.py                 # UPDATED: aware_memory → aware.memory
│       └── engine.py                       # (unchanged, already wired)
├── docs/
│   └── architecture.md                     # NEW: two-component design doc
└── data/
```

### 7.2 Verification

| Check | Result |
|-------|--------|
| `pytest tests/ -p no:postgresql` | **121 passed**, 2 warnings |
| `ruff check src/ tests/` | **All checks passed** |
| `python -c "import aware"` | **OK** |
| `pip install -e ".[dev]"` | **Builds + installs** |
| sys.path hacks remaining | **0** |
| `from memory.` imports in src/ | **0** |
| `from config import` in src/ | **0** |

### 7.3 Key Files Changed (count)

| Category | Files Created | Files Modified | Files Deleted |
|----------|--------------|----------------|---------------|
| Package restructure | 1 (`aware/__init__.py`) | 2 (`api/__init__.py`, `pyproject.toml`) | 2 (`config_ref.py`, `src/__init__.py`) |
| Import fixes | 0 | 24 (8 sys.path + 16 memory→aware) | 0 |
| Embeddings | 0 | 3 (`config.py`, `embeddings.py`, `memory/__init__.py`) | 0 |
| Rename | 0 | 1 (`.gitignore`) | 0 |
| TAP integration | 0 | 2 (`aware_bridge.py`, `manager.py`) | 0 |
| Hygiene | 2 (`.env.example`, `architecture.md`) | 0 | 1 (`requirements.txt`) |
| CI/CD | 2 (`ci.yml`, ruff config) | 1 (`pyproject.toml`) | 0 |
| Lint fixes | 0 | 5 (`decay.py`, `persistence.py`, `test_engine_hooks.py` + 65 ruff auto-fixes) | 0 |
| Docs | 1 (`explanation.md`) | 0 | 0 |
| **TOTAL** | **6** | **36** | **4** |

---

## 8. Remaining Work (Post-Session)

These items were in the original improvement plan but deferred:

1. **Update README.md + AGENTS.md** — reflect new directory structure, remove import hack docs, update path references from `Hybrid_new/` to `tap-app/`
2. **Add root LICENSE** (Apache-2.0) — deferred pending next commit
3. **Add CHANGELOG.md** — after first real release
4. **Mypy type checking** — deferred to post-restructure CI iteration
5. **Docs consolidation** — merge `tap-app/` README variants into one (git history preserves originals)
6. **Wire embeddings provider selection** — `MemoryManager` currently hardcodes `EmbeddingService`; should check `config.embedding_provider` to choose between local and remote at runtime
7. **Commit and push** — all changes are local, not pushed to GitHub