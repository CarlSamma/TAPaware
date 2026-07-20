# TAP Framework — Running on Windows (VSCode)

## Prerequisites

- **Python 3.11+** (check: `python --version`)
- **Docker Desktop** (for infrastructure services)
- **VSCode** with Python extension
- **Git**

## 1. Clone & Open

```powershell
git clone <repo-url>
cd framework
code .
```

## 2. Create Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 3. Install Dependencies

```powershell
pip install -e ".[dev]"
```

Or alternatively:
```powershell
pip install -r requirements.txt
pip install -r requirements-hybrid.txt
```

## 4. Configure Environment

Copy and edit the `.env` file (already present with dev credentials):
```powershell
copy .env .env.backup   # optional backup
notepad .env
```

Verify these are set (defaults work for local dev):
```
DB_PATH=data/tap.db
SSOT_PATH=data/hackinga0_analysis.md
TARGET_HANDLE=HackingA0
OPENROUTER_API_KEY=sk-or-v1-...
HYDRA_NEO4J_URI=bolt://localhost:7687
CHRONOS_DB_DSN=postgresql://tap:tap@localhost:5432/chronos
```

## 5. Create Data Directory

```powershell
mkdir data
```

## 6. Start Infrastructure (Docker)

```powershell
docker compose -f docker-compose.infra.yml up -d
```

This starts:
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 5432 | CHRONOS persistence |
| Neo4j 5.x | 7474, 7687 | V-Genome graph |
| Kafka + Zookeeper | 9092, 29092 | Event bus |
| Redis | 6369 | Caching |
| Temporal | 7233 | Workflow orchestration |

Wait ~30 seconds for services to be healthy:
```powershell
docker compose -f docker-compose.infra.yml ps
```

## 7. Seed V-Genome (Neo4j)

```powershell
$env:PYTHONPATH="src"
python scripts/seed_vgenome.py
```

This is idempotent — safe to re-run.

## 8. Run Database Migrations

```powershell
$env:PYTHONPATH="src"
alembic upgrade head
```

## 9. Start the API Server

```powershell
$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

Or equivalently:
```powershell
$env:PYTHONPATH="src"
python -m uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000
```

**API docs**: http://localhost:8000/docs

## 10. Verify It Works

```powershell
curl http://localhost:8000/api/health
```

Or open in browser: http://localhost:8000/api/health

---

## VSCode Launch Configuration

Create `.vscode/launch.json` for F5 debugging:

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
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            },
            "console": "integratedTerminal",
            "justMyCode": false
        },
        {
            "name": "Run Tests",
            "type": "debugpy",
            "request": "launch",
            "module": "pytest",
            "args": ["tests", "-v", "--tb=short", "--ignore=tests/integration"],
            "cwd": "${workspaceFolder}",
            "env": {
                "PYTHONPATH": "${workspaceFolder}/src"
            },
            "console": "integratedTerminal"
        }
    ]
}
```

---

## VSCode Settings

Create `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/.venv/Scripts/python.exe",
    "python.envFile": "${workspaceFolder}/.env",
    "python.terminal.envVariables": {
        "PYTHONPATH": "${workspaceFolder}/src"
    },
    "editor.formatOnSave": true,
    "python.analysis.typeCheckingMode": "basic"
}
```

---

## Run Tests

```powershell
$env:PYTHONPATH="src"
python -m pytest tests/ -v --tb=short --ignore=tests/integration
```

Skip integration tests (require kafka/neo4j/postgres Docker services):
```powershell
python -m pytest tests/ -v --ignore=tests/integration
```

---

## Troubleshooting

### `python` not found
Use the venv Python directly:
```powershell
& ".venv\Scripts\python.exe" -m pytest tests/
```

### `psycopg` / PostgreSQL import error
Tests that need PostgreSQL will fail locally — use `--ignore=tests/integration` flag:
```powershell
python -m pytest tests/ --ignore=tests/integration
```

### `kafka` module not found
Integration tests import `kafka-python`. Either install it or skip integration tests:
```powershell
pip install kafka-python
# OR skip integration tests:
python -m pytest tests/ --ignore=tests/integration
```

### Neo4j connection refused
Ensure Docker is running:
```powershell
docker ps | findstr neo4j
```

### Kafka connection timeout
Kafka takes ~15 seconds to start. Wait and retry:
```powershell
docker compose -f docker-compose.infra.yml logs kafka
```

### `PYTHONPATH` not set
Every PowerShell session needs:
```powershell
$env:PYTHONPATH="src"
```
Or add it to `.vscode/settings.json` as shown above.

---

## Quick Start (Minimal — No Docker)

If you only need the core TAP engine (SQLite only, no HYDRA/CHRONOS):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
mkdir data
$env:PYTHONPATH="src"
uvicorn tap.api:app --reload --port 8000
```

This runs with SQLite only. Neo4j/Kafka/PostgreSQL features will be unavailable but the core attack loop works.
