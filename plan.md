# TAPaware Evolution History + Code Error Audit

## Goal

Deliver a complete evolution history reconstructed from:
- `explanation.md` (plan / Q&A decisions)
- `mutation.deepseekv4pro.md` (structured session log)
- `deepseek_wholework.txt.md` (raw full session transcript)

…and a verified list of remaining code errors / doc-code mismatches against the current tree.

**This turn is an analysis deliverable.** Optional follow-up: fix the confirmed code bugs listed in Section 4.

---

## 1. What the three files are (roles)

| File | Size | Role | Reliability |
|------|------|------|-------------|
| `explanation.md` | ~60 lines | Pre-implementation **plan** from Q&A | **Stale snapshot** — written *before* Phase 0–3; claims TAP is “not integrated” |
| `mutation.deepseekv4pro.md` | ~345 lines | Clean **session log** of what was done | High — matches git commit `459205a` outcomes |
| `deepseek_wholework.txt.md` | ~1,874 lines / ~100KB | Raw DeepSeek agent transcript (thoughts + tool I/O) | High for process; noisy; best source for *errors hit during the session* |

**Timeline of the three docs relative to git:**

```
Jul 19  Initial Aware memory framework (fdc9218, 1bf72b2, 1aa84dc)
Jul 20  Hybrid TAP app ingested + first bridge (55011c9)  ← Hybrid_new/ still name
Jul 21  DeepSeek session: explanation → mutation work → commit 459205a
        + deepseek_wholework transcript dump (437b68c)
```

---

## 2. Evolution history (reconstructed)

### Phase −1 — Original problem set (user’s 10-item list)

Captured at the top of `deepseek_wholework.txt.md`:

1. Split/clarify two projects (`src/` memory lib vs `Hybrid_new/` TAP app)
2. Fix stale `requirements.txt` (missing `pydantic-settings`)
3. LICENSE / CHANGELOG / root `.gitignore`
4. CI (pytest + ruff + mypy)
5. Wire `AwareEngine` into real TAP
6. Install real embeddings (`sentence-transformers` + `sqlite-vss`)
7. Fix `sys.path` import hacks
8. Consolidate Hybrid docs
9. CHANGELOG
10. `.env.example`

**Core finding (all three docs):** hooks existed in `AwareEngine` but were not the real integration path yet; two projects lived in one repo with no clear story.

### Phase 0a — Q&A decisions (`explanation.md` + mutation §2)

| # | Decision |
|---|----------|
| 1 | Keep both components; document in `docs/architecture.md` |
| 2 | Rename `Hybrid_new/` → `tap-app/` |
| 3 | **Delete** `requirements.txt` (not patch it) |
| 4 | Secrets: `.gitignore` + `.env.example` only; skip history audit |
| 5 | Installable `aware` package + absolute imports |
| 6 | **API embeddings** (not local sentence-transformers as primary) |
| 7 | In-process TAP integration |
| 8 | Keep existing 4 hooks surface |
| A–D | Merge docs; Apache-2.0 root; order = restructure→embeddings→wire; CI = tests+ruff first |

`explanation.md` freezes this plan. It is **not** updated after implementation, so several statements are now false.

### Phase 0b — Foundation (mutation §3 + transcript)

Executed in DeepSeek session on local clone `D:\PROGETTI\Aware`:

1. **Package restructure:** `src/{config,memory,api,context,data}` → `src/aware/...`
2. Delete `config_ref.py`, root `src/__init__.py`
3. Create `src/aware/__init__.py` (27 public exports)
4. Remove `sys.path` hacks from 8 files
5. Rewrite test imports `from memory.` → `from aware.memory.` (~16 files)
6. Fix `pyproject.toml`: `setuptools.build_meta`, `where = ["src"]`, drop `pythonpath`
7. Add `RemoteEmbeddingService` + config fields (`embedding_provider`, `embedding_api_*`)
8. Rename `Hybrid_new/` → `tap-app/`

**Errors hit during this phase (from transcript):**

| Error | Cause | Fix applied |
|-------|-------|-------------|
| `pip install -e` timeout / Traceback on `import aware` | sentence-transformers download + install interrupted | `pip install -e ".[dev]" --no-deps` |
| `collected 37 items / 15 errors` on first pytest | 15 test files still used `from memory.xxx` | Mass replace → `from aware.memory.xxx` |
| Legacy setuptools backend failure (mentioned in mutation) | `setuptools.backends._legacy:_Backend` | Switched to `setuptools.build_meta` |

