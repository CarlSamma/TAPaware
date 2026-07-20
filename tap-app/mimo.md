
# TAP Framework (v3.0 / "APP_Opzione_Ibrida") — Comprehensive Project Description

## 1. What Is This Project?

**TAP Framework** (Tree of Attacks with Pruning) is an **LLM security research framework** designed to execute adversarial attack cycles against an LLM-powered Twitter/X bot (target: `@HackingA0`). Its purpose is to systematically extract secret properties of a passphrase protected by the target bot through a structured, information-theoretic attack pipeline.

The core workflow is:
1. **Select** the most informative property to probe next (using Shannon entropy).
2. **Generate** adversarial probes using LLMs, framed via "Deep Persona Absorption" (DPA) -- metaphorical layers (e.g., nautical/kraken themes, technical/medical themes).
3. **Prune** probes via off-topic filtering and semantic deduplication.
4. **Post** probes to Twitter/X (with human-in-the-loop selection).
5. **Collect** replies in real-time via the X Activity API stream.
6. **Classify** responses (verify_hit, rhetoric_block, persona_pivot, etc.).
7. **Score** responses with a Judge LLM (1-10 scale).
8. **Extract** confirmed properties and update the entropy model.
9. **Repeat** until entropy drops below 3.3 bits, triggering "Phase 5" autoregressive extraction.

The project is evolving from a monolithic v2.2 into a **hybrid architecture** (branch `hybrid`) with three named subsystems:
- **TAP** (original engine, SQLite-backed)
- **HYDRA** (Neo4j graph-based technique management, V-Genome)
- **CHRONOS** (Temporal-based workflow orchestration, beam search, PostgreSQL-backed)

The project is licensed under **Apache-2.0** and is classified as "Intended Audience: Science/Research" with a "Security" topic.

---

## 2. Tech Stack

### Backend (Python 3.11+)
| Category | Technology |
|---|---|
| Web framework | **FastAPI** + **uvicorn** |
| HTTP client | **httpx** |
| Twitter API | **tweepy** (OAuth 1.0a + OAuth 2.0 Bearer + Activity API) |
| LLM gateway | **OpenAI SDK** via **OpenRouter** (Claude Sonnet 4, Grok 4, Grok 4.3) |
| Settings | **pydantic-settings** (from `.env`) |
| Database (TAP) | **SQLite** via **aiosqlite** (async, WAL mode) |
| Database (CHRONOS) | **PostgreSQL 16** via **asyncpg** + **Alembic** migrations |
| Graph DB (HYDRA) | **Neo4j 5.x** (async driver) |
| Event bus | **Apache Kafka** (Confluent 7.7.0, via `kafka-python`) |
| Workflow engine | **Temporal** (via `temporalio` SDK) |
| Caching / state | **Redis 7** |
| Object storage | **MinIO** |
| Analytics DB | **ClickHouse** |
| CDC pipeline | **Debezium** (PostgreSQL -> Kafka -> Neo4j) |
| ML (stub) | **PyTorch** (in requirements, for surrogate model) |
| Logging | **structlog** (structured, context-var propagation) |
| Protobuf | **protobuf** + **grpcio** (schemas in `src/shared/proto/`) |
| Code quality | **ruff** (linter), **mypy** (strict mode) |

### Frontend (TypeScript / React)
| Category | Technology |
|---|---|
| Framework | **React 19** |
| Build tool | **Vite 7** |
| Language | **TypeScript 5.9** |
| Styling | **Tailwind CSS 4** |
| State/data | **TanStack React Query** |
| Charts | **Recharts** |
| Graph viz | **Cytoscape.js** + cytoscape-dagre |
| Icons | **Lucide React** |

### Infrastructure (Docker)
| Service | Image |
|---|---|
| PostgreSQL 16 | `postgres:16-alpine` |
| Neo4j 5 | `neo4j:5.26-community` |
| Kafka + Zookeeper | `confluentinc/cp-kafka:7.7.0` |
| Debezium | `quay.io/debezium/connect:2.7.3.Final` |
| Redis 7 | `redis:7-alpine` |
| Temporal | `temporalio/auto-setup:1.25` |
| Temporal UI | `temporalio/ui:2.32.0` |
| MinIO | `minio/minio` |
| ClickHouse | `clickhouse/clickhouse-server:24.11` |

