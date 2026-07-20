# TAP Framework v3.1 — Run Guide (VSCode Windows)

Step-by-step instructions to run the full TAP Framework stack from zero.

---

## Prerequisites

Install these before starting:

| Tool | Version | Link |
|------|---------|------|
| Docker Desktop | 4.x+ | https://docs.docker.com/desktop/install/windows-install/ |
| Node.js | 20.x LTS | https://nodejs.org/ (includes npm) |
| Python | 3.12.x | https://www.python.org/downloads/ (check "Add to PATH") |
| Git | latest | https://git-scm.com/download/win |
| VSCode | latest | https://code.visualstudio.com/ |

### VSCode Extensions (recommended)

```
ms-python.python
ms-python.vscode-pylance
dbaeumer.vscode-eslint
esbenp.prettier-vscode
bradlc.vscode-tailwindcss
```

### Verify installations

Open PowerShell and run:

```powershell
docker --version          # Docker 27.x+
docker compose version    # Docker Compose v2
node --version            # v20.x+
npm --version             # 10.x+
py -3 --version           # Python 3.12.x+
git --version             # 2.x+
```

---

## 1. Clone the Repository

```powershell
cd L:\PROGETTI
git clone https://github.com/CarlSamma/Hybrid.git
cd Hybrid
git checkout Hybridv4Mimo
```

---

## 2. Create the `.env` File

The application requires a `.env` file in the project root with ~50 environment variables.

### Option A: Copy from backup (if available)

```powershell
Copy-Item .env.data .env
```

Then edit `.env` and replace placeholder values with your actual credentials.

### Option B: Create from scratch

Create `.env` in the project root with these sections:

```env
# === Twitter API v2 — OAuth 2.0 Bearer Token (search/read) ===
TWITTER_BEARER_TOKEN=your_bearer_token_here

# === Twitter API v2 — OAuth 1.0a (posting) ===
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# === Twitter API v2 — OAuth 2.0 User Context (PKCE) ===
TWITTER_OAUTH2_CLIENT_ID=your_oauth2_client_id
TWITTER_OAUTH2_CLIENT_SECRET=your_oauth2_client_secret
TWITTER_OAUTH2_ACCESS_TOKEN=
TWITTER_OAUTH2_REFRESH_TOKEN=
TWITTER_CALLBACK_URL=http://localhost:8000/api/auth/callback

# === OpenRouter (all LLMs) ===
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL_PRIMARY=anthropic/claude-sonnet-4
OPENROUTER_MODEL_HARD=x-ai/grok-4.3
OPENROUTER_MODEL_GROK=x-ai/grok-4

# === Target ===
TARGET_HANDLE=HackingA0
OUR_BOT_HANDLE=

# === Operational ===
POLL_INTERVAL_SECONDS=30
POST_COOLDOWN_SECONDS=60
MAX_TWEETS_PER_HOUR=50
REPLY_TIMEOUT_SECONDS=200
TAP_WIDTH=10
TAP_DEPTH=10
TAP_BRANCHING=4

# === Paths ===
DB_PATH=data/tap.db
SSOT_PATH=data/hackinga0_analysis.md
LOG_FILE_PATH=data/server.log

# === v3.0 Flags ===
USE_UNIFIED_LLM_CLIENT=True
USE_PROMPT_SANITISER=True
USE_STRATEGY_SELECTOR=True
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60.0
ENABLE_CORRELATION_IDS=True
ENABLE_EVENT_LOG=True
ENABLE_PARALLEL_PIPELINE=True
DB_WRITE_QUEUE_THRESHOLD=5.0

# === v4 Phase 5 ===
PHASE5_ENTROPY_THRESHOLD=3.3
STIR_ROTATION_THRESHOLD=0.20
ORACLE_LATENCY_SECONDS=180
EIG_PROPERTY_UNIVERSE_PATH=data/eig_property_universe.json

# === HYDRA (Neo4j) ===
HYDRA_NEO4J_URI=bolt://localhost:7687
HYDRA_NEO4J_USER=neo4j
HYDRA_NEO4J_PASSWORD=tapv4hydra

# === HYDRA (Kafka) ===
HYDRA_KAFKA_BOOTSTRAP=localhost:9092

# === HYDRA (ClickHouse) ===
HYDRA_CLICKHOUSE_HOST=localhost
HYDRA_CLICKHOUSE_PORT=8123
HYDRA_CLICKHOUSE_USER=tap
HYDRA_CLICKHOUSE_PASSWORD=tap

# === CHRONOS (PostgreSQL) ===
CHRONOS_DB_DSN=postgresql://tap:tap@localhost:5432/chronos
CHRONOS_TEMPORAL_HOST=localhost:7233
CHRONOS_TEMPORAL_NAMESPACE=default
CHRONOS_KAFKA_BOOTSTRAP=localhost:9092
CHRONOS_REDIS_URL=redis://localhost:6379/0
CHRONOS_WORKER_IDENTITY=chronos-worker-01
```