**Verification claimed:** 121 passed after fix.

### Phase 1 — TAP integration (mutation §4 + transcript ~L1580+)

**Discovery (important):** TAP was **already partially wired** before this session (from commit `55011c9`):

- `TAPEngine(..., aware=None)` constructor
- Hooks at BRANCH / after classify / cycle end
- `api.py` lifespan creates `AwareBridge`

Session work:

1. Retarget `aware_bridge.py` imports: `aware_memory` / `aware_context` → `aware.memory` / `aware.context`
2. Fix `MemoryManager.__init__` to accept `str` db path (bridge passed a string; would have set `self.config = "data/aware.db"` and crashed on `.db_path`)
3. **Did NOT** inject `build_context` into attacker prompts (plan said yes; code only logs)

Transcript notes interface mismatch:
- `AwareEngine.on_reply_received(reply: dict)` vs `AwareBridge.on_reply_received(reply_text: str)`
- Engine uses **AwareBridge** → string path is OK
- Engine uses **AwareEngine** → would break on string reply

### Phase 2 — Hygiene (mutation §5)

- Delete `requirements.txt`
- Update `.gitignore` paths Hybrid → tap-app
- Create `tap-app/.env.example`
- Write `docs/architecture.md`

### Phase 3 — CI / lint (mutation §6)

- Add ruff to `pyproject.toml` (exclude `tap-app/`)
- Add `.github/workflows/ci.yml` (ruff + pytest matrix 3.10–3.12)
- First ruff run: **66 errors** → 65 auto-fixed + 3 manual unused-var fixes (`decay.py`, `persistence.py`, `test_engine_hooks.py`)
- Final: ruff clean, 121 tests pass

### Phase 4 — Docs dump

- Commit `437b68c`: add full `deepseek_wholework.txt.md` transcript
- Mutation file is the cleaned narrative of the same session

### Deferred (mutation §8 — still open)

1. Update README.md + AGENTS.md (still document old layout / sys.path)
2. Root LICENSE (Apache-2.0)
3. CHANGELOG.md
4. mypy in CI
5. Docs consolidation of tap-app README variants
6. **Wire `embedding_provider` selection in MemoryManager** (still hardcodes local `EmbeddingService`)
7. At session end: “commit and push — all local” — later pushed as `459205a`

---

## 3. Doc truth table (current tree vs docs)

| Claim | Source | Current reality |
|-------|--------|-----------------|
| TAP not integrated | `explanation.md` L14 | **False** — bridge wired in api+engine |
| Hooks never called by TAP | `explanation.md` | **False** — called; results only logged |
| `src/api/engine_hooks.py` path | explanation / README | **False** — now `src/aware/api/engine_hooks.py` |
| sys.path required | `AGENTS.md` | **False** for package code; still true in AGENTS doc |
| `from memory.knowledge_expansion` | README L120 | **Stale** — should be `from aware...` |
| API embeddings chosen | all three docs | **Partial** — class exists; **not selected at runtime** |
| build_context injected into prompts | explanation Phase 1 | **Not done** |
| 121 tests pass | mutation | **Confirmed** (re-run 2026-07-24: 121 passed, 2 warnings) |
| ruff clean on src/tests | mutation | **Confirmed** |
| Root LICENSE | deferred | **Still missing** |
| requirements.txt deleted | mutation | **Confirmed** |

---

## 4. Code errors / defects (verified against tree)

### P0 — Logic / integration bugs

| ID | Severity | Location | Issue |
|----|----------|----------|-------|
| **E1** | High | `tap-app/src/tap/engine.py` ~282–292 | `probe_ctx.memory_context` / `attack_knowledge` only **logged**, never injected into attacker prompt or technique selection. Integration is a side-channel recorder, not a closed loop. |
| **E2** | High | `src/aware/memory/manager.py` L30 | `embedding_provider` config **ignored**. Always `EmbeddingService(...)` (local ST). `RemoteEmbeddingService` dead code path for production. TAP init can fail if ST not installed and remote was intended. |
| **E3** | Medium | Dual API surface | `AwareEngine` expects `probe: dict` / `reply: dict`; `AwareBridge` expects `str`. Engine is correct for Bridge only. Switching to `AwareEngine` would raise `AttributeError` on `.get` / wrong types. |

### P1 — Correctness / data bugs