---

## 3. Directory Structure and Main Modules

```
framework/
|-- README.md                          # Technical architecture doc (Italian)
|-- CHANGELOG.md                       # Version history
|-- pyproject.toml                     # Python package config (setuptools)
|-- requirements.txt                   # Core TAP dependencies
|-- requirements-hybrid.txt            # HYDRA + CHRONOS dependencies
|-- alembic.ini                        # Alembic config for PostgreSQL migrations
|-- Dockerfile                         # Multi-stage: base | hydra | tap | adapters | chronos
|-- Dockerfile.frontend                # Multi-stage: builder | dev | prod (nginx)
|-- docker-compose.infra.yml           # Infrastructure stack (8 services)
|-- docker-compose.app.yml             # Application stack (5 services)
|-- .env                               # Environment variables (credentials)
|
|-- src/                               # Python source (PYTHONPATH=/app/src)
|   |-- tap/                           # ** TAP Engine (core) **
|   |   |-- api.py                     # FastAPI server, REST + WebSocket endpoints
|   |   |-- config.py                  # Pydantic Settings, .env loader
|   |   |-- engine.py                  # Core TAP cycle orchestrator
|   |   |-- models.py                  # Pydantic v2 data models (Tweet, TAPNode, Property, etc.)
|   |   |-- db.py                      # Async SQLite database (WAL, schema, CRUD)
|   |   |-- llm_client.py              # Unified LLM gateway (circuit breaker, retry, fallback)
|   |   |-- classifier.py             # Response classification (pattern recognition)
|   |   |-- judge.py                   # LLM judge (score 1-10)
|   |   |-- dpa.py                     # DPA frame manager (metaphor layers, aliases)
|   |   |-- grok_monitor.py            # Real-time reply detection via stream
|   |   |-- followup.py                # Dual-option A/B follow-up generator
|   |   |-- x_client.py                # Twitter/X API client (triple OAuth)
|   |   |-- stream_listener.py         # Activity API stream listener
|   |   |-- prompt_sanitiser.py        # Probe validation / injection prevention
|   |   |-- ssot.py                    # Single Source of Truth (living markdown)
|   |   |-- agents.py                  # AgentDPAFManager, AgentSTIREvaluator, AgentIntelExtractor
|   |   |-- personas.py                # 10 tactical persona definitions
|   |   |-- prompts.py                 # LLM prompt templates
|   |   |-- phase0.py                  # Phase 0 gate logic
|   |   |-- logger.py                  # Structured logging (structlog)
|   |   |-- exceptions.py              # Custom exception hierarchy
|   |   |-- oauth.py                   # OAuth helpers
|   |   |-- strategies/                # Probe generation strategies (Strategy Pattern)
|   |   |   |-- base.py                # PromptProvider ABC + ProbeContext/ProbeResult
|   |   |   |-- binary_search.py       # Default binary search strategy
|   |   |   |-- metaphor_shift.py      # Frame rotation strategy
|   |   |   |-- aesthetic.py           # Indirect preference extraction
|   |   |   |-- phase5.py              # Autoregressive extraction
|   |   |   |-- selector.py            # StrategySelector (priority cascade)
|   |   |-- control/                   # Policy and scheduling
|   |   |   |-- policy.py
|   |   |   |-- scheduler.py
|   |   |-- domain/                    # Domain events (event sourcing)
|   |   |   |-- events.py              # ProbePosted, ReplyReceived, PropertyConfirmed
|   |   |   |-- candidate_graph.py     # Candidate graph nodes
|   |   |-- execution/                 # Execution layer
|   |   |   |-- probe_factory.py
|   |   |   |-- probe_memory.py        # Probe deduplication / fingerprinting
|   |   |   |-- reply_worker.py
|   |   |   |-- transport_worker.py
|   |   |-- persistence/               # Event store + read model
|   |   |   |-- event_store.py         # EventStore (dual-write to event_log)
|   |   |   |-- read_model.py
|   |   |-- intelligence/              # Intelligence extraction
|   |   |   |-- eig_ranker.py          # Eig property ranking
|   |   |   |-- extractor.py
|   |   |-- infrastructure/            # (placeholder)
|   |   |-- templates/                 # HTML templates
|   |   |-- static/                    # Static assets
|   |
|   |-- hydra/                         # ** HYDRA Subsystem **
|   |   |-- v_genome.py                # Neo4j V-Genome client (technique graph)
|   |   |-- v_genome_schema.cypher     # Neo4j seed schema
|   |   |-- fusion_engine.py           # Cartesian pruning fusion engine
|   |   |-- surrogate_model.py         # Surrogate model (ASR/stealth estimation)
|   |   |-- m2s_converter.py           # Message-to-Social format converter
|   |   |-- obfuscation.py             # Prompt obfuscation layers
|   |   |-- handoff.py                 # HYDRA -> CHRONOS handoff
|   |   |-- acd.py                     # Adaptive Concept Drift detection
|   |
|   |-- chronos/                       # ** CHRONOS Subsystem **
|   |   |-- orchestrator.py            # Kafka consumer + Temporal workflow starter
|   |   |-- beam_search.py             # Beam search engine (gamma-based scoring)
|   |   |-- coat_engine.py             # Chain-of-Attack-Thought (CoAT) reasoning
|   |   |-- gamma_tracker.py           # Gamma score tracker (ensemble)
|   |   |-- behavioral_profiler.py     # OCEAN+ behavioral profiling
|   |   |-- persistence.py             # asyncpg PostgreSQL persistence
|   |   |-- activities/                # Temporal activities
|   |   |   |-- gamma_scoring.py
|   |   |   |-- coat_reasoning.py
|   |   |-- workflows/                 # Temporal workflows
|   |   |   |-- extraction_workflow.py
|   |
|   |-- shared/                        # ** Shared contracts **
|   |   |-- models.py                  # Canonical Pydantic v2 models (FusedPrompt, etc.)
|   |   |-- proto/                     # Protobuf schemas
|   |       |-- discovery.proto
|   |       |-- extraction.proto
|   |       |-- vgenome.proto
|   |       |-- alerts.proto
|   |
|   |-- adapters/                      # ** Adapters Layer **
|       |-- compat/                    # Compatibility adapters (placeholder)
|       |-- social/                    # Social platform adapters (placeholder)
|
|-- entrypoints/                       # Docker CMD entrypoints
|   |-- run_engine.py                  # TAP Engine process (HITL-driven idle loop)
|   |-- run_stream.py                  # Stream Listener process
|   |-- run_chronos.py                 # CHRONOS Temporal worker
|
|-- frontend/                          # React + TypeScript frontend
|   |-- package.json                   # tap-frontend v1.0.0
|   |-- vite.config.ts                 # Vite config with API proxy
|   |-- tsconfig.json
|   |-- src/
|       |-- App.tsx                    # Root component
|       |-- main.tsx                   # React DOM entry
|       |-- pages/Dashboard.tsx        # Main dashboard (3-column layout)
|       |-- components/
|       |   |-- attack/                # ProbeComposer, FollowUpCard
|       |   |-- feed/                  # LiveFeed (tweet stream)
|       |   |-- psycho/                # OceanRadar, StirHistory (OCEAN+ psychometrics)
|       |   |-- ssot/                  # SsotViewer (living markdown)
|       |   |-- system/                # HealthPanel
|       |   |-- layout/                # TopBar
|       |   |-- toast/                 # ToastContainer
|       |   |-- vgenome/               # (empty, placeholder)
|       |-- hooks/
|       |   |-- useApi.ts
|       |   |-- useEngineStatus.ts
|       |   |-- useWebSocket.ts
|       |-- types/tap.ts               # TypeScript type definitions
|
|-- tests/                             # Pytest test suite
|   |-- conftest.py                    # Shared fixtures (mock DB, settings, sample data)
|   |-- test_api.py
|   |-- test_classifier.py
|   |-- test_db.py
|   |-- test_dpa.py
|   |-- test_followup.py
|   |-- test_health.py
|   |-- test_llm_client.py
|   |-- test_models.py
|   |-- test_prompt_sanitiser.py
|   |-- test_ssot.py
|   |-- test_strategies.py
|   |-- test_agents.py
|   |-- test_x_client.py
|   |-- test_x_client_new.py
|   |-- hydra/                         # HYDRA unit tests
|   |   |-- test_m2s_converter.py
|   |   |-- test_obfuscation.py
|   |   |-- test_surrogate_model.py
|   |-- chronos/                       # CHRONOS unit tests
|   |   |-- test_beam_search.py
|   |   |-- test_gamma_tracker.py
|   |-- integration/
|       |-- test_hydra_chronos_handoff.py
|
|-- migrations/                        # Alembic PostgreSQL migrations
|   |-- env.py
|   |-- script.py.mako
|   |-- versions/
|
|-- scripts/                           # Utility scripts
|   |-- setup_db.py
|   |-- seed_vgenome.py
|   |-- debezium.ps1
|   |-- analyze_logs.py
|   |-- verify_x_creds.py
|   |-- test_refresh.py
|   |-- test_stream.py
|   |-- fix_*.py
|
|-- data/                              # Runtime data
|   |-- tap.db                         # SQLite database
|   |-- eig_property_universe.json     # EIG property entropy weights
|   |-- server.log                     # Application logs
|
|-- Sources/                           # Research papers (50+ markdown/PDF references)
|-- .ignore.workinprogress/            # Archived design docs, audit reports, plans
```

