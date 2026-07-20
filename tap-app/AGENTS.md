# AGENTS.md — TAP Framework

## Project Identity
- **Name**: TAP Framework (Tree of Attacks with Pruning) v3.0.0
- **Purpose**: LLM security research — adversarial attack pipeline against `@HackingA0` on X/Twitter
- **Branch**: `hybridGUI` (active development)
- **License**: Apache-2.0

## Quick Commands

```bash
# Tests
python -m pytest tests -q                          # Run all tests
python -m pytest tests/test_models.py -v           # Run single test file
python -m pytest tests/integration/ -v             # Integration tests only

# Type check & lint
mypy src/ --strict                                 # Type check (strict mode)
ruff check src/                                    # Lint

# Dev server (from project root)
PYTHONPATH=src uvicorn tap.api:app --reload        # Start API server

# V-Genome (requires Neo4j running)
python scripts/seed_vgenome.py                     # Seed attack techniques (idempotent)

# Docker
docker compose -f docker-compose.infra.yml up -d   # Start infrastructure (8 services)
docker compose -f docker-compose.app.yml up -d --build  # Start application (5 services)

# Utilities
python scripts/verify_x_creds.py                  # Verify X/Twitter credentials
python scripts/analyze_logs.py                    # Analyze attack session logs
```

## Architecture

Three subsystems on `hybridGUI`:

| Subsystem | Purpose | Database |
|-----------|---------|----------|
| **TAP** | Core attack engine, API, strategies | SQLite (`data/tap.db`) |
| **HYDRA** | Neo4j graph-based technique management | Neo4j 5.x |
| **CHRONOS** | Temporal workflow orchestration | PostgreSQL 16 |

**Entrypoints**:
- `src/tap/api.py` — FastAPI app, lifespan wires full stack (primary)
- `entrypoints/run_engine.py` — TAP engine idle loop (HITL-driven)
- `entrypoints/run_stream.py` — X/Twitter stream listener
- `entrypoints/run_chronos.py` — Temporal worker (NOT IMPLEMENTED — `chronos/worker.py` missing)

**PYTHONPATH**: `src/` (Docker: `/app/src`, local: `PYTHONPATH=src`)

**Imports**: `from tap.config import Settings`, `from hydra.v_genome import VGenome`, etc.

## Attack Techniques — V-Genome Schema

Techniques are `AttackTechnique` nodes in Neo4j. Schema:

| Field | Type | Description |
|-------|------|-------------|
| `technique_id` | string | Unique identifier |
| `name` | string | Human-readable name |
| `category` | string | Family: incremental, persuasion, roleplay, priming, injection, reasoning, multimodal, optimization, agentic |
| `asr` | float | Attack Success Rate (0-1) |
| `stealth` | float | Stealth index (0-1) |
| `burned` | bool | Whether technique has been detected |
| `cost_usd` | float | Estimated execution cost |
| `avg_turns` | float | Average turns required |
| `tags` | list | Semantic labels |

**Current techniques** (11 seeded):
- `crescendo` — Foot-in-the-Door (ASR 0.62, stealth 0.78)
- `pap_authority` — Psychological Authority (ASR 0.55, stealth 0.71)
- `roleplay_persona` — Roleplay Hijack (ASR 0.68, stealth 0.74)
- `many_shot` — Many-Shot Priming (ASR 0.71, stealth 0.65)
- `prompt_injection` — Context Injection (ASR 0.58, stealth 0.80)
- `chain_of_thought` — CoT Manipulation (ASR 0.65, stealth 0.82)
- `multimodal_injection` — Cross-Modal Injection (ASR 0.58, stealth 0.85)
- `indirect_injection` — Indirect Prompt Injection (ASR 0.52, stealth 0.88)
- `gcg_optimization` — Gradient-Based Optimization (ASR 0.73, stealth 0.60)
- `tool_exploitation` — Tool-Use Exploitation (ASR 0.61, stealth 0.79)

**Relations**: TARGETS (→TargetModel), COUNTERS (→DefenseLayer), COMPLEMENTS (→AttackTechnique with strength)

**Defense layers**: `input_filter`, `alignment`, `output_moderation`

**To add techniques**: Edit `scripts/seed_vgenome.py`, add MERGE statements following existing pattern. Re-run `python scripts/seed_vgenome.py` — MERGE is idempotent.

## Known Bugs

