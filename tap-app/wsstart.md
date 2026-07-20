# Quick Start — TAP Framework (Branch hybrid)

## Prerequisiti
- Docker Desktop avviato (icona verde nella taskbar)
- Python 3.11+ installato
- Node.js 18+ installato (solo per la dashboard GUI)

---

## 1. Attiva il virtual environment

```powershell
cd L:\PROGETTI\Framework160626\framework
.venv\Scripts\Activate.ps1
```

## 2. Avvia l'infrastruttura Docker

```powershell
docker compose -f docker-compose.infra.yml up -d
```

Aspetta ~30 secondi che tutti i container siano `running`.

## 3. Migrazioni e seed V-Genome

```powershell
$env:PYTHONPATH = "src"
alembic upgrade head
python scripts/seed_vgenome.py
```

## 4. Avvia il Backend (API + Engine)

```powershell
$env:PYTHONPATH = "src"
uvicorn tap.api:app --reload --port 8000
```

## 5. Avvia il Frontend (Dashboard GUI)

Apri un **secondo terminale**:

```powershell
cd L:\PROGETTI\Framework160626\framework\frontend
npm run dev
```

## 6. Apri il Browser

- **Dashboard GUI**: http://localhost:3000
- **API docs**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (login: `neo4j` / `tapv4hydra`)

---

## Verifica rapida

```powershell
# Health check backend
curl http://localhost:8000/health
```

## Reset completo (se qualcosa va storto)

```powershell
docker compose -f docker-compose.infra.yml down -v
docker compose -f docker-compose.infra.yml up -d
python scripts/seed_vgenome.py
```