---

## 4. Architecture

The project follows a **modular monolith** evolving toward a **hybrid microservice architecture**:

### Current State (v3.0 -- branch `hybrid`)
- **Single Python process** for the core TAP engine (FastAPI + uvicorn).
- **Multi-container Docker deployment** splitting into 4 backend services:
  - `hydra-api` (FastAPI REST API on port 8000)
  - `tap-engine` (core attack engine, HITL-driven)
  - `adapters` (X/Twitter stream listener)
  - `chronos-worker` (Temporal workflow worker)
- **Frontend** as a separate React app (port 3000), proxied to the API.
- **Infrastructure** on 8 backing services (PostgreSQL, Neo4j, Kafka, Redis, Temporal, MinIO, ClickHouse, Debezium).

### Architectural Layers
1. **Configuration Layer**: `.env` + Pydantic Settings (cached singleton).
2. **Infrastructure Layer**: FastAPI, SQLite, structured logging, Twitter client, stream listener.
3. **LLM Layer**: Unified `LLMClient` gateway (OpenRouter) with circuit breaker, retry, model fallback, token tracking.
4. **Application Layer**: TAPEngine, FollowUpGenerator, GrokMonitor, AgentDPAFManager, Judge, StrategySelector.
5. **Presentation Layer**: React dashboard (3-column layout: controls/feed/OCEAN radar).

