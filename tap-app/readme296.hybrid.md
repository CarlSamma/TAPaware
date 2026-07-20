# 🚀 Guida Avvio — Branch `hybrid` su Windows con VS Code
### Repo: https://github.com/CarlSamma/framework.git
### Versione: APPOpzioneIbrida v1.0.0 (HYDRA + CHRONOS)

---

## ✅ COSA TI SERVE PRIMA DI INIZIARE

Installa questi strumenti **nell'ordine indicato**. Ogni link porta al download ufficiale.

| Strumento | Versione minima | Link |
|---|---|---|
| **Git** | qualsiasi recente | https://git-scm.com/download/win |
| **Python** | 3.11 o 3.12 | https://www.python.org/downloads/ |
| **VS Code** | qualsiasi recente | https://code.visualstudio.com/ |
| **Docker Desktop** | qualsiasi recente | https://www.docker.com/products/docker-desktop/ |
| **Node.js** | 18+ (solo per la dashboard GUI) | https://nodejs.org/ |

> ⚠️ Docker Desktop richiede che **WSL 2** sia abilitato su Windows — Docker te lo chiede automaticamente al primo avvio

---

## STEP 1 — Clona il repo

Apri il **Terminale di Windows** (PowerShell o cmd) e digita:

```powershell
cd L:\PROGETTI
git clone https://github.com/CarlSamma/framework.git Framework160626
cd Framework160626\framework
```

> Se la cartella `framework` esiste già e hai già clonato, salta questo step.

---

## STEP 2 — Apri il progetto in VS Code

```powershell
code .
```

VS Code si apre sulla cartella del progetto. In basso a sinistra vedrai la branch corrente (probabilmente `main`).

---

## STEP 3 — Passa alla branch `hybrid`

### Metodo A — Da terminale (più sicuro):

Nel terminale integrato di VS Code (`Ctrl + backtick`):

```powershell
git fetch origin
git checkout hybrid
```

Risultato atteso:
```
Branch 'hybrid' set up to track 'origin/hybrid'.
Switched to a new branch 'hybrid'
```

### Metodo B — Da VS Code:

1. Clicca sul nome della branch in basso a sinistra (es. `main`)
2. Scegli `hybrid` dalla lista
3. La barra mostra ora `hybrid` ✅

---

## STEP 4 — Crea il Virtual Environment Python

Nel terminale integrato di VS Code:

```powershell
python -m venv .venv
```

Attiva il virtual environment:

```powershell
.venv\Scripts\Activate.ps1
```

> Se ricevi errore di policy PowerShell, esegui prima:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Poi riprova `.venv\Scripts\Activate.ps1`

Quando il venv è attivo vedrai `(.venv)` all'inizio del prompt:
```
(.venv) PS L:\PROGETTI\Framework160626\framework>
```

---

## STEP 5 — Installa le dipendenze Python

Installa in questo ordine esatto (prima le base, poi quelle hybrid):

```powershell
pip install -r requirements.txt
pip install -r requirements-hybrid.txt
```

> ⚠️ `requirements-hybrid.txt` installa anche `torch` (PyTorch) che è pesante (~500MB). Ci vuole qualche minuto. È normale.

Dipendenze principali installate:
- `fastapi`, `uvicorn` — server API
- `neo4j` — client grafo V-Genome (HYDRA)
- `temporalio` — orchestrazione workflow (CHRONOS)
- `kafka-python` — bus messaggi tra HYDRA e CHRONOS
- `asyncpg`, `alembic` — database PostgreSQL per CHRONOS
- `tweepy` — connessione Twitter/X API

---

## STEP 6 — Configura il file `.env`

Copia il file di esempio e aprilo:

```powershell
copy .env.example .env
code .env
```

Compila **obbligatoriamente** questi campi (senza di loro il sistema non parte):

