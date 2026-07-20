# TAP Framework — Project Memory

## Project context
- **Name**: TAP Framework (Tree of Attacks with Pruning)
- **Version**: v3.0.0 (`hybridGUI` branch), evolving toward v3.1.0-beta
- **Purpose**: LLM security research framework — adversarial attack pipeline to extract secret passphrase properties from an LLM-powered Twitter/X bot (`@HackingA0`) using Shannon entropy-driven probe generation
- **License**: Apache-2.0, classified as Science/Research + Security
- **Target**: `pyproject.toml` name = `tap-framework`, Python >= 3.11

## Rules
- User speaks Italian — conversational turns may be in Italian
- User prefers concise, direct answers

## Architecture decisions
- **2026-06-26**: Evolving from monolithic TAP v2.2 into hybrid architecture with three subsystems: TAP (core engine, SQLite), HYDRA (Neo4j graph-based technique management), CHRONOS (Temporal workflow orchestration, PostgreSQL). Decision documented in `.ignore.workinprogress/TAPv4/migration/APP_Opzione_Ibrida_Tech_Specs.md` [ses_0e1561c8cffe2nzwJRvCas1s75]
- **2026-06-26**: Phases 0+1+2 of hybrid migration completed: directory structure, Pydantic v2 contracts, Protobuf schemas, HYDRA/CHRONOS module implementations, 15 passing tests, mypy strict clean. Phase 3 (integration tests) is the declared next step [ses_0e1561c8cffe2nzwJRvCas1s75]
- **2026-06-26**: Docker Compose split into two stacks: `docker-compose.infra.yml` (8 backing services) and `docker-compose.app.yml` (5 application services). Infrastructure never actually started/verified [ses_0e1561c8cffe2nzwJRvCas1s75]
- **2026-07-01**: Simulator should be built before other improvements (elevated from Phase 6 to P0 in roadmap). Enables offline strategy evaluation without burning real probes [ses_0e1561c8cffe2nzwJRvCas1s75]

## Discovered durable knowledge
- **Bug confirmed**: `src/chronos/orchestrator.py:79` uses `uuid4()` but only `UUID` is imported (line 77). Will raise `NameError` at runtime when `attack_id` is falsy. Fix: add `from uuid import uuid4` [ses_0e1561c8cffe2nzwJRvCas1s75]
- **node_modules committed**: `frontend/node_modules/` is tracked in git, bloating the repo. `.gitignore` missing this entry [ses_0e1561c8cffe2nzwJRvCas1s75]
- **Untested modules**: HYDRA (acd, v_genome, fusion_engine) and CHRONOS (coat_engine, behavioral_profiler, persistence, orchestrator, workflows, activities) lack test coverage [ses_0e1561c8cffe2nzwJRvCas1s75]
- **Protobuf not compiled**: `.proto` files in `src/shared/proto/` are defined but never compiled to Python stubs [ses_0e1561c8cffe2nzwJRvCas1s75]
- **Rust Fusion Engine planned**: `fusion_engine.py` is an explicit Python stub. Full implementation calls for Rust 1.80+ core with PyO3 bindings [ses_0e1561c8cffe2nzwJRvCas1s75]
- **SSOT still markdown**: Planned Kafka-based event sourcing replacing `hackinga0_analysis.md` static markdown is not implemented [ses_0e1561c8cffe2nzwJRvCas1s75]
- **engine.py is 745 lines** (v4 Phase 1 with EventStore dual-write). Strangler Fig refactoring plan targets reduction to ~180 lines across 5 phases [ses_0e1561c8cffe2nzwJRvCas1s75]
- **Zero TODO/FIXME markers in src/**: Codebase is clean of TODO, FIXME, HACK, XXX, STUB, PLACEHOLDER, NotImplementedError markers. Verified by grep across all .py files [ses_0e1561c8cffe2nzwJRvCas1s75]
- **stream_listener.py is well-structured**: Exception handling uses structured logging, not bare pass blocks. Only bare pass in QueueFull and CancelledError — both acceptable [ses_0e1561c8cffe2nzwJRvCas1s75]

## Patterns
- **Language**: Bilingual Italian/English — code comments/docstrings in English, narrative prose/commits often in Italian
- **Config**: Pydantic Settings loaded from `.env`, cached singleton via `@lru_cache` on `get_settings()`
- **Logging**: `structlog` with contextvars propagation (`cycle_id`, `probe_id`)
- **LLM Gateway**: OpenRouter via OpenAI SDK with circuit breaker (CLOSED→OPEN→HALF_OPEN), multi-tier fallback (PRIMARY/HARD/GROK)
- **HITL constraint**: Attack cycle requires explicit human selection of probe A/B before execution — core design decision
- **Entropy trigger**: Phase 5 autoregressive extraction activates when Shannon entropy drops below 3.3 bits

## Gotchas
- Docker infrastructure (Neo4j, Kafka, PostgreSQL, Redis, Temporal) has never been started — docker-compose files exist but are unverified in practice
- Heavy hybrid dependencies (torch, neo4j, temporalio, asyncpg, redis, clickhouse-driver) are in requirements but not all installed in dev environment
- Git branch landscape is complex: 10 local + 11 remote branches. Active branch is `hybridGUI`
- Commit messages are inconsistent: Italian ("forse", "cisiamoquasi"), English ("fix: ..."), and terse ("29626", "296")