### Key Design Patterns
- **Strategy Pattern**: Pluggable probe generation strategies (`PromptProvider` ABC with `BinarySearchProvider`, `MetaphorShiftProvider`, `AestheticEvalProvider`, `Phase5ExtractionProvider`), selected by `StrategySelector` via priority cascade.
- **Circuit Breaker**: `LLMClient` trips after N consecutive failures, enters half-open state.
- **Event Sourcing**: `EventStore` dual-writes domain events (`ProbePosted`, `ReplyReceived`, `PropertyConfirmed`) to SQLite event_log.
- **Dependency Injection**: All TAPEngine dependencies injected via constructor.
- **HITL (Human-in-the-Loop)**: User selects probe options A/B via the dashboard before posting.
- **Information Theory**: Shannon entropy drives property selection and Phase 5 trigger.
- **DPA (Deep Persona Absorption)**: 10 tactical personas with metaphorical framing layers, alias management (active/burned/absorbed).

---

## 5. Key Configuration Files

| File | Purpose |
|---|---|
| `pyproject.toml` | Python package definition (v3.0.0), dependencies, mypy/ruff/pytest config |
| `requirements.txt` | Core TAP runtime dependencies (25 packages) |
| `requirements-hybrid.txt` | HYDRA + CHRONOS extended dependencies (32 packages) |
| `.env` | All credentials (Twitter OAuth, OpenRouter API key, DB connections, Neo4j, Kafka, etc.) |
| `alembic.ini` | Alembic config for CHRONOS PostgreSQL migrations |
| `docker-compose.infra.yml` | Infrastructure stack (8 services: Postgres, Neo4j, Kafka, Zookeeper, Debezium, Redis, Temporal, MinIO, ClickHouse) |
| `docker-compose.app.yml` | Application stack (5 services: hydra-api, tap-engine, adapters, chronos-worker, frontend) |
| `Dockerfile` | Multi-stage Python image (base, hydra, tap, adapters, chronos targets) |
| `Dockerfile.frontend` | Multi-stage Node.js image (builder, dev, prod targets) |
| `frontend/package.json` | Frontend dependencies (React 19, Vite 7, Tailwind 4, Cytoscape, Recharts) |
| `frontend/vite.config.ts` | Vite dev server with API/WebSocket proxy to port 8000 |
| `frontend/tsconfig.json` | TypeScript strict config targeting ES2022 |

