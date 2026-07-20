# Aware — Implementation Plan

*Generated from scope analysis Q&A session — July 2026*

## 1. Context

The Aware repo contains two components under one roof:

| Component | What it is | State |
|---|---|---|
| `src/` | 7-type Agent Memory library + context engineering | Functional, 121 tests passing |
| `tap-app/` (ex-Hybrid_new/) | TAP Framework v3.1 full-stack adversarial app | Working but **not integrated** with the memory library |

**Core finding:** the repo's stated scope — *"TAP Framework integration with Agent Memory"* — is not yet implemented. `AwareEngine` (`src/api/engine_hooks.py`) exposes the right hooks but is never called by the real TAP engine.

## 2. Decisions Locked (via Q&A)

| # | Question | Decision |
|---|---|---|
| 1 | Project split | **Option A** — keep both; story lives in `docs/architecture.md` |
| 2 | Naming | **Rename `Hybrid_new/` → `tap-app/`** |
| 3 | requirements.txt | **Delete it** — `pyproject.toml` is the single source of truth |
| 4 | Secrets hygiene | Root `.gitignore` + `tap-app/.env.example`; **skip git-history audit** |
| 5 | Import hack | **Proper installable `aware` package + absolute imports** — sys.path boilerplate eliminated |
| 6 | Embeddings | **API-based embeddings** (OpenRouter endpoint) instead of local sentence-transformers; MockEmbedder retained for fast unit tests |
| 7 | TAP integration | **In-process** — `tap-app/src/tap/engine.py` imports and calls AwareEngine hooks directly |
| 8 | Hook surface | **Existing 4 hooks are enough for now** (`on_probe_generated`, `on_reply_received`, `on_session_end`, `build_context`) |

## 3. Additional Decisions

| # | Question | Decision |
|---|---|---|
| A | Docs consolidation | Merge useful content into README.md + AGENTS.md; delete redundant files (git history preserves them) |
| B | Root license | Apache-2.0 at root (matching tap-app/ and TAP Framework upstream) |
| C | Execution order | Package restructure → embeddings → wire TAP (foundation before features) |
| D | CI/CD scope | Tests (`pytest -p no:postgresql`) + lint (`ruff check`) first; mypy deferred to post-restructure |

## 4. Implementation Plan

### Phase 0 — Foundation (P0)

1. **Restructure `src/` → installable `aware` package**
   - All files use `from aware.config import AwareConfig` (absolute imports)
   - Remove all `sys.path` boilerplate from `src/memory/*`, `src/api/*`, `tests/conftest.py`
   - Update `pyproject.toml` packages config
   - Run full test suite to verify

2. **API-embedding provider**
   - Add `RemoteEmbeddingService` to `src/memory/embeddings.py` (OpenRouter-compatible endpoint, key via `AWARE_OPENAI_API_KEY` env)
   - Keep `MockEmbedder` for unit tests
   - Add `real_embeddings` pytest marker tier for integration tests

3. **Rename `Hybrid_new/` → `tap-app/`**
   - Update all internal references in docs and config

### Phase 1 — Integration (P0)

4. **Wire `tap-app/src/tap/engine.py` → AwareEngine in-process**
   - `on_probe_generated` — called at step 3 (BRANCH) to provide memory context + attack knowledge
   - `on_reply_received` — called at step 7 (CLASSIFY) to store + recall related memories
   - `on_session_end` — called at campaign end for consolidation + decay
   - `build_context` — inject its output into probe-generation prompts

### Phase 2 — Hygiene (P1)

5. Delete `requirements.txt`
6. Add root `.gitignore` (`.env*`, `data/`, `__pycache__/`, `node_modules/`)
7. Add `tap-app/.env.example` with placeholder keys
8. Write `docs/architecture.md` (two-component story + diagram)

### Phase 3 — Quality & Docs (P2/P3)

9. **GitHub Actions**: single workflow — `pytest -v -p no:postgresql` + `ruff check src/`
10. **Docs consolidation**: merge `tap-app/` markdown files into README.md + AGENTS.md; delete duplicates
11. **Root `LICENSE`**: Apache-2.0
12. **`CHANGELOG.md`**: added after first real release

## 5. Divergences from Original 10-Item List

- **#2 (fix requirements.txt)** → superseded: file deleted entirely, not patched
- **#6 (install sentence-transformers + sqlite-vss)** → superseded: API-based embeddings chosen
- **New items from Q&A:** rename to `tap-app/`, `docs/architecture.md`, package restructure as explicit Phase 0