| ID | Severity | Location | Issue |
|----|----------|----------|-------|
| **E4** | Medium | `knowledge_expansion.py` history/rollback | Pydantic warning on export/rollback: `countermeasures` restored as **dicts** not `Countermeasure` models (`Expected Countermeasure … input_type=dict`). Snapshot round-trip incomplete. Tests still pass but serialization is wrong. |
| **E5** | Low | `models.py` vs `schemas.py` | **Duplicate** `ProbeContext`, `ProbeRequest`, `SessionEndResult`. `engine_hooks` imports from `models`; package public API re-exports from `schemas` via `api/__init__.py` — two parallel definitions can drift. |

### P2 — Hygiene / docs / CI

| ID | Severity | Location | Issue |
|----|----------|----------|-------|
| **E6** | Medium | `AGENTS.md`, `README.md` | Document pre-restructure layout, sys.path hacks, wrong import examples |
| **E7** | Medium | `.github/workflows/ci.yml` | Only tests **aware**; never runs `tap-app/tests` |
| **E8** | Low | Root | No `LICENSE` despite Apache-2.0 claim |
| **E9** | Low | `tap-app/src/aware_*` | Legacy duplicate memory package still present; bridge fixed, copy remains confusing |
| **E10** | Info | pytest without install | `ModuleNotFoundError: aware` unless `pip install -e .` (by design after removing pythonpath) |

### Runtime verification (this machine)

```
pip install -e ".[dev]" --no-deps
pytest tests/ -q -p no:postgresql  →  121 passed, 2 warnings
ruff check src/ tests/             →  All checks passed
ast.parse all src/ + tap/src/tap   →  syntax OK
```

Warnings = E4 only (import_export_json + rollback).

### Errors fixed in the historical session (not present now)

- 15 ImportErrors from old `memory.*` paths
- 66 ruff lint issues
- MemoryManager string config crash (fixed)
- aware_bridge old package names (fixed)
- setuptools legacy backend (fixed)

---

## 5. Evolution summary (one paragraph)

The repo evolved in two layers: (1) Jul 19–20 built a standalone 7-type memory library and then **vendored** the full TAP Hybrid app with a first `AwareBridge`; (2) Jul 21 DeepSeek session executed the Q&A plan in `explanation.md` — package rename to installable `aware`, remote embedder class, Hybrid→tap-app, hygiene, CI — and recorded everything in `mutation.deepseekv4pro.md` / `deepseek_wholework.txt.md`. Integration was discovered as “already half-wired”; the session fixed imports/compat but **left memory closed-loop and remote embedding selection unfinished**. `explanation.md` was never rewritten, so it still describes the pre-session world.

---

## 6. Optional remediation plan (only if you want code fixes next)

### PR-A — Close memory loop (E1)
- Inject `probe_ctx.memory_context` (+ compact attack_knowledge) into `ATTACKER_USER` / system messages in `generate_probes` or immediately before branch.
- Optionally bias technique selector with attack_knowledge tags.

### PR-B — Embeddings provider (E2)
- In `MemoryManager.__init__`, branch on `config.embedding_provider`:
  - `local` → `EmbeddingService`
  - `remote` → `RemoteEmbeddingService` (key from `embedding_api_key` or `llm_api_key`)
- Fail fast with clear error if remote and no key.

### PR-C — API surface cleanup (E3, E5)
- Prefer single hook interface: either thin-wrap `AwareEngine` from bridge, or align signatures (`str` vs `dict`).
- Collapse duplicate models to one module.

### PR-D — Countermeasure snapshot (E4)
- On history write/read and rollback, re-hydrate `countermeasures` via `Countermeasure(**cm)` if dict.

### PR-E — Docs/CI hygiene (E6–E8)
- Refresh README + AGENTS to `src/aware` + absolute imports.
- Root LICENSE Apache-2.0.
- Optional second CI job for tap-app unit tests (no Docker).

**Suggested order:** B → D → A → C → E (foundation before closed-loop behavior).

---

## 7. Out of scope for this analysis

- Fixing live X/Twitter or LLM credentials
- Running full Docker TAP stack
- Deleting `tap-app` scrapbook markdown
- Git history rewrite / secrets audit (explicitly skipped in Q&A)

---

## Approval

Approve to:
1. **Analysis only** — keep this report; no code changes, or
2. **Implement PR-A…E** (or a subset) as concrete code fixes.