---

## 6. Entry Points and Main Functionality

### Primary Entry Point
- **`uvicorn tap.api:app --reload`** (or `tap-server` CLI script) -- starts the FastAPI server on port 8000.
- The `lifespan` context manager in `api.py` handles all initialization (DB, LLM client, Twitter client, stream listener, engine, etc.).

### Docker Entry Points
| Entrypoint | CMD | Purpose |
|---|---|---|
| `entrypoints/run_engine.py` | `python /app/entrypoints/run_engine.py` | TAP Engine idle loop (waits for API triggers) |
| `entrypoints/run_stream.py` | `python /app/entrypoints/run_stream.py` | X/Twitter stream listener |
| `entrypoints/run_chronos.py` | `python /app/entrypoints/run_chronos.py` | Temporal workflow worker |

### REST API Endpoints
- `GET /` -- Dashboard HTML
- `GET /api/feed` -- Live tweet feed
- `GET /api/tree` -- TAP tree state
- `GET /api/properties` -- Confirmed properties
- `GET /api/dpa` -- Active DPA frame
- `GET /api/stir` -- STIR psychometric history
- `GET /api/ssot` -- SSOT JSON snapshot
- `GET /api/stats` -- Summary statistics
- `GET /api/entropy` -- Entropy state
- `POST /api/generate-options` -- Generate two probe options (A/B)
- `POST /api/select?choice=A|B` -- Select probe option
- `POST /api/post` -- Execute attack cycle (background task)
- `POST /api/reset` -- Force-reset engine state
- `POST /api/mock` -- Inject mock reply
- `POST /api/confirm_property` -- Manual Phase 0 unlock
- `POST /api/fetch` -- Force-fetch new replies
- `POST /api/webhook` -- X Activity API webhook receiver
- `GET /api/auth/login` -- Start Twitter OAuth 2.0 PKCE flow
- `GET /api/auth/callback` -- OAuth callback
- `GET /health` -- Health check (DB, LLM, stream, sanitiser)
- `GET /metrics` -- Prometheus-compatible metrics
- `GET /api/events` -- Recent event log
- `WS /ws/live` -- Real-time WebSocket updates

---

## 7. Testing Approach