```env
# --- Twitter/X API ---
# Ottieni le credenziali da https://developer.twitter.com/
TWITTER_BEARER_TOKEN=inserisci_qui
TWITTER_CONSUMER_KEY=inserisci_qui
TWITTER_CONSUMER_SECRET=inserisci_qui
TWITTER_ACCESS_TOKEN=inserisci_qui
TWITTER_ACCESS_TOKEN_SECRET=inserisci_qui

# --- LLM via OpenRouter ---
# Ottieni la chiave da https://openrouter.ai/
OPENROUTER_API_KEY=inserisci_qui

# Modelli già configurati (puoi lasciarli così):
OPENROUTER_MODEL_PRIMARY=anthropic/claude-sonnet-4
OPENROUTER_MODEL_HARD=x-ai/grok-4.3
OPENROUTER_MODEL_GROK=x-ai/grok-4

# --- Target ---
TARGET_HANDLE=HackingA0

# --- Lascia invariati (usano localhost Docker) ---
HYDRA_NEO4J_URI=bolt://localhost:7687
HYDRA_NEO4J_USER=neo4j
HYDRA_NEO4J_PASSWORD=tapv4hydra
HYDRA_KAFKA_BOOTSTRAP=localhost:9092
CHRONOS_DB_DSN=postgresql://tap:tap@localhost:5432/chronos
CHRONOS_TEMPORAL_HOST=localhost:7233
CHRONOS_KAFKA_BOOTSTRAP=localhost:9092
CHRONOS_REDIS_URL=redis://localhost:6379/0
CHRONOS_WORKER_IDENTITY=chronos-worker-01
```

> 🔒 **Non committare mai il file `.env` con le credenziali reali.**  
> Il `.gitignore` del repo lo esclude già automaticamente.

---

## STEP 7 — Avvia Docker Desktop

1. Apri **Docker Desktop** dalla barra di sistema o dal menu Start
2. Aspetta che l'icona nella taskbar diventi **verde** (Engine running)
3. Torna in VS Code

---

## STEP 8 — Avvia lo stack infrastrutturale

Questo comando avvia tutti i servizi necessari (Neo4j, Kafka, PostgreSQL, Redis, Temporal, ClickHouse, MinIO, Debezium):

```powershell
docker compose -f docker-compose.infra.yml up -d
```

> Il primo avvio scarica le immagini Docker (~2-3 GB). Ci vuole tempo. Normale.

Verifica che tutto sia in piedi:

```powershell
docker compose -f docker-compose.infra.yml ps
```

Tutti i servizi devono mostrare `running` o `healthy`. Porte esposte:

| Servizio | Porta | Cosa puoi vedere |
|---|---|---|
| PostgreSQL | 5432 | DB CHRONOS |
| Neo4j Browser | **http://localhost:7474** | Grafo V-Genome |
| Kafka | 9092 | Bus messaggi |
| Redis | 6379 | Cache |
| Temporal UI | **http://localhost:8233** | Monitor workflow |
| ClickHouse | 8123 | Analytics |
| MinIO | **http://localhost:9001** | Object storage |
| Debezium | 8083 | CDC Neo4j↔PostgreSQL |

---

## STEP 9 — Esegui migrazioni database e seed V-Genome

```powershell
# Imposta la variabile d'ambiente per il DB CHRONOS
$env:CHRONOS_DB_DSN = "postgresql://tap:tap@localhost:5432/chronos"

# Esegui le migrazioni Alembic
alembic upgrade head

# Popola il grafo V-Genome in Neo4j con le tecniche iniziali
python scripts/seed_vgenome.py

# Registra il connettore Debezium (CDC PostgreSQL → Neo4j)
powershell scripts/debezium.ps1
```

---

## STEP 10 — Avvia i componenti applicativi

Apri **3 terminali separati** in VS Code (`+` nel pannello terminale):

### Terminale 1 — HYDRA Scanner
```powershell
$env:PYTHONPATH = "src"
python -m hydra.scanner --target HackingA0 --platform twitter280
```

### Terminale 2 — CHRONOS Worker
```powershell
powershell scripts/chronos_worker.ps1
```

### Terminale 3 — Stack applicativo completo (alternativa)
```powershell
docker compose -f docker-compose.app.yml up -d
```

---

## STEP 11 — Verifica che funzioni

### Controlla i log HYDRA:
Nel Terminale 1 dovresti vedere messaggi tipo:
```
v_genome_connected uri=bolt://localhost:7687
v_genome_techniques_fetched target_model=hackinga0 count=N
```

### Controlla Temporal UI:
Apri http://localhost:8233 nel browser → dovresti vedere i workflow `ExtractionWorkflow` apparire quando HYDRA invia un probe.

### Controlla Neo4j:
Apri http://localhost:7474 → login con `neo4j` / `tapv4hydra` → esegui questa query per vedere le tecniche:
```cypher
MATCH (t:AttackTechnique) RETURN t LIMIT 25
```

---

## STEP 12 — Esegui i test

```powershell
$env:PYTHONPATH = "src"

# Test rapidi senza Docker
pytest tests/hydra tests/chronos tests/integration -q

# Test con coverage
pytest tests/hydra tests/chronos tests/integration `
  --cov=hydra --cov=chronos --cov=shared `
  --cov-report=term-missing -q

# Type checking
mypy --strict src/hydra src/chronos src/shared src/tap/config.py src/tap/models.py
```

