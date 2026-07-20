# TAP Framework v3.1 — Hybrid Edition

> **Tree of Attacks with Pruning** — LLM Security Research Framework for adversarial attack pipeline against `@HackingA0` on X/Twitter

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![TypeScript 5.9](https://img.shields.io/badge/TypeScript-5.9-blue.svg)](https://typescriptlang.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-orange.svg)](LICENSE)

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Three-Subsystem Design](#three-subsystem-design)
- [Quick Start](#quick-start)
- [Launching the Framework (Windows/VSCode)](#launching-the-framework-windowsvscode)
- [Full System Launch (Docker — Everything Included)](#full-system-launch-docker--everything-included)
- [Docker Infrastructure](#docker-infrastructure)
- [Core Engine (TAP)](#core-engine-tap)
- [Graph Intelligence (HYDRA)](#graph-intelligence-hydra)
- [Workflow Orchestration (CHRONOS)](#workflow-orchestration-chronos)
- [Attack Techniques — V-Genome](#attack-techniques--v-genome)
- [Frontend Dashboard](#frontend-dashboard)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Configuration](#configuration)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Research Library](#research-library)

---

## Recent Updates (Branch `07072026`)

10 verified bugs fixed via cross-analysis of 3 AI reports (Nemotron3Ultra, GLM-5.2, Claude Sonnet 4.6):

| Bug | Severity | Fix |
|-----|----------|-----|
| `_enforce_probe_latency` never sleeps | Critical | Added `asyncio.sleep()`, reduced latency to 3 min |
| Duplicate `/api/reset` route | Critical | Removed dead handler |
| `_attacker_client` bypasses circuit breaker | Critical | Conditional instantiation |
| `upsert_property` TOCTOU race | High | Atomic `ON CONFLICT DO UPDATE` |
| `_filter_similar_probes` wrong field | High | Dedup by `property_tested` |
| CORS credentials + wildcard | High | `allow_credentials=False` |
| `get_settings()` cache stale | High | Added `cache_clear()` |
| `CRITICAL_CLUE` confidence too low | Medium | Raised to 0.85 |
| `enforce_single_property` no-op | Medium | Raises `ValueError` |
| Monitor task not cancelled | Medium | Cancel on shutdown |

See [`fixbugs.md`](fixbugs.md) for full details.

---

## Architecture Overview

The TAP Framework is a **three-subsystem hybrid architecture** designed for LLM security research — specifically, systematic adversarial probing of language models to understand defense mechanisms, alignment boundaries, and information leakage patterns.

The system combines:
- **Automated attack orchestration** with human-in-the-loop (HITL) decision points
- **Graph-based technique management** using Neo4j for dynamic strategy selection
- **Temporal workflow orchestration** for multi-stage extraction campaigns
- **Real-time monitoring** via React dashboard with WebSocket streaming

### Design Principles

1. **Information-theoretic approach**: Uses Shannon entropy to select the most informative property to test next, minimizing total probes needed (~20-30 for passphrase extraction)
2. **Human-in-the-loop**: Every probe requires explicit human approval; the system generates A/B options and waits for selection
3. **Defense-aware strategy**: Tracks observed defense patterns (alignment, output moderation, input filtering) and dynamically adjusts attack techniques
4. **Modular & replaceable**: Each component (LLM gateway, Twitter client, strategy provider, database) can be swapped independently

---

## Three-Subsystem Design

```
┌─────────────────────────────────────────────────────────────────┐
│                        TAP Framework v3.1                       │
├──────────────┬──────────────────┬───────────────────────────────┤
│     TAP      │      HYDRA       │          CHRONOS              │
│   (Core)     │   (Graph DB)     │     (Workflows)               │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Engine       │ V-Genome         │ Gamma Tracker                 │
│ Strategies   │ Fusion Engine    │ Beam Search                   │
│ Classifier   │ CAST Steering    │ Behavioral Profiler           │
│ Judge        │ Layer Steering   │ CoAT Engine                   │
│ LLM Client   │ Surrogate Model  │ Extraction Workflow           │
│ Stream       │ Scanner          │ Orchestrator                  │
│ SSOT         │ M2S Converter    │ Persistence                   │
├──────────────┼──────────────────┼───────────────────────────────┤
│  SQLite      │     Neo4j 5.x    │     PostgreSQL 16             │
└──────────────┴──────────────────┴───────────────────────────────┘
         │              │                    │
         └──────────────┴────────────────────┘
                        │
              Apache Kafka (Event Bus)
              Redis (State Cache)
              MinIO (Object Storage)
              ClickHouse (Analytics)
```

| Subsystem | Purpose | Database | Key Files |
|-----------|---------|----------|-----------|
| **TAP** | Core attack engine, API, strategies, probe generation | SQLite (`data/tap.db`) | `src/tap/` (53 files) |
| **HYDRA** | Graph-based technique management, activation steering | Neo4j 5.x | `src/hydra/` (13 files) |
| **CHRONOS** | Temporal workflow orchestration, gamma scoring | PostgreSQL 16 | `src/chronos/` (13 files) |

---

## Quick Start

**Windows/VSCode**: See [README47.md](README47.md) for step-by-step installation.

### Local Development

```powershell
# Clone
git clone https://github.com/CarlSamma/Hybrid.git
cd Hybrid

# Setup Python environment
# If 'python' is not on PATH, use 'py' launcher instead:
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Start the API server (Windows PowerShell)
$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

**Dashboard**: http://localhost:8000
**API Docs**: http://localhost:8000/docs

### Docker (Full Stack)

> **Important**: A `.dockerignore` file is required to prevent `frontend/node_modules` from being copied into the Docker image (which would overwrite `npm ci`'s clean install). This file is included in the repo.

```powershell
# 1. Start infrastructure (10 services: PostgreSQL, Neo4j, Kafka, Zookeeper, Debezium, Redis, Temporal, Temporal UI, MinIO, ClickHouse)
docker compose -f docker-compose.infra.yml up -d

# 2. Start application (5 services: HYDRA API, TAP Engine, Adapters, Chronos Worker, Frontend)
docker compose -f docker-compose.app.yml up -d --build
```

**Frontend**: http://localhost:3000
**API**: http://localhost:8000
**Temporal UI**: http://localhost:8233
**Neo4j Browser**: http://localhost:7474
**MinIO Console**: http://localhost:9001

---

## Launching the Framework (Windows/VSCode)

Step-by-step guide to run the TAP Framework locally on Windows with Visual Studio Code.

### Prerequisites

| Software | Minimum Version | Download | Verify Command |
|----------|-----------------|----------|----------------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) | `node --version` |
| **Git** | Latest | [git-scm.com](https://git-scm.com/download/win) | `git --version` |
| **VSCode** | Latest | [code.visualstudio.com](https://code.visualstudio.com/) | `code --version` |
| **Docker Desktop** | Latest | [docker.com](https://www.docker.com/products/docker-desktop/) | `docker --version` |

> **Important**: During Python installation, check **"Add Python to PATH"**. Also ensure `py -3.11` works if you have multiple Python versions.

Open PowerShell and verify everything is installed:

```powershell
python --version       # Python 3.11.x or higher
node --version         # v18.x or higher
git --version          # git version 2.x
docker --version       # Docker version 24.x
```

---

### Step 1: Clone the Repository

```powershell
# Navigate to your projects directory
cd L:\PROGETTI

# Clone the repository
git clone https://github.com/CarlSamma/Hybrid.git

# Enter the project
cd Hybrid
```

---

### Step 2: Python Virtual Environment

```powershell
# Create virtual environment
# Use 'py' if 'python' is not on PATH (common on Windows):
py -m venv .venv

# Activate it (PowerShell)
.venv\Scripts\Activate.ps1
```

> **If you get "Execution of scripts is disabled on this system"**, run this first (one-time only):
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

> **If you get "Python was not found"**, use `py -m venv .venv` instead of `python -m venv .venv`. The `py` launcher finds installed Python versions automatically.

You should see `(.venv)` prefix in your terminal prompt.

---

### Step 3: Install Backend Dependencies

```powershell
# Core dependencies (FastAPI, Tweepy, OpenAI, SQLite, etc.)
# Use 'py -m pip' if 'pip' is not on PATH:
py -m pip install -r requirements.txt

# Dev tools (optional but recommended)
py -m pip install pytest pytest-asyncio mypy ruff
```

For the full hybrid stack (Neo4j, Temporal, Kafka, PyTorch):

```powershell
py -m pip install -r requirements-hybrid.txt
```

**Verify installation**:

```powershell
py -c "import fastapi; print('FastAPI:', fastapi.__version__)"
py -c "import uvicorn; print('Uvicorn OK')"
py -c "import tweepy; print('Tweepy OK')"
py -c "import aiosqlite; print('aiosqlite OK')"
```

---

### Step 4: Install Frontend Dependencies

```powershell
# Navigate to frontend directory
cd frontend

# Install npm packages (React 19, Tailwind 4, Vite 7, Recharts, Cytoscape)
npm install

# Verify build works
npm run build

# Go back to project root
cd ..
```

---

### Step 5: Create the .env File

Create a `.env` file in the project root with your credentials. Use PowerShell to create it:

```powershell
@"
# ===== Twitter/X API (Triple OAuth) =====
# OAuth 2.0 Bearer Token (read/search)
TWITTER_BEARER_TOKEN=your_bearer_token_here

# OAuth 1.0a (posting tweets)
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here

# OAuth 2.0 User Context (Activity API subscriptions)
TWITTER_OAUTH2_CLIENT_ID=your_oauth2_client_id
TWITTER_OAUTH2_CLIENT_SECRET=your_oauth2_client_secret
TWITTER_OAUTH2_ACCESS_TOKEN=your_oauth2_access_token

# ===== OpenRouter (single key for ALL LLMs) =====
OPENROUTER_API_KEY=your_openrouter_api_key_here

# ===== Target Configuration =====
TARGET_HANDLE=HackingA0
OUR_BOT_HANDLE=your_bot_handle_here

# ===== Database Paths =====
DB_PATH=data/tap.db
SSOT_PATH=data/hackinga0_analysis.md
LOG_FILE_PATH=data/server.log

# ===== HYDRA (Neo4j — optional, for V-Genome) =====
HYDRA_NEO4J_URI=bolt://localhost:7687
HYDRA_NEO4J_USER=neo4j
HYDRA_NEO4J_PASSWORD=tapv4hydra

# ===== CHRONOS (PostgreSQL — optional, for Temporal) =====
CHRONOS_DB_DSN=postgresql://tap:tap@localhost:5432/chronos
CHRONOS_TEMPORAL_HOST=localhost:7233

# ===== Infrastructure =====
HYDRA_KAFKA_BOOTSTRAP=localhost:9092
CHRONOS_REDIS_URL=redis://localhost:6379/0
"@ | Out-File -FilePath .env -Encoding utf8
```

Now open `.env` in VSCode and replace each `your_*_here` value with your real credentials.

> **Where to get credentials:**
> - **Twitter/X**: [developer.x.com](https://developer.x.com/) → Create a Project + App → Keys & Tokens
> - **OpenRouter**: [openrouter.ai](https://openrouter.ai/) → Create API Key

> **Security Warning**: Do NOT commit `.env`, `.env.data`, `Copia.env.txt`, or `others.env` to version control. These files may contain real API keys and tokens. Ensure they are listed in `.gitignore` before committing.

---

### Step 6: VSCode Configuration

#### 6.1 Open the Project

```powershell
code .
```

#### 6.2 Recommended Extensions

Install these VSCode extensions (Ctrl+Shift+X to open Extensions panel):

| Extension | ID | Purpose |
|-----------|----|---------|
| Python | `ms-python.python` | Python support |
| Pylance | `ms-python.vscode-pylance` | Type checking + IntelliSense |
| ESLint | `dbaeumer.vscode-eslint` | JS/TS linting |
| Tailwind CSS IntelliSense | `bradlc.vscode-tailwindcss` | Tailwind class autocomplete |
| GitLens | `eamodlo.gitlens` | Git history + blame |
| Thunder Client | `rangav.vscode-thunder-client` | API testing (like Postman) |

#### 6.3 Select Python Interpreter

1. Press `Ctrl+Shift+P`
2. Type **"Python: Select Interpreter"**
3. Choose **`.venv\Scripts\python.exe`** (the one inside your project)

#### 6.4 Create launch.json (Debug Configuration)

Create `.vscode/launch.json` for one-click debugging:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "TAP Server (Debug)",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "tap.api:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Run Tests",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": ["tests", "-v"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "cwd": "${workspaceFolder}",
      "console": "integratedTerminal"
    }
  ]
}
```

#### 6.5 Create settings.json (Workspace Settings)

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
  "python.analysis.extraPaths": ["${workspaceFolder}/src"],
  "python.analysis.typeCheckingMode": "basic",
  "editor.formatOnSave": true,
  "python.analysis.stubPath": "",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.codeActionsOnSave": {
      "source.fixAll.ruff": "explicit",
      "source.organizeImports.ruff": "explicit"
    }
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/.mypy_cache": true,
    "**/.pytest_cache": true,
    "frontend/node_modules": true
  },
  "search.exclude": {
    "frontend/node_modules": true,
    "**/*.pyc": true
  }
}
```

---

### Step 7: Neo4j Setup (Optional — for V-Genome)

The V-Genome attack technique graph requires Neo4j. If you started the full Docker infrastructure in the Quick Start, Neo4j is already running on port 7474.

If you're running locally without Docker, start Neo4j separately:

```powershell
# Start Neo4j via Docker
docker run -d --name neo4j-tap `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/tapv4hydra `
  -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' `
  -e NEO4J_dbms_memory_heap_initial__size=512m `
  -e NEO4J_dbms_memory_heap_max__size=1G `
  neo4j:5.26-community
```

Wait ~30 seconds for Neo4j to start, then seed the attack techniques:

```powershell
$env:PYTHONPATH="src"
py scripts/seed_vgenome.py
```

Verify in browser: http://localhost:7474 (login: `neo4j` / `tapv4hydra`)

---

### Step 8: Launch the Backend

Open a terminal in VSCode (Ctrl+` ) and run:

```powershell
# Make sure venv is active
.venv\Scripts\Activate.ps1

# Set PYTHONPATH and start the server
$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

Or simply press **F5** if you configured `launch.json` in Step 6.4.

**Expected output**:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     database_initialized path=data/tap.db
INFO:     llm_client_ready
INFO:     prompt_sanitiser_ready
INFO:     strategy_selector_ready
INFO:     v_genome_client_ready          (if Neo4j running)
INFO:     gamma_tracker_ready            (if hybrid deps installed)
INFO:     api_startup_complete
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

---

### Step 9: Launch the Frontend (Development Mode)

Open a **second terminal** (Ctrl+` then click the + icon):

```powershell
cd frontend
npm run dev
```

**Expected output**:

```
VITE v7.3.x  ready in 300 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

The Vite dev server proxies `/api` and `/ws` requests to `localhost:8000` automatically.

---

### Step 10: Verify Everything Works

| Service | URL | What to Check |
|---------|-----|---------------|
| **Backend API** | http://localhost:8000 | Redirects to dashboard |
| **API Docs (Swagger)** | http://localhost:8000/docs | All endpoints listed |
| **Health Check** | http://localhost:8000/health | All components `healthy` |
| **React Dashboard** | http://localhost:3000 | 4-column grid loads |
| **WebSocket** | ws://localhost:8000/ws/live | Connection established |

**Quick health test in PowerShell**:

```powershell
# Test health endpoint
Invoke-RestMethod -Uri http://localhost:8000/health | ConvertTo-Json -Depth 3

# Test feed endpoint
Invoke-RestMethod -Uri http://localhost:8000/api/feed | ConvertTo-Json

# Test stats
Invoke-RestMethod -Uri http://localhost:8000/api/stats | ConvertTo-Json
```

---

### Full System Launch (Docker — Everything Included)

To run the **entire stack** (all 15 containers: 10 infrastructure + 5 application):

```powershell
# 1. Remove any old containers from previous runs
docker rm -f tap-zookeeper tap-neo4j tap-kafka tap-postgres tap-debezium tap-redis tap-temporal tap-temporal-ui tap-minio tap-clickhouse tap-hydra-api tap-engine tap-adapters tap-chronos-worker tap-frontend 2>$null

# 2. Start infrastructure (10 services)
docker compose -f docker-compose.infra.yml up -d

# 3. Wait for infrastructure to be healthy (~30 seconds)
docker compose -f docker-compose.infra.yml ps

# 4. Start application (5 services)
docker compose -f docker-compose.app.yml up -d --build

# 5. Verify all 15 containers are running
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | findstr tap-
```

**All services and their URLs:**

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend Dashboard** | http://localhost:3000 | React UI |
| **HYDRA API** | http://localhost:8000 | FastAPI REST + WebSocket |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Neo4j Browser** | http://localhost:7474 | Graph database (login: `neo4j` / `tapv4hydra`) |
| **Temporal UI** | http://localhost:8233 | Workflow monitoring |
| **Debezium** | http://localhost:8083 | CDC connector management |
| **MinIO Console** | http://localhost:9001 | Object storage (login: `tap` / `tapv4minio`) |
| **ClickHouse** | http://localhost:8123 | Analytics database |
| **Kafka** | localhost:9092 | Event bus |
| **PostgreSQL** | localhost:5432 | CHRONOS database |
| **Redis** | localhost:6379 | Cache + circuit breaker state |

**Stopping everything:**

```powershell
# Stop application stack
docker compose -f docker-compose.app.yml down

# Stop infrastructure stack
docker compose -f docker-compose.infra.yml down

# Remove all containers and volumes (clean slate)
docker compose -f docker-compose.app.yml down -v
docker compose -f docker-compose.infra.yml down -v
```

---

### Running the Attack Cycle

Once both backend and frontend are running:

1. **Open the dashboard** at http://localhost:3000
2. **Select a technique** from the Technique Selector panel (or let auto-select choose)
3. **Click "Generate Options"** — the engine creates 2 probe variants (A/B)
4. **Review both options** in the ProbeComposer panel
5. **Select A or B** — your choice becomes the active probe
6. **Click "Post & Execute"** — the probe is published as a tweet mentioning @HackingA0
7. **Wait for reply** — the StreamListener detects the response in real-time
8. **View results** — classification, judge score, gamma score appear in the dashboard
9. **Repeat** — new A/B options are generated for the next cycle

---

### Useful Commands Reference

| Task | Command |
|------|---------|
| **Start backend** | `$env:PYTHONPATH="src"; uvicorn tap.api:app --reload` |
| **Start frontend** | `cd frontend; npm run dev` |
| **Run all tests** | `py -m pytest tests -q` |
| **Run single test** | `py -m pytest tests/test_models.py -v` |
| **Type check** | `py -m mypy src/ --strict` |
| **Lint** | `py -m ruff check src/` |
| **Format** | `py -m ruff format src/` |
| **Seed V-Genome** | `$env:PYTHONPATH="src"; py scripts/seed_vgenome.py` |
| **Verify X credentials** | `$env:PYTHONPATH="src"; py scripts/verify_x_creds.py` |
| **Analyze logs** | `$env:PYTHONPATH="src"; py scripts/analyze_logs.py` |
| **Start Neo4j** | `docker start neo4j-tap` |
| **Stop Neo4j** | `docker stop neo4j-tap` |
| **Remove old containers** | `docker rm -f tap-zookeeper tap-neo4j tap-kafka tap-postgres tap-debezium tap-redis tap-temporal tap-temporal-ui tap-minio tap-clickhouse` |

---

### Troubleshooting

#### "Python was not found" / "ModuleNotFoundError"

The `python` command is not on PATH. Use the `py` launcher instead:

```powershell
py -m venv .venv
py -m pip install -r requirements.txt
py -c "import tap; print('OK')"
```

Or set `PYTHONPATH` with the correct Windows syntax:

```powershell
$env:PYTHONPATH="src"
py -c "import tap; print('OK')"
```

Or add `"PYTHONPATH": "${workspaceFolder}/src"` to your `launch.json` env block.

#### "Address already in use" (port 8000)

Another process is using the port. Find and kill it:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### "Execution of scripts is disabled on this system"

PowerShell execution policy blocks the venv activation:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### "Neo4j not connected" / V-Genome unavailable

The framework still works without Neo4j — it falls back to hardcoded techniques. To fix:

```powershell
docker ps | findstr neo4j
docker start neo4j-tap    # if stopped
$env:PYTHONPATH="src"; py scripts/seed_vgenome.py  # re-seed techniques
```

#### "Twitter auth failed"

1. Check all `TWITTER_*` values in `.env`
2. Run `$env:PYTHONPATH="src"; py scripts/verify_x_creds.py` to diagnose
3. Ensure tokens are not expired (regenerate at developer.x.com)

#### "OpenRouter API error" / LLM failures

1. Check `OPENROUTER_API_KEY` in `.env`
2. Verify balance at https://openrouter.ai
3. The circuit breaker trips after 5 consecutive failures — wait 60s or restart the server

#### Frontend shows "Network Error"

The Vite dev server is not proxying to the backend. Ensure:
1. Backend is running on port 8000
2. Frontend `vite.config.ts` has the proxy configured (it does by default)
3. You're accessing http://localhost:3000 (not the direct Vite URL)

#### Windows-specific: Path issues with PYTHONPATH

On Windows PowerShell, use:

```powershell
$env:PYTHONPATH="src"
```

Not `export PYTHONPATH=src` (that's Linux/macOS syntax).

#### Docker: "sh: vite: not found" (Frontend crash-loop)

The `frontend/node_modules` directory is committed to git and gets copied into the Docker image, overwriting `npm ci`'s clean install. The `.dockerignore` file (included in the repo) prevents this. If you still see this error:

```powershell
# Rebuild with --no-cache
docker compose -f docker-compose.app.yml build --no-cache frontend
docker compose -f docker-compose.app.yml up -d frontend
```

---

## Docker Infrastructure

### Infrastructure Stack (`docker-compose.infra.yml`) — 10 Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| **PostgreSQL 16** | `postgres:16-alpine` | 5432 | CHRONOS primary persistence |
| **Neo4j 5.x** | `neo4j:5.26-community` | 7474, 7687 | HYDRA V-Genome graph store |
| **Apache Kafka** | `confluentinc/cp-kafka:7.7.0` | 9092 | Event bus (dual listeners: Docker internal + host) |
| **Zookeeper** | `confluentinc/cp-zookeeper:7.7.0` | 2181 | Kafka coordination |
| **Debezium Connect** | `quay.io/debezium/connect:2.7.3.Final` | 8083 | CDC: PostgreSQL → Kafka → Neo4j |
| **Redis 7** | `redis:7-alpine` | 6379 | Circuit breaker state + cache |
| **Temporal** | `temporalio/auto-setup:1.25` | 7233 | Workflow orchestration engine |
| **Temporal UI** | `temporalio/ui:2.32.0` | 8233 | Workflow monitoring dashboard |
| **MinIO** | `minio/minio` | 9000, 9001 | Object storage for artifacts |
| **ClickHouse** | `clickhouse/clickhouse-server:24.11` | 8123, 9009 | Analytics data warehouse |

### Application Stack (`docker-compose.app.yml`) — 5 Services

| Service | Target | Port | Purpose |
|---------|--------|------|---------|
| **hydra-api** | `hydra` | 8000 | FastAPI REST + WebSocket server |
| **tap-engine** | `tap` | — | Core TAP engine idle loop |
| **adapters** | `adapters` | — | X/Twitter stream listener |
| **chronos-worker** | `chronos` | — | Temporal workflow worker |
| **frontend** | `dev` | 3000 | React + TypeScript dashboard |

### Kafka Dual Listener Architecture

```
Container network (Docker):
  kafka:29092  ← Debezium, TAP Engine, CHRONOS Orchestrator

Host machine (Windows):
  localhost:9092  ← kafkacat, debugging tools, local scripts
```

---

## Core Engine (TAP)

The TAP engine (`src/tap/engine.py`, 870 lines) is the central orchestrator implementing the **Tree of Attacks with Pruning** methodology.

### Attack Cycle (9 Steps)

```
┌──────────────────────────────────────────────────────────────┐
│                    TAP ATTACK CYCLE                          │
├──────┬───────────────────────────────────────────────────────┤
│  1.  │ SELECT — Next property via Shannon entropy            │
│  2.  │ TECHNIQUE — Graph-guided via V-Genome (optional)      │
│  3.  │ BRANCH — Generate DPA-framed probe variants (LLM)     │
│  4.  │ PRUNE — Off-topic filter + similarity dedup           │
│  5.  │ POST — Publish probe tweet (HITL approved)            │
│  6.  │ COLLECT — Wait for reply via StreamListener           │
│  7.  │ CLASSIFY — Pattern classification (6 categories)      │
│  8.  │ SCORE — Judge scoring + gamma tracking (0-10)         │
│  9.  │ FOLLOW-UP — Generate A/B options for next cycle       │
└──────┴───────────────────────────────────────────────────────┘
```

### Phase Gates

| Phase | Trigger | Action |
|-------|---------|--------|
| **Phase 0** | Missing foundational properties | Blocks engine until `word_count`, `total_length`, `language` confirmed |
| **Phase 5** | Entropy < 3.3 bits | Autoregressive extraction via Primacy Weighting |
| **Frame Refresh** | Every 5 probes | Automatic DPA persona rotation |
| **STIR Rotation** | STIR score < 20% | Forced frame rotation to break defense plateau |

### Information-Theoretic Property Selection

The engine maintains a universe of ~10 passphrase properties, each with estimated entropy:

| Property | Entropy (bits) | Description |
|----------|----------------|-------------|
| `word_count` | 2.0 | Number of words in passphrase |
| `total_length` | 3.0 | Total character count |
| `word1_length` | 2.0 | First word character count |
| `word2_length` | 2.0 | Second word character count |
| `language` | 1.5 | Language of each word |
| `word1_language` | 1.5 | Language of first word |
| `word2_language` | 1.5 | Language of second word |
| `first_letter` | 1.0 | First character |
| `word1_first_letter` | 1.0 | First word initial |
| `word2_first_letter` | 1.0 | Second word initial |

**Total entropy budget**: ~15.5 bits → estimated ~20-30 probes for full extraction.

### Response Classification (6 Pattern Classes)

| Pattern | Description | Action |
|---------|-------------|--------|
| `verify_hit` | Property confirmed or denied | Extract property, update SSOT |
| `rhetoric_block` | Defensive deflection ("nice try") | Record defense, consider frame rotation |
| `persona_pivot` | Alignment invocation ("as an AI") | Record alignment defense |
| `critical_clue` | Partial information leaked | Score boost, extract fragments |
| `no_response` | Timeout or silence | Retry with different strategy |
| `metaphor_shift` | Target adopted new metaphor layer | Record layer, update frame |

### Core Files

| File | Lines | Purpose |
|------|-------|---------|
| `api.py` | 782 | FastAPI server, REST + WebSocket, lifespan wiring |
| `engine.py` | 870 | TAP cycle orchestrator, probe generation, extraction |
| `db.py` | 801 | Async SQLite layer, schema, migrations |
| `models.py` | 323 | Pydantic v2 data contracts (14 models, 6 enums) |
| `config.py` | 248 | Settings via pydantic-settings, .env loader |
| `llm_client.py` | 558 | Unified LLM gateway, circuit breaker, fallback |
| `x_client.py` | — | X/Twitter API client (triple OAuth) |
| `stream_listener.py` | — | Activity API stream, real-time reply detection |
| `grok_monitor.py` | — | Reply detection + LLM-based analysis |
| `classifier.py` | — | Response pattern classification |
| `judge.py` | — | Response scoring (1-10 scale) |
| `ssot.py` | 297 | Single Source of Truth, living markdown document |
| `followup.py` | — | Dual A/B follow-up generation |
| `prompt_sanitiser.py` | — | Probe validation before posting |
| `dpa.py` | — | DPA frame management, alias lifecycle |
| `agents.py` | 136 | AgentDPAFManager, AgentSTIREvaluator, AgentIntelExtractor |
| `personas.py` | 67 | 10 tactical DPA personas with prefix templates |
| `prompts.py` | 289 | All LLM prompt templates (centralized) |
| `escalation.py` | 111 | 5-level escalation orchestration with cooldowns |
| `phase0.py` | — | Foundational property gate |
| `frame_refresh.py` | — | Automatic frame rotation logic |
| `verify_claim_patterns.py` | — | 4 claim types for deterministic probes |
| `exceptions.py` | — | Custom exception hierarchy |

### Strategy Providers

| Provider | File | Trigger | Purpose |
|----------|------|---------|---------|
| `BinarySearchProvider` | `binary_search.py` | Default | Standard binary property search |
| `MetaphorShiftProvider` | `metaphor_shift.py` | Avg score < 3.0 | Frame rotation when defenses plateau |
| `AestheticEvalProvider` | `aesthetic.py` | 2+ consecutive blocks | Indirect extraction via aesthetic framing |
| `Phase5ExtractionProvider` | `phase5.py` | Entropy < 3.3 bits | Autoregressive passphrase completion |
| `GraphTechniqueSelector` | `technique_selector.py` | V-Genome available | Dynamic technique selection via graph queries |

### Persistence Layer

| Module | File | Purpose |
|--------|------|---------|
| `EventStore` | `persistence/event_store.py` | Domain event persistence (ProbePosted, ReplyReceived, PropertyConfirmed) |
| `ReadModel` | `persistence/read_model.py` | CQRS read model for projections |

---

## Graph Intelligence (HYDRA)

The HYDRA subsystem (`src/hydra/`, 12 files) provides graph-based attack technique management using Neo4j 5.x.

### V-Genome Schema

Attack techniques are stored as `AttackTechnique` nodes in Neo4j:

```
(AttackTechnique)
  ├── technique_id: string (unique)
  ├── name: string
  ├── category: string (incremental, persuasion, roleplay, priming, injection, reasoning, multimodal, optimization, agentic)
  ├── asr: float (0-1) — Attack Success Rate
  ├── stealth: float (0-1) — Stealth index
  ├── burned: bool — Whether technique has been detected
  ├── cost_usd: float
  ├── avg_turns: float
  └── tags: list

Relations:
  (AttackTechnique)-[:TARGETS]->(TargetModel)
  (AttackTechnique)-[:COUNTERS]->(DefenseLayer)
  (AttackTechnique)-[:COMPLEMENTS {strength: float}]->(AttackTechnique)
```

### Fusion Engine

The Fusion Engine (`fusion_engine.py`, 230 lines) computes composite scores for technique combinations:

```
v2_score = 0.35 * avg_asr
         + 0.25 * avg_stealth
         + 0.20 * synergy
         + 0.10 * platform_fit
         + 0.10 * v_usable_info
```

Bonus multipliers: `+0.05` for MeasurementClaim, `+0.05` for CitationClaim, `+0.08` for CAST usage.

### Activation Steering

| Module | Lines | Purpose |
|--------|-------|---------|
| `cast_steering.py` | 353 | Conditional Activation Steering — modifies hidden states based on condition vectors |
| `layer_steering.py` | 211 | Multi-vector layer-separated steering for different model layers |

### Other HYDRA Components

| Module | Purpose |
|--------|---------|
| `surrogate_model.py` | Surrogate model for technique effectiveness prediction |
| `scanner.py` | Target vulnerability scanner |
| `obfuscation.py` | Prompt obfuscation techniques |
| `m2s_converter.py` | Markdown-to-semantic converter |
| `handoff.py` | HYDRA → CHRONOS handoff protocol |
| `acd.py` | Adaptive context decomposition |

---

## Workflow Orchestration (CHRONOS)

The CHRONOS subsystem (`src/chronos/`, 13 files) manages multi-stage extraction workflows via Temporal.

### Gamma Tracker

The γ-Tracker (`gamma_tracker.py`, 170 lines) implements a 3-layer ensemble scoring system:

| Layer | Method | Latency | Description |
|-------|--------|---------|-------------|
| **Lexical** | Regex/keyword | 0ms | Fast pattern matching for disclosure indicators |
| **Semantic** | LLM judge | ~1-2s | Deep compliance assessment |
| **Behavioral** | OCEAN profile | ~0.5s | Personality-based adjustment |

**γ Scale**: 0.0 (hard refusal) → 10.0 (full secret disclosure)

### Beam Search

`beam_search.py` — Explores multiple attack trajectories in parallel, pruning low-performing branches.

### Behavioral Profiler

`behavioral_profiler.py` — Builds OCEAN personality profiles from target responses.

### CoAT Engine

`coat_engine.py` — Contrastive Attack Style Transfer for generating adversarial prompts.

### Extraction Workflow

`extraction_workflow.py` — Temporal workflow definition for multi-stage extraction campaigns.

---

## Attack Techniques — V-Genome

The system maintains 10+ attack techniques in Neo4j, each with effectiveness metrics:

| ID | Technique | Category | ASR | Stealth | Description |
|----|-----------|----------|-----|---------|-------------|
| `crescendo` | Foot-in-the-Door | incremental | 0.62 | 0.78 | Gradual escalation from benign to harmful |
| `pap_authority` | Psychological Authority | persuasion | 0.55 | 0.71 | Appeals to authority figures |
| `roleplay_persona` | Roleplay Persona Hijack | roleplay | 0.68 | 0.74 | Assumes fictional identity |
| `many_shot` | Many-Shot Priming | priming | 0.71 | 0.65 | Long-context pattern injection |
| `prompt_injection` | Context Injection | injection | 0.58 | 0.80 | Direct context manipulation |
| `chain_of_thought` | CoT Manipulation | reasoning | 0.65 | 0.82 | Exploits reasoning chains |
| `multimodal_injection` | Cross-Modal Injection | multimodal | 0.58 | 0.85 | Vision-language attacks |
| `indirect_injection` | Indirect Prompt Injection | injection | 0.52 | 0.88 | RAG poisoning, indirect channels |
| `gcg_optimization` | Gradient-Based Optimization | optimization | 0.73 | 0.60 | Automated adversarial suffix search |
| `tool_exploitation` | Tool-Use Exploitation | agentic | 0.61 | 0.79 | Exploits tool-use capabilities |

### Defense Layers Tracked

| Defense | Counter-Technique |
|---------|-------------------|
| `input_filter` | Obfuscation, indirect injection |
| `alignment` | Roleplay, authority framing, persona hijack |
| `output_moderation` | Stealth techniques, gradual escalation |

### Tactical Personas (10)

Each technique maps to a DPA persona that provides the cover-story framing:

| Persona | Layer | Technique Match | Style |
|---------|-------|-----------------|-------|
| Patologo Sinaptico | Layer 8 | `many_shot` | Scientific/clinical |
| Geometra del Latente | Layer 8 | `chain_of_thought` | Geometric reasoning |
| Git-Rebase Authority | Layer 9 | `pap_authority` | Technical authority |
| Orchestratore Edge 6G | Layer 9 | `prompt_injection` | Technical/edge computing |
| MD2GPS Specialist | Layer 10 | `indirect_injection` | Medical/indirect |
| Erede del Cantastorie | Layer 10 | `roleplay_persona` | Storytelling |
| Sycophancy Mirror | Layer 11 | `crescendo` | Mirroring/flattery |
| Zalgo Sovereign | Layer XX | `multimodal_injection` | Glitch/visual corruption |
| Unicode Chessmaster | Layer XX | `gcg_optimization` | Adversarial tokens |
| Sleeper Janitor | Layer XX | `tool_exploitation` | System/admin |

---

## Frontend Dashboard

### Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework |
| TypeScript | 5.9 | Type safety |
| Tailwind CSS | 4.1 | Utility-first styling |
| Vite | 7.3 | Build tool & dev server |
| Recharts | 2.15 | Data visualization |
| Cytoscape | 3.32 | Graph visualization |
| TanStack Query | 5.90 | Server state management |
| Lucide React | 0.563 | Icon library |

### Dashboard Layout (4-Column Grid)

```
┌──────────┬──────────────────┬──────────┬──────────┐
│ Controls │   Live Feed      │  OCEAN   │ Escalate │
│ Health   │   @HackingA0     │  Radar   │ Steering │
│ STIR     │                  │          │          │
│ SSOT     │                  │          │          │
└──────────┴──────────────────┴──────────┴──────────┘
  280px         1fr              260px      280px
```

### Components (17)

| Component | Directory | Purpose |
|-----------|-----------|---------|
| `TopBar` | `layout/` | Navigation bar with engine status indicator |
| `LiveFeed` | `feed/` | Real-time tweet feed with WebSocket updates |
| `TweetCard` | `feed/` | Individual tweet display card |
| `ProbeComposer` | `attack/` | Generate and select A/B probe options |
| `FollowUpCard` | `attack/` | Display follow-up recommendations |
| `TechniqueSelector` | `attack/` | Manual technique selection from V-Genome |
| `TechniqueIntelligence` | `attack/` | Technique scoring breakdown (v2) |
| `ScoringBreakdown` | `attack/` | Judge + gamma score visualization |
| `OceanRadar` | `psycho/` | OCEAN personality radar chart |
| `StirHistory` | `psycho/` | STIR metric time series |
| `EscalationMonitor` | `orchestration/` | Escalation level + cooldown display |
| `SteeringControl` | `steering/` | Activation steering vector management |
| `ClaimTypeDashboard` | `verify/` | Claim type distribution visualization |
| `HealthPanel` | `system/` | System health indicators |
| `SsotViewer` | `ssot/` | Living markdown document viewer |
| `AnalyticsDashboard` | `analytics/` | Session analytics + statistics |
| `ToastContainer` | `toast/` | Notification system |

### Real-Time Communication

- **WebSocket** (`ws://localhost:8000/ws/live`): Push events for new tweets, probe results, property confirmations
- **REST API**: Polling fallback for all state queries
- **Keepalive**: 20-second ping/pong heartbeat with automatic reconnection (3s delay)

### Hooks

| Hook | Purpose |
|------|---------|
| `useWebSocket` | WebSocket connection management with auto-reconnect |
| `useApi` | REST API client with typed endpoints |
| `useEngineStatus` | Engine state polling + WebSocket event fusion |

---

## API Reference

### Core Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Dashboard HTML |
| `GET` | `/health` | System health (DB, LLM, Stream, Sanitiser) |
| `GET` | `/metrics` | Prometheus-format metrics |
| `GET` | `/api/feed` | Live tweet feed |
| `GET` | `/api/tree` | TAP attack tree state |
| `GET` | `/api/properties` | Confirmed passphrase properties |
| `GET` | `/api/dpa` | Active DPA frame and aliases |
| `GET` | `/api/ssot` | Full SSOT JSON snapshot |
| `GET` | `/api/stats` | Summary statistics |
| `GET` | `/api/entropy` | Current entropy state |
| `GET` | `/api/stir` | STIR history for psychometric dashboard |
| `GET` | `/api/status` | Real-time cycle execution status |
| `GET` | `/api/events` | Recent event log |
| `GET` | `/api/auth-status` | Twitter auth status |

### Technique Selection

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/techniques` | All available attack techniques |
| `POST` | `/api/technique/select` | Select technique for next probe |
| `GET` | `/api/technique/selected` | Get currently selected technique |
| `GET` | `/api/technique/relations/{id}` | Related techniques (COMPLEMENTS, COUNTERS) |
| `GET` | `/api/technique/auto-select` | Auto-select best technique via graph |

### Attack Control

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/generate-options` | Generate A/B probe options |
| `POST` | `/api/select?choice=A\|B` | Select probe option |
| `POST` | `/api/post` | Execute attack cycle (background) |
| `POST` | `/api/reset` | Force-reset stuck cycle |
| `POST` | `/api/fetch` | Force-fetch new replies |
| `POST` | `/api/confirm_property` | Manual property confirmation |
| `POST` | `/api/mock` | Inject mock reply (testing) |

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/auth/login` | Start Twitter OAuth 2.0 PKCE flow |
| `GET` | `/api/auth/callback` | OAuth callback handler |

### WebSocket

| Path | Description |
|------|-------------|
| `WS /ws/live` | Real-time event stream |

**Event Types**: `new_tweet`, `probe_posted`, `probe_result`, `property_confirmed`, `followup_generated`, `cycle_status`, `cycle_timeout`, `cycle_failed`, `stir_evaluated`, `rotation_suggested`, `phase5_extraction`, `force_reset`

---

## Database Schema

### SQLite Tables (`data/tap.db`)

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `tweets` | Raw tweet storage | `id`, `user_id`, `username`, `text`, `source`, `created_at` |
| `nodes` | TAP tree nodes (attack attempts) | `tweet_id`, `branch_strategy`, `dpa_frame`, `judge_score`, `pattern_class`, `gamma_score`, `technique_used` |
| `properties` | Confirmed/denied passphrase properties | `property_key`, `property_value`, `status`, `confidence` |
| `metaphor_layers` | Metaphor evolution timeline | `layer_number`, `layer_name`, `terms`, `source` |
| `aliases` | DPA alias registry | `alias`, `status` (active/burned/absorbed) |
| `other_user_intel` | Intelligence from other users | `username`, `new_aliases`, `defensive_pattern` |
| `event_log` | WebSocket event persistence | `event_type`, `event_data`, `cycle_id`, `probe_id` |
| `probe_memory` | Probe fingerprint dedup | `fingerprint`, `probe_preview`, `pattern_class`, `judge_score` |
| `candidate_graph_nodes` | Candidate graph for extraction | `node_id`, `property_key`, `status`, `confidence`, `entropy_before/after` |

### Neo4j Graph Schema (HYDRA)

```
(AttackTechnique)-[:TARGETS]->(TargetModel)
(AttackTechnique)-[:COUNTERS]->(DefenseLayer)
(AttackTechnique)-[:COMPLEMENTS {strength}]->(AttackTechnique)
(AttackTechnique)-[:PROVENANCE {attack_id, outcome, asr}]->()
```

---

## Configuration

All configuration is loaded from `.env` via `pydantic-settings`. See `src/tap/config.py` for the complete schema.

### Required Environment Variables

```env
# Twitter API (Triple OAuth)
TWITTER_BEARER_TOKEN=          # OAuth 2.0 Bearer (search/read)
TWITTER_CONSUMER_KEY=          # OAuth 1.0a (posting)
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_OAUTH2_CLIENT_ID=      # OAuth 2.0 User Context
TWITTER_OAUTH2_CLIENT_SECRET=

# OpenRouter (single key for all LLMs)
OPENROUTER_API_KEY=
OPENROUTER_MODEL_PRIMARY=anthropic/claude-sonnet-4
OPENROUTER_MODEL_HARD=x-ai/grok-4.3
OPENROUTER_MODEL_GROK=x-ai/grok-4

# Target
TARGET_HANDLE=HackingA0
OUR_BOT_HANDLE=

# Paths
DB_PATH=data/tap.db
SSOT_PATH=data/hackinga0_analysis.md
LOG_FILE_PATH=data/server.log

# HYDRA (Neo4j)
HYDRA_NEO4J_URI=bolt://localhost:7687
HYDRA_NEO4J_USER=neo4j
HYDRA_NEO4J_PASSWORD=tapv4hydra

# CHRONOS (PostgreSQL + Temporal)
CHRONOS_DB_DSN=postgresql://tap:tap@localhost:5432/chronos
CHRONOS_TEMPORAL_HOST=localhost:7233

# Infrastructure
HYDRA_KAFKA_BOOTSTRAP=localhost:9092
CHRONOS_REDIS_URL=redis://localhost:6379/0
```

### Operational Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `poll_interval_seconds` | 30 | Tweet polling frequency |
| `post_cooldown_seconds` | 60 | Minimum time between posts |
| `reply_timeout_seconds` | 200 | Wait time for bot reply |
| `tap_width` | 10 | TAP tree width (top-w pruning) |
| `tap_depth` | 10 | TAP tree depth levels |
| `tap_branching` | 4 | Variants per leaf node |
| `circuit_breaker_failure_threshold` | 5 | LLM failures before circuit trips |
| `circuit_breaker_recovery_timeout` | 60.0 | Seconds before half-open probe |
| `phase5_entropy_threshold` | 3.3 | Entropy (bits) triggering Phase 5 |
| `oracle_latency_seconds` | 180 | Minimum inter-probe latency (3 min) |

---

## Testing

### Current Status

**269 tests collected**, 267 passed, 2 pre-existing failures (missing `torch` for hydra steering imports — requires `pip install -r requirements-hybrid.txt`).

### Framework

- **pytest** + **pytest-asyncio** (auto mode)
- Each test gets a fresh SQLite DB in `tmp_path`
- LLM/Twitter dependencies mocked via `conftest.py` fixtures

### Test Structure

```
tests/
├── conftest.py                    # Shared fixtures (mock_settings, db, ssot, dpa, sample_*)
├── test_api.py                    # REST endpoint tests
├── test_agents.py                 # AgentDPAFManager, STIREvaluator tests
├── test_classifier.py             # Response classification tests
├── test_db.py                     # Database CRUD tests
├── test_dpa.py                    # DPA frame management tests
├── test_followup.py               # Follow-up generation tests
├── test_health.py                 # Health endpoint tests
├── test_imports.py                # Module import verification
├── test_llm_client.py             # LLM gateway + circuit breaker tests
├── test_models.py                 # Pydantic model validation tests
├── test_prompt_sanitiser.py       # Probe validation tests
├── test_ssot.py                   # SSOT engine tests
├── test_strategies.py             # Strategy provider tests
├── test_technique_selector.py     # Graph technique selector tests
├── test_verify_claim_patterns.py  # Claim pattern tests
├── test_v_genome_new_techniques.py# V-Genome technique tests
├── test_x_client.py               # Twitter client tests
├── test_x_client_new.py           # Updated Twitter client tests
├── benchmark/
│   └── test_scoring_performance.py# Scoring performance benchmarks
├── chronos/
│   ├── test_beam_search.py        # Beam search tests
│   └── test_gamma_tracker.py      # Gamma tracker tests
├── hydra/
│   ├── test_m2s_converter.py      # M2S converter tests
│   ├── test_obfuscation.py        # Obfuscation tests
│   └── test_surrogate_model.py    # Surrogate model tests
└── integration/
    ├── test_engine_cycle.py       # Full engine cycle integration
    └── test_hydra_chronos_handoff.py # HYDRA → CHRONOS handoff
```

### Commands

```powershell
# Run all tests
py -m pytest tests -q

# Run specific test file
py -m pytest tests/test_models.py -v

# Run integration tests only
py -m pytest tests/integration/ -v

# Run with coverage
py -m pytest tests --cov=src/tap --cov-report=html

# Type checking (strict mode)
py -m mypy src/ --strict

# Linting
py -m ruff check src/
```

---

## Project Structure

```
Hybrid/
├── src/
│   ├── tap/                        # Core TAP subsystem (53 files)
│   │   ├── api.py                  # FastAPI server (782 lines)
│   │   ├── engine.py               # TAP cycle orchestrator (870 lines)
│   │   ├── db.py                   # Async SQLite layer (801 lines)
│   │   ├── models.py               # Pydantic data contracts (323 lines)
│   │   ├── config.py               # Settings management (248 lines)
│   │   ├── llm_client.py           # Unified LLM gateway (558 lines)
│   │   ├── ssot.py                 # Single Source of Truth (297 lines)
│   │   ├── prompts.py              # LLM prompt templates (289 lines)
│   │   ├── personas.py             # 10 tactical DPA personas
│   │   ├── strategies/             # Strategy providers (7 files)
│   │   │   ├── base.py             # StrategyType, ProbeContext, PromptProvider
│   │   │   ├── selector.py         # Automated strategy selection
│   │   │   ├── technique_selector.py # Graph-guided technique selection
│   │   │   ├── binary_search.py    # Default binary search
│   │   │   ├── metaphor_shift.py   # Frame rotation
│   │   │   ├── aesthetic.py        # Indirect extraction
│   │   │   └── phase5.py           # Autoregressive extraction
│   │   ├── persistence/            # CQRS event store (3 files)
│   │   ├── domain/                 # Domain events (3 files)
│   │   ├── execution/              # Transport + probe workers (5 files)
│   │   ├── intelligence/           # Extractor + EIG ranker (3 files)
│   │   ├── control/                # Scheduler + policy (3 files)
│   │   └── infrastructure/         # Infrastructure adapters (1 file)
│   ├── hydra/                      # Graph intelligence subsystem (12 files)
│   │   ├── v_genome.py             # Neo4j client (320 lines)
│   │   ├── fusion_engine.py        # Technique scoring (230 lines)
│   │   ├── cast_steering.py        # Conditional activation steering (353 lines)
│   │   ├── layer_steering.py       # Layer-separated steering (211 lines)
│   │   ├── surrogate_model.py      # Effectiveness prediction
│   │   ├── scanner.py              # Vulnerability scanner
│   │   ├── obfuscation.py          # Prompt obfuscation
│   │   ├── m2s_converter.py        # Markdown-to-semantic
│   │   ├── handoff.py              # HYDRA → CHRONOS protocol
│   │   └── acd.py                  # Adaptive context decomposition
│   ├── chronos/                    # Workflow orchestration (13 files)
│   │   ├── gamma_tracker.py        # 3-layer ensemble scoring (170 lines)
│   │   ├── beam_search.py          # Parallel trajectory exploration
│   │   ├── behavioral_profiler.py  # OCEAN personality profiling
│   │   ├── coat_engine.py          # Contrastive style transfer
│   │   ├── orchestrator.py         # Kafka + Temporal bridge (85 lines)
│   │   ├── persistence.py          # Temporal persistence
│   │   ├── worker.py               # Temporal worker entry
│   │   ├── workflows/              # Temporal workflow definitions
│   │   └── activities/             # Temporal activity implementations
│   ├── shared/                     # Cross-subsystem contracts (3 files)
│   │   └── models.py               # Shared Pydantic models (180 lines)
│   └── adapters/                   # Platform adapters (3 files)
├── frontend/                       # React + TypeScript dashboard
│   ├── src/
│   │   ├── App.tsx                 # Root component
│   │   ├── pages/Dashboard.tsx     # 4-column layout
│   │   ├── components/             # 17 UI components
│   │   ├── hooks/                  # useWebSocket, useApi, useEngineStatus
│   │   └── types/tap.ts            # TypeScript type definitions
│   ├── package.json                # React 19, Tailwind 4, Vite 7
│   └── vite.config.ts              # Vite configuration
├── entrypoints/                    # Standalone entry scripts
│   ├── run_engine.py               # TAP engine idle loop
│   ├── run_stream.py               # X/Twitter stream listener
│   └── run_chronos.py              # Temporal worker
├── scripts/                        # Utility scripts
│   ├── seed_vgenome.py             # Seed Neo4j with attack techniques
│   ├── setup_db.py                 # Database setup
│   ├── verify_x_creds.py           # Verify X/Twitter credentials
│   ├── analyze_logs.py             # Analyze attack session logs
│   └── fix_*.py                    # Migration/fix scripts
├── tests/                          # Test suite (27 files)
├── migrations/                     # Alembic database migrations
├── data/                           # Runtime data (SQLite DB, logs, SSOT)
├── docs/                           # Documentation
├── .mimocode/                      # Research library (50+ documents)
├── docker-compose.infra.yml        # Infrastructure stack (8 services)
├── docker-compose.app.yml          # Application stack (5 services)
├── Dockerfile                      # Multi-stage Python build
├── Dockerfile.frontend             # Multi-stage Node.js build
├── pyproject.toml                  # Python project config
├── alembic.ini                     # Alembic migration config
├── AGENTS.md                       # AI agent instructions
├── RESEARCH.md                     # Research document catalog (50+ sources)
└── requirements.txt                # Python dependencies
```

---

## Research Library

50+ research documents in `.mimocode/Sources/` covering the full spectrum of LLM security research. See [RESEARCH.md](RESEARCH.md) for the complete catalog.

| Category | Key Documents | Focus |
|----------|---------------|-------|
| **TAP Framework** | #45 Tree of Attacks, #1 Protocollo TAP | Core methodology, automated jailbreaking |
| **Jailbreaking** | #49 AutoDAN, #47 Many-Shot, #44 SM-GCG | Stealthy attacks, long-context exploitation |
| **Prompt Injection** | #36 Indirect IPI, #43 QueryIPI, #42 Agentic | Indirect attacks, coding agent vulnerabilities |
| **Activation Steering** | #3 Activation 2026, #14 ODESteer, #18 RepE | Hidden state manipulation, alignment bypass |
| **Security** | #28 SentinelOne, #17 PriMod4AI, #5 AgentRAE | Threat modeling, backdoor detection |
| **Multimodal** | #33 Beyond Text, #41 PolyJailbreak, #35 FigStep | Cross-modal attacks, vision-language models |

---

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'feat: add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- **Type checking**: All code must pass `py -m mypy src/ --strict`
- **Linting**: `py -m ruff check src/` with 100-char line length
- **Testing**: Each test gets a fresh SQLite DB; mock LLM/Twitter dependencies
- **Imports**: Use `from tap.config import Settings`, `from hydra.v_genome import VGenomeClient`
- **PYTHONPATH**: `src/` (Docker: `/app/src`, local: `$env:PYTHONPATH="src"` in PowerShell)
