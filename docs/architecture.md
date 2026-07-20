# Aware — Architecture

## Two-Component System

Aware is a hybrid repo containing two components that work together for
LLM security research and adversarial attack pipelines.

```
┌──────────────────────────────────────────────────┐
│                    Aware Repo                    │
├─────────────────────┬────────────────────────────┤
│  src/aware/         │  tap-app/                  │
│  (Memory Library)   │  (TAP Application)         │
├─────────────────────┼────────────────────────────┤
│ • 7 memory types    │ • FastAPI REST + WebSocket │
│ • Context engine    │ • React 19 dashboard       │
│ • Vector search     │ • Neo4j V-Genome graph     │
│ • Knowledge expand  │ • Temporal workflows       │
│ • Consolidation     │ • Kafka event bus          │
│ • Decay             │ • Docker 15-container stack│
├─────────────────────┼────────────────────────────┤
│  SQLite             │  SQLite + Neo4j + PG16     │
│  pip install aware  │  docker compose up         │
└─────────────────────┴────────────────────────────┘
```

## Component 1: aware (Memory Library)

**Location:** `src/aware/`

A Python library implementing the 7-type Agent Memory Manager Pattern
from the Deeplearning.ai "Agent Memory" course, adapted for adversarial
LLM research.

### Memory Types

| Type            | Purpose                              | Search Method      |
|-----------------|--------------------------------------|--------------------|
| Conversational  | Probe/reply exchange history         | Keyword + metadata |
| Knowledge       | Confirmed facts (passphrase bits)    | Vector + keyword   |
| Workflow        | Attack cycle state transitions       | Semantic dedup     |
| Toolbox         | Available attack techniques          | Semantic search    |
| Entity          | Target/persona profiles              | Entity resolution  |
| Summary         | Compressed session overviews         | Keyword            |
| Tool Log        | Audit trail of all operations        | Metadata query     |

### Key Features
- SQLite persistence with async access (aiosqlite)
- Vector search: local (sentence-transformers) or API-based (OpenAI-compatible)
- Token-aware context window assembly with auto-compression
- Memory lifecycle: consolidation (episodic → semantic), exponential decay
- Cross-session persistence with backup/restore
- Knowledge expansion: attack type CRUD with versioning + import/export

### Installation
```bash
pip install -e ".[dev]"
```

## Component 2: tap-app (TAP Application)

**Location:** `tap-app/`

A full-stack adversarial attack framework implementing Tree of Attacks
with Pruning (TAP). Three subsystems:

| Subsystem | Purpose                    | Database     |
|-----------|----------------------------|--------------|
| TAP       | Core attack engine + API   | SQLite       |
| HYDRA     | Graph-based V-Genome       | Neo4j 5.x    |
| CHRONOS   | Temporal workflow orch.    | PostgreSQL 16|

### Attack Cycle (9 Steps)
1. **SELECT** — Next property via Shannon entropy
2. **TECHNIQUE** — Graph-guided via V-Genome (optional)
3. **BRANCH** — Generate DPA-framed probe variants (LLM)
4. **PRUNE** — Off-topic filter + similarity dedup
5. **POST** — Publish probe tweet (HITL approved)
6. **COLLECT** — Wait for reply via StreamListener
7. **CLASSIFY** — Pattern classification (6 categories)
8. **SCORE** — Judge scoring + gamma tracking (0-10)
9. **FOLLOW-UP** — Generate A/B options for next cycle

### Launch
```bash
cd tap-app
docker compose -f docker-compose.infra.yml up -d
docker compose -f docker-compose.app.yml up -d --build
```

## Integration: AwareBridge

`tap-app/src/tap/aware_bridge.py` connects the two components in-process.
The TAP engine calls AwareBridge hooks at three points in the attack cycle:

| Hook                  | Called at         | What it does                          |
|-----------------------|-------------------|---------------------------------------|
| `on_probe_generated`  | Step 3 (BRANCH)   | Stores probe, enriches with context   |
| `on_reply_received`   | Step 7 (CLASSIFY) | Stores reply, recalls similar past    |
| `on_session_end`      | Cycle end         | Consolidation + decay + stats         |

## Key Decisions

- **Package structure**: `aware` is a pip-installable Python package
  (`pip install -e .`)
- **Embeddings**: Local (sentence-transformers) or API-based
  (OpenAI-compatible), configurable via `AWARE_EMBEDDING_PROVIDER`
- **Integration**: In-process via direct import — no HTTP/event bus overhead
- **Import style**: Absolute imports (`from aware.config import AwareConfig`)
  — no `sys.path` hacks
- **Requirements**: `pyproject.toml` is the single source of truth —
  no separate `requirements.txt`