# TAP Framework v3.0 — Installazione e Avvio su Windows/VSCode

> Guida passo-passo per installare e avviare il TAP Framework su Windows con VSCode.

---

## Prerequisiti

### Software Necessari

| Software | Versione | Link Download |
|----------|----------|---------------|
| **Python** | 3.11+ | https://www.python.org/downloads/ |
| **Node.js** | 18+ | https://nodejs.org/ |
| **Git** | Ultima | https://git-scm.com/download/win |
| **VSCode** | Ultima | https://code.visualstudio.com/ |
| **Neo4j** | 5.x | https://neo4j.com/download/ |
| **Docker Desktop** | Ultima | https://www.docker.com/products/docker-desktop/ |

### Verifica Installazioni

Apri PowerShell e verifica:

```powershell
python --version      # deve mostrare Python 3.11+
node --version        # deve mostrare Node.js 18+
git --version         # deve mostrare Git version
code --version        # deve mostrare VSCode
```

---

## Step 1: Clone del Repository

```powershell
# Scegli una directory di lavoro
cd D:\PROGETTI

# Clona il repository
git clone https://github.com/CarlSamma/Hybrid.git

# Entra nella directory
cd Hybrid
```

---

## Step 2: Configurazione Python

### 2.1 Crea Virtual Environment

```powershell
# Crea il venv
python -m venv .venv

# Attiva il venv (PowerShell)
.venv\Scripts\Activate.ps1

# Se ricevi errore di esecuzione:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.2 Installa Dipendenze Backend

```powershell
# Installa requirements
pip install -r requirements.txt

# Installa dipendenze dev (opzionale)
pip install pytest pytest-asyncio mypy ruff
```

### 2.3 Verifica Installazione

```powershell
python -c "import fastapi; print('FastAPI:', fastapi.__version__)"
python -c "import uvicorn; print('Uvicorn OK')"
python -c "import tweepy; print('Tweepy OK')"
```

---

## Step 3: Configurazione Frontend

### 3.1 Installa Dipendenze Frontend

```powershell
# Entra nella directory frontend
cd frontend

# Installa dipendenze
npm install

# Torna alla root
cd ..
```

### 3.2 Verifica Frontend

```powershell
cd frontend
npm run build
# Se build OK, il frontend è pronto
cd ..
```

---

## Step 4: Configurazione Ambiente

### 4.1 Crea File .env

Crea il file `.env` nella root del progetto:

```powershell
# Crea il file .env
@"
# Twitter/X API Credentials
TWITTER_BEARER_TOKEN=your_bearer_token_here
TWITTER_CONSUMER_KEY=your_consumer_key_here
TWITTER_CONSUMER_SECRET=your_consumer_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret_here
TWITTER_OAUTH2_ACCESS_TOKEN=your_oauth2_token_here

# Target
TARGET_HANDLE=@HackingA0
OUR_BOT_HANDLE=@your_bot_handle

# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_key_here

# Models
PRIMARY_MODEL=anthropic/claude-sonnet-4
HARD_MODEL=x-ai/grok-4.3
GROK_MODEL=x-ai/grok-4

# Neo4j (per V-Genome)
HYDRA_NEO4J_URI=bolt://localhost:7687
HYDRA_NEO4J_USER=neo4j
HYDRA_NEO4J_PASSWORD=tapv4hydra

# Database
DB_PATH=data/tap.db
SSOT_PATH=data/hackinga0_ssot.md