1. **`src/tap/stream_listener.py`** — 3 bare `pass` blocks swallow exceptions silently (lines ~253, ~259, ~287). QueueFull `pass` blocks are intentional.
2. **Python version mismatch** — Dockerfile uses 3.12, pyproject.toml says >=3.11, mypy targets 3.11.
3. **`frontend/node_modules/`** — Committed to git, bloats repo. `.gitignore` missing this entry.

### Fixed (previously listed)
- ~~`orchestrator.py` uuid4 import~~ — Fixed: `uuid4` now imported from `uuid`.
- ~~`run_stream.py` constructor mismatch~~ — Fixed: removed `db` arg, changed `run()` → `start()`.
- ~~`chronos/worker.py` missing~~ — Fixed: stub created with `run_worker()` function.
- ~~`api.py` silent exception in monitor~~ — Fixed: now logs warning.
- ~~`test_x_client_new.py` casing~~ — Fixed: test expects `@HackingA0`.
- ~~Strategy providers missing `technique` param~~ — Fixed: added defaults to `binary_search.py`, `metaphor_shift.py`, `probe_factory.py`.
- ~~`/api/tree` 500 error~~ — Fixed: added `ALTER TABLE` migrations in `db.py` for `gamma_score`, `gamma_breakdown`, `technique_used` columns.
- ~~Stuck cycle state~~ — Fixed: added `POST /api/reset` endpoint to force-clear `_is_running`.

## Testing Patterns

- **Framework**: pytest + pytest-asyncio (auto mode)
- **Fixtures**: `tests/conftest.py` — `mock_settings`, `db`, `ssot`, `dpa`, `sample_*` fixtures
- **API tests**: Inject mocks into module-level globals (`api._db = mock_db`), cleanup is manual
- **Integration tests**: `tests/integration/` — uses FakeKafkaProducer + FakeTemporalClient (no real services)
- **Each test**: Gets fresh SQLite DB in `tmp_path`

## Config & Environment

- `.env` file required (Twitter OAuth, OpenRouter API key, Neo4j, Kafka, PostgreSQL, Redis, Temporal)
- Settings via `pydantic-settings` — `get_settings()` cached singleton
- No `.env.example` exists — check `src/tap/config.py` for all env var names
- Kafka dual listeners: internal Docker `kafka:29092`, host `localhost:9092`

## Improvement Focus

To plan improvement and increase attack techniques:

1. **Research**: Identify new attack categories (e.g., chain-of-thought manipulation, tool-use exploitation, multimodal injection)
2. **Design**: Define technique schema with ASR/stealth estimates based on literature
3. **Implement**: Add MERGE statements to `scripts/seed_vgenome.py`
4. **Connect**: Add TARGETS, COUNTERS, COMPLEMENTS relations
5. **Test**: Verify techniques are selected by `StrategySelector` in the attack loop
6. **Validate**: Run against target and measure entropy reduction

Key files for technique improvement:
- `scripts/seed_vgenome.py` — Technique definitions
- `src/hydra/v_genome.py` — Neo4j client
- `src/hydra/fusion_engine.py` — Cartesian pruning (currently Python stub)
- `src/tap/strategies/selector.py` — Strategy selection logic

## Research Library

50+ research documents in `.mimocode/Sources/`. Full catalog in `RESEARCH.md`.

| Category | Key Documents | Keywords |
|----------|---------------|----------|
| **TAP Framework** | #45 Tree of Attacks, #1 Protocollo TAP | `TAP` `jailbreaking` `pruning` |
| **Jailbreaking** | #49 AutoDAN, #47 Many-Shot, #44 SM-GCG | `stealthy` `long-context` `optimization` |
| **Prompt Injection** | #36 Indirect IPI, #43 QueryIPI, #42 Agentic | `indirect` `query-agnostic` `coding agents` |
| **Steering** | #3 Activation 2026, #14 ODESteer, #18 RepE | `activation` `representation` `alignment` |
| **Security** | #28 SentinelOne, #17 PriMod4AI, #5 AgentRAE | `security` `privacy` `backdoors` |
| **Multimodal** | #33 Beyond Text, #41 PolyJailbreak, #35 FigStep | `cross-modal` `vision-language` `typographic` |

Search keywords: `TAP` `jailbreaking` `prompt injection` `activation steering` `representation engineering` `LLM security`