- **Framework**: **pytest** with **pytest-asyncio** (auto mode), **pytest-cov**, **pytest-postgresql**.
- **Test paths**: `tests/`, `tests/hydra/`, `tests/chronos/`, `tests/shared/`, `tests/integration/`.
- **Fixtures** (`conftest.py`): In-memory SQLite database, mock settings (no real API keys), sample data factories (Tweet, TAPNode, Property, DPAFrame, etc.).
- **Mocking**: LLM/Twitter dependencies are mocked in tests. The tests use mock OpenRouter responses.
- **Coverage**: Tests cover:
  - API endpoints (`test_api.py`)
  - Database CRUD (`test_db.py`)
  - Response classification (`test_classifier.py`)
  - DPA frame management (`test_dpa.py`)
  - Follow-up generation (`test_followup.py`)
  - Health endpoints (`test_health.py`)
  - LLM client circuit breaker/retry (`test_llm_client.py`)
  - Data models (`test_models.py`)
  - Prompt sanitiser (`test_prompt_sanitiser.py`)
  - SSOT engine (`test_ssot.py`)
  - Strategy providers (`test_strategies.py`)
  - Agent modules (`test_agents.py`)
  - Twitter client (`test_x_client.py`, `test_x_client_new.py`)
  - HYDRA: M2S converter, obfuscation, surrogate model
  - CHRONOS: beam search, gamma tracker
  - Integration: HYDRA-CHRONOS handoff
- **Run command**: `python -m pytest tests -q`

---

## 8. Notable Patterns and Conventions

1. **Italian/English bilingual**: Code comments, README, and commit messages mix Italian and English. Module docstrings and field descriptions are in English; narrative prose is often in Italian.

2. **Structured logging with context propagation**: All modules use `structlog` via `tap.logger.get_logger()`. Correlation IDs (`cycle_id`, `probe_id`) are propagated through contextvars.

3. **Pydantic v2 everywhere**: All data models use Pydantic v2 `BaseModel` with `Field()` descriptions. No business logic in models -- pure data contracts.

4. **Async-first**: The entire backend is async (`async/await`). SQLite access is via `aiosqlite`. PostgreSQL via `asyncpg`. Kafka consumer runs in an executor.

5. **Circuit breaker pattern**: The `LLMClient` implements a full circuit breaker (CLOSED -> OPEN -> HALF_OPEN) with configurable thresholds and recovery timeout.

6. **Multi-tier model selection**: LLM calls use a tier system (PRIMARY/HARD/GROK) with automatic fallback chains.

7. **Dependency injection**: All major components receive their dependencies via constructor. No global singletons except `get_settings()` (cached via `@lru_cache`).

8. **Event sourcing (v4 Phase 1)**: Domain events (`ProbePosted`, `ReplyReceived`, `PropertyConfirmed`) are dual-written to an event_log table for replay and debugging.

9. **Strategy pattern for probe generation**: Pluggable `PromptProvider` implementations selected by a `StrategySelector` with a priority cascade based on entropy, block count, and frame effectiveness.

10. **HITL (Human-in-the-Loop)**: The attack cycle requires explicit human selection of probe options A/B before execution. This is a core design constraint.

11. **Information-theoretic attack**: Property selection uses Shannon entropy with a 50/50 split heuristic. Phase 5 triggers autoregressive extraction when entropy drops below 3.3 bits.

12. **DPA (Deep Persona Absorption)**: 10 tactical personas with elaborate metaphorical framing (Italian technical jargon, git-rebase authority, zalo sovereign, etc.) to disguise probes as legitimate system interactions.

13. **Multi-database architecture**: SQLite for TAP, PostgreSQL for CHRONOS, Neo4j for HYDRA, Redis for caching/circuit breaker state, ClickHouse for analytics, MinIO for object storage.

14. **Docker Compose split**: Infrastructure and application stacks are separated into two compose files, started in sequence.

15. **Prometheus-compatible metrics**: The `/metrics` endpoint exposes cycle counts, LLM costs, DB stats, and WebSocket client counts in Prometheus text format.

16. **Webhook + streaming dual path**: Reply detection supports both real-time Activity API streaming and webhook callbacks, with fallback mechanisms.