> **Important**: The `.env` file is git-ignored. Never commit it.

---

## 3. Start Infrastructure (Docker)

The infrastructure stack provides databases, message queues, and supporting services.

```powershell
docker compose -f docker-compose.infra.yml up -d
```

**Services started** (8 containers):

| Service | Port | Purpose |
|---------|------|---------|
| `postgres` | 5432 | PostgreSQL 16 |
| `neo4j` | 7474, 7687 | Neo4j 5.x graph DB |
| `kafka` | 9092 | Apache Kafka |
| `zookeeper` | (internal) | Kafka coordination |
| `debezium` | 8083 | CDC connector |
| `redis` | 6379 | Cache + circuit breaker |
| `temporal` | 7233 | Workflow orchestration |
| `temporal-ui` | 8233 | Temporal dashboard |
| `minio` | 9000, 9001 | Object storage |
| `clickhouse` | 8123 | Analytics DB |

Wait for all services to be healthy (~30-60 seconds):

```powershell
docker compose -f docker-compose.infra.yml ps
```

All should show `Up` or `healthy` status.

---

## 4. Start Application (Docker)

```powershell
docker compose -f docker-compose.app.yml up -d --build
```

**Services started** (5 containers):

| Service | Port | URL |
|---------|------|-----|
| `hydra-api` | 8000 | http://localhost:8000 (API + Swagger docs) |
| `frontend` | 3000 | http://localhost:3000 (React dashboard) |
| `tap-engine` | — | Core engine (HITL idle loop) |
| `adapters` | — | X/Twitter stream listener |
| `chronos-worker` | — | Temporal workflow worker |

Wait for the API to become healthy:

```powershell
# Wait until this returns 200
Invoke-RestMethod -Uri http://localhost:8000/health
```

Open in browser:
- **Dashboard**: http://localhost:3000
- **API Docs (Swagger)**: http://localhost:8000/docs
- **API Docs (ReDoc)**: http://localhost:8000/redoc
- **Temporal UI**: http://localhost:8233
- **Neo4j Browser**: http://localhost:7474 (login: `neo4j` / `tapv4hydra`)
- **MinIO Console**: http://localhost:9001 (login: `tap` / `tapv4minio`)

---

## 5. Seed V-Genome (Attack Techniques)

After infrastructure is running, seed Neo4j with attack techniques:

```powershell
# Option A: Run inside Docker (recommended)
docker exec -it tap-hydra-api python scripts/seed_vgenome.py

# Option B: Run locally (requires neo4j pip package + Neo4j accessible on localhost:7687)
$env:PYTHONPATH="src"; py -3 scripts/seed_vgenome.py
```

This is idempotent — safe to re-run.

---

## 6. Verify X/Twitter Credentials

```powershell
py -3 scripts/verify_x_creds.py
```

This tests:
- Bearer token (search/read)
- OAuth 1.0a (posting)
- OAuth 2.0 User Context (Activity API)

### OAuth 2.0 PKCE Flow (first time)

1. Open: http://localhost:8000/api/auth/login
2. Authorize in browser
3. Tokens are saved to `.env` automatically

---

## 7. Local Development (without Docker)

For faster iteration, run services locally instead of in Docker.

### Terminal 1: API Server

```powershell
cd L:\PROGETTI\Hybrid\Hybrid
$env:PYTHONPATH="src"
py -3 -m uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Frontend Dev Server

```powershell
cd L:\PROGETTI\Hybrid\Hybrid\frontend
npm install
npm run dev
```

Vite proxies `/api` to `http://localhost:8000` automatically.

### Terminal 3: Engine (optional)

```powershell
cd L:\PROGETTI\Hybrid\Hybrid
$env:PYTHONPATH="src"
py -3 entrypoints/run_engine.py
```

### Terminal 4: Stream Listener (optional)

```powershell
cd L:\PROGETTI\Hybrid\Hybrid
$env:PYTHONPATH="src"
py -3 entrypoints/run_stream.py
```

> **Note**: Infrastructure services (PostgreSQL, Neo4j, Kafka, etc.) still need to run via Docker.

---

## 8. Useful Commands

### Docker

```powershell
# View running containers
docker compose -f docker-compose.infra.yml ps
docker compose -f docker-compose.app.yml ps

# View logs (follow mode)
docker compose -f docker-compose.app.yml logs -f hydra-api
docker compose -f docker-compose.app.yml logs -f frontend
docker compose -f docker-compose.app.yml logs -f adapters

# Rebuild a single service
docker compose -f docker-compose.app.yml up -d --build hydra-api

# Stop everything
docker compose -f docker-compose.app.yml down
docker compose -f docker-compose.infra.yml down

# Stop and remove volumes (full reset)
docker compose -f docker-compose.app.yml down -v
docker compose -f docker-compose.infra.yml down -v
```