# Server
API_HOST=0.0.0.0
API_PORT=8000
"@ | Out-File -FilePath .env -Encoding utf8
```

### 4.2 Modifica le Credenziali

Apri `.env` e sostituisci i valori placeholder con le tue credenziali reali.

---

## Step 5: Configurazione VSCode

### 5.1 Apri il Progetto

```powershell
code .
```

### 5.2 Installa Estensioni Consigliate

| Estensione | ID | Scopo |
|------------|-----|-------|
| Python | ms-python.python | Supporto Python |
| Pylance | ms-python.vscode-pylance | Type checking |
| ESLint | dbaeumer.vscode-eslint | Linting JS/TS |
| Tailwind CSS | bradlc.vscode-tailwindcss | Supporto Tailwind |
| GitLens | eamodio.gitlens | Git history |

### 5.3 Configura Python Interpreter

1. Premi `Ctrl+Shift+P`
2. Cerca "Python: Select Interpreter"
3. Seleziona `.venv\Scripts\python.exe`

### 5.4 Configura Launch (opzionale)

Crea `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "TAP Server",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["tap.api:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      },
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

---

## Step 6: Neo4j (Opzionale - per V-Genome)

### 6.1 Avvia Neo4j con Docker

```powershell
# Avvia Neo4j
docker run -d --name neo4j-tap `
  -p 7474:7474 -p 7687:7687 `
  -e NEO4J_AUTH=neo4j/tapv4hydra `
  -e NEO4J_PLUGINS='["apoc"]' `
  neo4j:5
```

### 6.2 Seed Tecniche di Attacco

```powershell
# Con Neo4j in esecuzione
python scripts/seed_vgenome.py
```

### 6.3 Verifica Neo4j Browser

Apri http://localhost:7474 nel browser:
- Username: `neo4j`
- Password: `tapv4hydra`

---

## Step 7: Avvio del Sistema

### 7.1 Avvia Backend

```powershell
# Assicurati di essere nella root del progetto
# Con venv attivato

# Opzione 1: Comando diretto
PYTHONPATH=src uvicorn tap.api:app --reload --host 0.0.0.0 --port 8000

# Opzione 2: Da VSCode (usa launch.json)
# Premi F5 o Run > Start Debugging
```

### 7.2 Avvia Frontend (sviluppo)

```powershell
# In un secondo terminale
cd frontend
npm run dev
```

### 7.3 Verifica Avvio

| Servizio | URL | Descrizione |
|----------|-----|-------------|
| **API Backend** | http://localhost:8000 | FastAPI server |
| **Dashboard** | http://localhost:8000 | UI principale |
| **API Docs** | http://localhost:8000/docs | Swagger UI |
| **Health** | http://localhost:8000/health | Stato sistema |
| **Frontend Dev** | http://localhost:5173 | Vite dev server |

---

## Step 8: Verifica Funzionamento

### 8.1 Test Health Endpoint

```powershell
curl http://localhost:8000/health
```

### 8.2 Test API Feed

```powershell
curl http://localhost:8000/api/feed
```

### 8.3 Apri Dashboard

Apri http://localhost:8000 nel browser.

---

## Comandi Utili

### Server

```powershell
# Avvia con auto-reload
PYTHONPATH=src uvicorn tap.api:app --reload

# Avvia su porta specifica
PYTHONPATH=src uvicorn tap.api:app --port 8080

# Avvia in produzione
PYTHONPATH=src uvicorn tap.api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Testing

```powershell
# Esegui tutti i test
python -m pytest tests -q

# Test specifico
python -m pytest tests/test_models.py -v

# Test con coverage
python -m pytest tests --cov=src
```

### Code Quality

```powershell
# Type check
mypy src/ --strict

# Lint
ruff check src/

# Format
ruff format src/
```

### V-Genome

```powershell
# Seed tecniche (idempotente)
python scripts/seed_vgenome.py

# Verifica credenziali X
python scripts/verify_x_creds.py
```

---

## Docker (Alternativa)

### Avvia Infrastruttura

```powershell
docker compose -f docker-compose.infra.yml up -d
```

### Avvia Applicazione

```powershell
docker compose -f docker-compose.app.yml up -d --build
```

### Servizi Docker

| Servizio | Porta | Descrizione |
|----------|-------|-------------|
| neo4j | 7474, 7687 | Graph database |
| kafka | 9092 | Event bus |
| postgres | 5432 | CHRONOS database |
| redis | 6379 | Cache |
| temporal | 8088 | Workflow engine |

---

## Troubleshooting

### Errore: "Module not found"

```powershell
# Verifica PYTHONPATH
$env:PYTHONPATH="src"
python -c "import tap; print('OK')"
```

### Errore: "Address already in use"

```powershell
# Trova il processo che usa la porta
netstat -ano | findstr :8000

# Termina il processo
taskkill /PID <PID> /F
```

### Errore: "Neo4j not connected"

```powershell
# Verifica che Neo4j sia in esecuzione
docker ps | findstr neo4j

# Riavvia se necessario
docker restart neo4j-tap
```

### Errore: "Twitter auth failed"

1. Verifica le credenziali nel file `.env`
2. Esegui `python scripts/verify_x_creds.py`
3. Controlla che i token non siano scaduti

### Errore: "OpenRouter API error"

1. Verifica `OPENROUTER_API_KEY` nel `.env`
2. Controlla il saldo su https://openrouter.ai

---

## Struttura Progetto

```
framework/
├── src/
│   ├── tap/                    # Core TAP engine
│   ├── hydra/                  # V-Genome + Fusion Engine
│   ├── chronos/                # Temporal workflows
│   ├── shared/                 # Modelli condivisi
│   └── adapters/               # Social adapters
├── frontend/                   # React/TypeScript UI
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docs/research/              # Research findings
├── data/                       # Database + SSOT
├── .env                        # Configurazione (non committare)
└── requirements.txt            # Dipendenze Python
```

---

## Risorse

- **Documentazione API**: http://localhost:8000/docs
- **GitHub**: https://github.com/CarlSamma/Hybrid
- **Branch**: `Hybridv4Mimo`

---

*Guida aggiornata: 2026-07-04*
*TAP Framework v3.0.0 — Hybridv4Mimo*
