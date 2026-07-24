# TAPaware — Running on Windows (VS Code)

Step-by-step guide to set up and run the full TAPaware stack from VS Code on Windows.

---

## Prerequisites

| Software | Min Version | Download | Verify |
|----------|-------------|----------|--------|
| **Python** | 3.11+ | [python.org](https://www.python.org/downloads/) | `python --version` |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) | `node --version` |
| **Git** | Latest | [git-scm.com](https://git-scm.com/download/win) | `git --version` |
| **Docker Desktop** | Latest | [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/) | `docker --version` |
| **VS Code** | Latest | [code.visualstudio.com](https://code.visualstudio.com/) | `code --version` |

> During Python installation, check **"Add Python to PATH"**.

Open PowerShell and verify:

```powershell
python --version       # 3.11.x or higher
node --version         # v18.x or higher
docker --version       # Docker version 24.x
git --version          # git version 2.x
```

### VS Code Extensions

Install these extensions in VS Code (`Ctrl+Shift+X`):
- **Python** (`ms-python.python`)
- **Pylance** (`ms-python.vscode-pylance`)
- **Docker** (`ms-azuretools.vscode-docker`)

---

## Step 1: Clone & Open

```powershell
cd L:\PROGETTI
git clone https://github.com/CarlSamma/TAPaware.git
cd TAPaware
code .
```

VS Code opens the **workspace root** (`TAPaware/`), not `tap-app/`.

---

## Step 2: Create Virtual Environment

Open the VS Code terminal (`Ctrl+` backtick) and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks execution:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Verify the venv is active (you should see `(.venv)` in the prompt):

```powershell
python --version
```

---

## Step 3: Install the Aware Library

From the workspace root (`TAPaware/`):

```powershell
pip install -e ".[dev]"
```

This installs the `aware` memory library in editable mode. Verify:

```powershell
python -c "import aware; print(aware.__version__)"
# Should print: 0.1.0
```

---

## Step 4: Install the TAP App

```powershell
cd tap-app
pip install -e ".[dev,hybrid]"
cd ..
```

This installs the TAP Framework with all dependencies, including the `aware` library as a path dependency. Verify:

```powershell
python -c "import tap; print(tap.__version__)"
# Should print: 3.1.0
```

---

## Step 5: Configure Environment Variables

```powershell
cd tap-app
copy .env.example .env
cd ..
```

Open `tap-app/.env` in VS Code and fill in at minimum:

```ini
# Required: OpenRouter API key (for LLM calls)
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Required: Twitter API credentials (for posting probes)
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_CONSUMER_KEY=your_consumer_key
TWITTER_CONSUMER_SECRET=your_consumer_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
```

All other values have working defaults for local development.

---

## Step 6: Create Data Directory

```powershell
mkdir tap-app\data -ErrorAction SilentlyContinue
```

---

## Step 7: Start Infrastructure (Docker)

```powershell
cd tap-app
docker compose -f docker-compose.infra.yml up -d
cd ..
```

This starts 10 services: PostgreSQL, Neo4j, Kafka, Zookeeper, Debezium, Redis, Temporal, Temporal UI, MinIO, ClickHouse.

Wait ~30 seconds for all services to become healthy:

```powershell
cd tap-app
docker compose -f docker-compose.infra.yml ps
cd ..
```

All services should show `Up` status. Key ports:

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | `postgresql://localhost:5432` |
| Neo4j Browser | 7474 | http://localhost:7474 |
| Kafka | 9092 | `localhost:9092` |
| Redis | 6379 | `localhost:6379` |
| Temporal UI | 8233 | http://localhost:8233 |
| MinIO Console | 9001 | http://localhost:9001 |
| ClickHouse | 8123 | http://localhost:8123 |

---

## Step 8: Seed V-Genome (Neo4j)

```powershell
cd tap-app
$env:PYTHONPATH="src"
python scripts/seed_vgenome.py
cd ..
```

This loads 10+ attack techniques into Neo4j. Idempotent — safe to re-run.

---

## Step 9: Run Database Migrations

```powershell
cd tap-app
$env:PYTHONPATH="src"
alembic upgrade head
cd ..
```

Creates the CHRONOS tables in PostgreSQL.

---

## Step 10: Start the API Server

**Option A — PowerShell terminal:**

```powershell
cd tap-app
$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

**Option B — VS Code launch config (F5):**

Create `.vscode/launch.json` in the workspace root:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "TAP API Server",
            "type": "debugpy",
            "request": "launch",
            "module": "uvicorn",
            "args": ["tap.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            "cwd": "${workspaceFolder}/tap-app",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/tap-app/src"
            },
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Run Tests (aware)",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests", "-v", "-p", "no:postgresql"],
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal"
        },
        {
            "name": "Run Tests (tap-app)",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests", "-v", "--ignore=tests/integration"],
            "cwd": "${workspaceFolder}/tap-app",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/tap-app/src"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

Then press **F5** and select "TAP API Server".

---

## Step 11: Start the Frontend (Dashboard)

Open a **second terminal** in VS Code (`Ctrl+Shift+` backtick):

```powershell
cd tap-app\frontend
npm install
npm run dev
```

---

## Step 12: Open in Browser

| What | URL |
|------|-----|
| **Dashboard GUI** | http://localhost:3000 |
| **API Docs (Swagger)** | http://localhost:8000/docs |
| **Neo4j Browser** | http://localhost:7474 (login: `neo4j` / `tapv4hydra`) |
| **Temporal UI** | http://localhost:8233 |

Verify the backend is running:

```powershell
curl http://localhost:8000/health
```

---

## Running Tests

### Aware library tests (from workspace root):

```powershell
python -m pytest tests/ -v -p no:postgresql
```

### TAP app tests (from tap-app/):

```powershell
cd tap-app
$env:PYTHONPATH="src"
python -m pytest tests/ -v --ignore=tests/integration
```

Skip the `-p no:postgresql` flag is not needed for tap-app tests (they don't use the aware conftest).

---

## Quick Start (Minimal — No Docker)

If you only need the core TAP engine with SQLite (no Neo4j/Kafka/PostgreSQL):

```powershell
# From workspace root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"

cd tap-app
pip install -e ".[dev]"
mkdir data -ErrorAction SilentlyContinue

$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --port 8000
```

The core attack loop works. HYDRA/CHRONOS features will be unavailable.

---

## Stopping Everything

```powershell
# Stop infrastructure
cd tap-app
docker compose -f docker-compose.infra.yml down

# Stop app services (if running via docker compose)
docker compose -f docker-compose.app.yml down

# Deactivate venv
deactivate
```

To also remove volumes (full reset):

```powershell
cd tap-app
docker compose -f docker-compose.infra.yml down -v
```

---

## Troubleshooting

### `python` not found

Use the venv Python directly:

```powershell
& ".venv\Scripts\python.exe" --version
```

Or use the `py` launcher:

```powershell
py -3.11 --version
```

### `Set-ExecutionPolicy` error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### `aware` import fails

Make sure you installed from the workspace root:

```powershell
# From TAPaware/ (not tap-app/)
pip install -e ".[dev]"
```

### `tap` import fails

Make sure you installed from tap-app/:

```powershell
cd tap-app
pip install -e ".[dev,hybrid]"
```

### Docker: `hybrid_default` network error

This was a known issue — now fixed. The network is named `tap-net`. If you see this error, make sure you have the latest code:

```powershell
git pull
```

### PostgreSQL: `hydra` database does not exist

This was a known issue — now fixed. An init script creates it automatically. If it still fails:

```powershell
cd tap-app
docker compose -f docker-compose.infra.yml down -v
docker compose -f docker-compose.infra.yml up -d
```

### Kafka connection timeout

Kafka takes ~15 seconds to start. Check logs:

```powershell
cd tap-app
docker compose -f docker-compose.infra.yml logs kafka
```

### `pytest-postgresql` crashes on import

The root `aware` tests require `-p no:postgresql`:

```powershell
python -m pytest tests/ -v -p no:postgresql
```

### `PYTHONPATH` not set

Every PowerShell session needs this for tap-app:

```powershell
$env:PYTHONPATH="src"
```

Or use the VS Code launch config (F5) which sets it automatically.

### Port already in use

Check what's using the port:

```powershell
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## Full Reset

If everything is broken:

```powershell
# Stop all Docker containers
docker compose -f tap-app/docker-compose.infra.yml down -v
docker compose -f tap-app/docker-compose.app.yml down

# Reinstall
pip install -e ".[dev]"
cd tap-app
pip install -e ".[dev,hybrid]"
mkdir data -ErrorAction SilentlyContinue

# Restart infrastructure
docker compose -f docker-compose.infra.yml up -d
Start-Sleep -Seconds 30

# Seed and migrate
$env:PYTHONPATH="src"
python scripts/seed_vgenome.py
alembic upgrade head

# Start server
uvicorn tap.api:app --reload --port 8000
```