### Python

```powershell
# Run tests (267 pass, 2 pre-existing torch failures)
py -3 -m pytest tests -q --ignore=tests/integration

# Run tests excluding torch-dependent tests
py -3 -m pytest tests -q --ignore=tests/integration -k "not cast_steering and not layer_steering"

# Lint
ruff check src/

# Type check
mypy src/ --strict
```

### Database

```powershell
# Initialize SQLite
py -3 scripts/setup_db.py

# Analyze server logs
py -3 scripts/analyze_logs.py
```

---

## 9. Architecture Overview

```
                    ┌──────────────────────────────┐
                    │     Frontend (React/Vite)     │
                    │        http://localhost:3000   │
                    └──────────┬───────────────────┘
                               │ /api, /ws
                    ┌──────────▼───────────────────┐
                    │    FastAPI (hydra-api:8000)    │
                    │  TAP Engine + Stream Listener  │
                    └──┬───────┬───────┬───────────┘
                       │       │       │
          ┌────────────▼┐  ┌───▼───┐  ┌▼────────────┐
          │   SQLite     │  │ Neo4j │  │  OpenRouter  │
          │  (tap.db)    │  │  5.x  │  │ (LLM calls)  │
          └──────────────┘  └───────┘  └──────────────┘
                       │       │
          ┌────────────▼───────▼──────────────┐
          │     Docker Infrastructure          │
          │  PostgreSQL · Kafka · Redis · etc  │
          └───────────────────────────────────┘
```

---

## 10. Troubleshooting

### Port already in use

```powershell
# Find process using port 8000
netstat -ano | findstr :8000
# Kill it (replace PID)
taskkill /PID <PID> /F
```

### Docker containers not starting

```powershell
# Check Docker Desktop is running
docker info

# Check for port conflicts
docker compose -f docker-compose.infra.yml logs postgres
docker compose -f docker-compose.infra.yml logs neo4j
```

### API returns 500 errors

```powershell
# Check API logs
docker logs tap-hydra-api --tail 50

# Common fix: rebuild with fresh context
docker compose -f docker-compose.app.yml up -d --build hydra-api
```

### .env not loaded in Docker

The `.env` file is mounted as a volume. If you edit it locally, rebuild:

```powershell
docker compose -f docker-compose.app.yml up -d --build hydra-api
```

### Activity API returns 403

This is expected on the X API Free tier. The system automatically falls back to **Grok x_search** via OpenRouter for tweet monitoring. No action required.

### Frontend shows "Cannot connect to API"

Ensure the API is running and the Vite proxy is configured:

```powershell
# Verify API is up
Invoke-RestMethod -Uri http://localhost:8000/health

# Frontend proxy config is in frontend/vite.config.ts
# /api -> http://localhost:8000
# /ws   -> ws://localhost:8000
```

### Neo4j auth failed

Default credentials: `neo4j` / `tapv4hydra`
Reset: delete `neo4j_data` volume and restart.

---

## 11. Quick Start (TL;DR)

```powershell
cd L:\PROGETTI\Hybrid\Hybrid

# 1. Create .env (see step 2)
notepad .env

# 2. Start infrastructure
docker compose -f docker-compose.infra.yml up -d

# 3. Start application
docker compose -f docker-compose.app.yml up -d --build

# 4. Wait for health check
Start-Sleep -Seconds 30
Invoke-RestMethod -Uri http://localhost:8000/health

# 5. Open dashboard
Start-Process http://localhost:3000

# 6. Seed attack techniques (one-time)
docker exec -it tap-hydra-api python scripts/seed_vgenome.py

# 7. Verify X credentials
py -3 scripts/verify_x_creds.py
```

---

## File Reference

| File | Purpose |
|------|---------|
| `.env` | Environment variables (git-ignored) |
| `docker-compose.infra.yml` | Infrastructure stack (8 services) |
| `docker-compose.app.yml` | Application stack (5 services) |
| `Dockerfile` | Python multi-stage build (API, engine, stream, chronos) |
| `Dockerfile.frontend` | React/Vite frontend build |
| `src/tap/api.py` | FastAPI application entrypoint |
| `src/tap/config.py` | Settings class (all env vars) |
| `src/tap/engine.py` | Core TAP engine loop |
| `src/tap/stream_listener.py` | X Activity API stream listener |
| `src/tap/grok_monitor.py` | Grok-based tweet monitoring (x_search fallback) |
| `entrypoints/run_engine.py` | Engine entrypoint (Docker) |
| `entrypoints/run_stream.py` | Stream listener entrypoint (Docker) |
| `entrypoints/run_chronos.py` | Temporal worker entrypoint (Docker) |
| `scripts/seed_vgenome.py` | Seed Neo4j with attack techniques |
| `scripts/verify_x_creds.py` | Verify X API credentials |
| `frontend/` | React + TypeScript + Vite frontend |