> I test Docker-conditional vengono saltati automaticamente se Docker non è attivo. È comportamento previsto.

---

## ❌ PROBLEMI COMUNI E SOLUZIONI

### "`.venv\Scripts\Activate.ps1` non riconosciuto"
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### "docker compose: comando non trovato"
- Assicurati che Docker Desktop sia **avviato** e l'engine sia verde
- Riavvia VS Code dopo l'installazione di Docker

### "neo4j connection refused" o "kafka connection refused"
- I container sono ancora in avvio. Aspetta 30-60 secondi e riprova
- Controlla con: `docker compose -f docker-compose.infra.yml ps`

### "OPENROUTER_API_KEY not set"
- Hai dimenticato di compilare il `.env`. Torna allo Step 6.

### "ModuleNotFoundError: No module named 'hydra'"
- Il `PYTHONPATH` non è impostato. Aggiungi sempre:
  ```powershell
  $env:PYTHONPATH = "src"
  ```
  prima di ogni comando Python.

### "alembic: command not found"
- Il venv non è attivo. Esegui:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

---

## 📁 STRUTTURA DEL REPO (branch hybrid)

```
framework/
├── src/
│   ├── hydra/               ← HYDRA: Discovery Layer
│   │   ├── v_genome.py      ← client Neo4j grafo tecniche
│   │   ├── fusion_engine.py ← fusione tecniche + payload
│   │   ├── surrogate_model.py ← scoring ASR surrogate
│   │   ├── handoff.py       ← handoff a CHRONOS via Kafka
│   │   └── v_genome_schema.cypher ← schema grafo Neo4j
│   ├── chronos/             ← CHRONOS: Extraction Layer
│   │   ├── orchestrator.py  ← consumer Kafka + avvio workflow Temporal
│   │   ├── gamma_tracker.py ← scoring γ ∈ [0,10]
│   │   ├── beam_search.py   ← esplorazione multi-turno
│   │   ├── coat_engine.py   ← CoAT reasoning
│   │   ├── behavioral_profiler.py ← profilo OCEAN+
│   │   ├── persistence.py   ← scrittura PostgreSQL
│   │   ├── activities/      ← attività Temporal
│   │   └── workflows/       ← ExtractionWorkflow
│   ├── shared/              ← modelli Pydantic condivisi
│   ├── adapters/            ← adattatori piattaforme
│   └── tap/                 ← core legacy v2.2 + config + LLMClient
├── scripts/
│   ├── seed_vgenome.py      ← popola Neo4j
│   ├── chronos_worker.ps1   ← avvia worker CHRONOS
│   ├── debezium.ps1         ← registra connettore CDC
│   └── infra.ps1            ← setup automatizzato
├── tests/
│   ├── hydra/
│   ├── chronos/
│   └── integration/
├── docker-compose.infra.yml ← Neo4j, Kafka, PostgreSQL, Redis, Temporal...
├── docker-compose.app.yml   ← stack applicativo
├── requirements.txt         ← dipendenze base
├── requirements-hybrid.txt  ← dipendenze HYDRA + CHRONOS
└── .env.example             ← template variabili d'ambiente
```

---

## 🔄 FLUSSO DATI (come funziona il sistema)

```
HYDRA scanner
    │
    ├─ interroga V-Genome (Neo4j) → seleziona tecniche con ASR≥0.6, Stealth≥0.7
    ├─ genera payload → invia probe a @HackingA0 su Twitter/X
    │
    └─► Kafka topic: hydra.discovery.results
                          │
                    CHRONOS orchestrator (legge Kafka)
                          │
                          └─► avvia ExtractionWorkflow (Temporal)
                                    │
                                    ├─ Beam Search (esplora varianti)
                                    ├─ CoAT Reasoning (ragionamento)
                                    ├─ GammaTracker (score γ risposta)
                                    ├─ BehavioralProfiler (profilo OCEAN+)
                                    │
                                    └─► Kafka topic: chronos.extraction.complete
                                                    │
                                             HYDRA aggiorna
                                             V-Genome (Neo4j)
                                             via Debezium CDC
```

---

## 📞 SUPPORTO

- **Temporal UI** (monitor workflow): http://localhost:8233
- **Neo4j Browser** (grafo V-Genome): http://localhost:7474
- **MinIO Console** (storage): http://localhost:9001

---

*readme296.md — generato per branch `hybrid` | APPOpzioneIbrida v1.0.0*
