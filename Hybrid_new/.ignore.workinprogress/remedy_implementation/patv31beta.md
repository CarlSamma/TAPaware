<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# genera una descrizione tecnica dettagliata della struttura della branch patv3.1.beta. DESCRIZIONE ESTRAMENTE MOLTO APPROFONDITA E TECNICA PER PUBBLICO AUDIENCE DESTINATARI: senior engineer programmer developer

Con il codice sorgente completo analizzato, posso ora produrre la descrizione tecnica approfondita richiesta.

***

# TAP Framework — `patv3.1.beta`: Technical Deep-Dive

## Overview \& Identity

La branch `patv3.1.beta` (HEAD: `307b85a`, SHA completo: `307b85a7394770813ade6ba748fa0c8800ec501d`) ospita la versione **3.1 beta** di **TAP — Tree of Attacks with Pruning**, un framework Python di ricerca sulla sicurezza degli LLM (classificato `Development Status :: 3 - Alpha` in PyPI) . Il package è distribuito sotto licenza **Apache-2.0**, richiede **Python ≥ 3.11**, e il build system è basato su `setuptools>=68.0` con wheel . Il package entry-point principale è `tap-server → tap.api:main`, ovvero un server FastAPI avviato direttamente da CLI .

***

## Repository Structure

La root della branch espone la seguente struttura flat/arborescente :

```
/
├── .gitignore
├── .ignore.workinprogress/         ← WIP staging area (esclusa dal tree)
├── .python-version                 ← Pin versione Python (runtime lock)
├── Copia.env.txt                   ← Template env vars (non .env effettivo)
├── LICENSE                         ← Apache-2.0
├── README.md                       ← 9.7 KB
├── Sources/                        ← Artefatti di ricerca/riferimento
├── data/                           ← Dataset runtime / SQLite persistence
├── framework_specs.md              ← 47.3 KB — specifica architettonica completa
├── inspect_data.py                 ← Utility diagnostica sul DB
├── pyproject.toml                  ← Build metadata (PEP 517/518)
├── remedy_implementation/          ← Documenti operativi & log v3.1
├── requirements.txt                ← Dependency manifest flat
├── scripts/                        ← Automation / runner scripts
├── src/tap/                        ← Package principale (src-layout)
├── tests/                          ← Test suite (pytest-asyncio)
└── xSUBSCRIPTION.txt               ← 21.2 KB — subscription/quota management
```

La scelta del **src-layout** (`src/tap/`) è una best practice moderna per evitare import accidentali del package non-installato durante i test .

***

## Dependency Stack

Le dipendenze di produzione definite in `pyproject.toml` e `requirements.txt` sono :


| Package | Version | Ruolo |
| :-- | :-- | :-- |
| `fastapi` | ≥ 0.115.0 | REST API layer / WebSocket hub |
| `uvicorn[standard]` | ≥ 0.30.0 | ASGI server (con `httptools`, `uvloop`) |
| `pydantic` | ≥ 2.9.0 | Data modeling / validation (V2 API) |
| `pydantic-settings` | ≥ 2.5.0 | Env-based config injection |
| `tweepy` | ≥ 4.14.0 | Twitter API v2 client (OAuth 1.0a/2.0) |
| `httpx` | ≥ 0.27.0 | Async HTTP client (probe delivery) |
| `aiosqlite` | ≥ 0.20.0 | Async SQLite persistence layer |
| `openai` | ≥ 1.50.0 | Unified LLM gateway (OpenRouter compat.) |
| `asyncio-throttle` | ≥ 1.0.2 | Rate-limiting asincrono su task |
| `jinja2` | ≥ 3.1.4 | Template rendering per probe/markdown |
| `python-dotenv` | ≥ 1.0.1 | .env loading a runtime |
| `structlog` | ≥ 24.4.0 | Structured logging (JSON events) |

Dev dependencies aggiungono: `pytest`, `pytest-asyncio`, `pytest-cov`, `ruff` (linter/formatter), `mypy` (type checking) .

***

## Core Package — `src/tap/`

Il package principale contiene **24 moduli Python** più subdirectory `strategies/`, `static/`, `templates/` . Segue la mappa funzionale completa:

### Orchestration Layer

**`engine.py`** (42.8 KB) è il cuore del sistema — la classe `TAPEngine` implementa l'intero ciclo TAP attraverso il metodo `run_cycle()` . Il ciclo esegue 9 step sequenziali con dependency injection completa nel costruttore:

```
SELECT → BRANCH → PRUNE → POST → COLLECT → CLASSIFY → SCORE → EXTRACT → FOLLOW-UP
```

Il costruttore riceve per DI: `Database`, `TwitterClient`, `SSOTEngine`, `DPAFrameManager`, `ResponseClassifier`, `Judge`, `GrokMonitor`, `Settings`, `FollowUpGenerator`, più due agenti opzionali `stir_evaluator` e `intel_extractor` introdotti nella v3.1 . Il fallback LLM client è un `AsyncOpenAI` puntato su **OpenRouter** (`https://openrouter.ai/api/v1`) con `response_format={"type": "json_object"}` .

**`api.py`** (26.3 KB) espone la REST API FastAPI e il WebSocket broadcast layer — è il punto di ingresso `tap-server` da CLI .

**`ssot.py`** (SSOT Engine, 12.8 KB) è il **Single Source of Truth** — mantiene lo stato canonico delle proprietà confermate e calcola l'**entropia di Shannon** del candidato passphrase .

***

### Phase Architecture

Il framework implementa una macchina a stati multi-fase esplicita :

**Phase 0 Gate** — blocca il loop principale finché tre *foundational properties* (`word_count`, `total_length`, `language`) non sono confermate. Se il gate fallisce, `AgentIntelExtractor.analyze_and_unlock()` tenta un unlock automatico; se anche questo fallisce, forza la selezione della prima proprietà mancante .

**Phase 5 Autoregressive Extraction** — si attiva quando l'entropia scende sotto la soglia `_PHASE5_THRESHOLD = 3.3 bits` (corrispondente a < 10 candidati residui). Usa **Primacy Weighting**: frammenti parziali del passphrase che forzano la completamento autoregressivo del target bot .

**Property Selection** — algoritmo information-theoretic basato su Shannon entropy con priorità ordinata su 10 property keys (`word_count`, `total_length`, `first_letter`, `language`, `word1_length`, ecc.), selezionando sempre la prima proprietà non ancora confermata .

***

### Agents \& Intelligence Modules

**`agents.py`** (5.9 KB) — definisce gli agenti v3.1: `AgentDPAFManager`, `AgentSTIREvaluator`, `AgentIntelExtractor` .

**`dpa.py`** (14.3 KB) — `DPAFrameManager`: gestione dei **DPA frames** (Discreet Persona Architecture), alias burning, metaphor shift detection, e frame rotation. Il metodo `record_score()` alimenta il tracking dell'efficacia del frame corrente; se lo STIR score scende sotto il 20%, il sistema forza la rotazione automatica del frame .

**`llm_client.py`** (22.3 KB) — gateway LLM unificato con `ModelTier` enum per routing multi-modello (primary/hard tier via OpenRouter, compatibile con tutti i provider: Grok, Claude, GPT, ecc.) .

**`grok_monitor.py`** (12.3 KB) — `GrokMonitor`: polling asincrono dei reply del target bot su X/Twitter con timeout configurabile (`reply_timeout_seconds`) .

**`judge.py`** (12.2 KB) — off-topic filter + scoring con scala da 1 a 10, deduplicazione semantica via Jaccard similarity (`_SIMILARITY_THRESHOLD = 0.80`) .

**`classifier.py`** (10.4 KB) — `ResponseClassifier`: pattern classification delle risposte in `PatternClass` enum (es. `VERIFY_HIT`, `NO_RESPONSE`, ecc.) .

**`followup.py`** (32.7 KB) — `FollowUpGenerator`: genera sempre due opzioni A/B (HITL — Human-In-The-Loop) per permettere all'operatore di selezionare il probe successivo .

***

### Data \& Communication Layer

**`db.py`** (30.4 KB) — layer di persistenza asincrono su **aiosqlite**, con metodi `upsert_tweet()`, `insert_node()`, `get_active_nodes()`, `get_latest_our_bot_tweet()`, `insert_metaphor_layer()` .

**`x_client.py`** (32.8 KB) — `TwitterClient`: wrapper Tweepy v2 con `post_probe()`, `sync_compliance()`, `get_quota_status()`. Implementa **Oracle Protocol Step 8**: latency enforcement di 1800s (30 minuti) tra probes consecutivi per eludere rate-limiting comportamentale .

**`stream_listener.py`** (29.5 KB) — listener asincrono del Twitter streaming endpoint per ingestione real-time dei reply .

**`oauth.py`** (5.4 KB) — gestione OAuth 1.0a / OAuth 2.0 per X API .

***

### Configuration \& Utilities

**`config.py`** (8.1 KB) — `Settings` via `pydantic-settings`: binding completo da env vars per `openrouter_api_key`, `openrouter_model_primary`, `openrouter_model_hard`, `reply_timeout_seconds`, `tap_branching`, `our_bot_handle`, e parametri X/Twitter .

**`models.py`** (12.2 KB) — Pydantic V2 data models: `TAPNode`, `Property`, `DualFollowUp`, `JudgeScore`, `ResponseClassification`, `PatternClass`, `BranchStrategy`, `PropertyStatus`, `Tweet`, `TweetSource` .

**`prompts.py`** (12.4 KB) — template prompt `ATTACKER_SYSTEM` e `ATTACKER_USER` per la generazione dei probes tramite Attacker LLM .

**`prompt_sanitiser.py`** (13.2 KB) — sanitizzazione e validazione dei prompt prima dell'invio .

**`personas.py`** (3.2 KB) — definizione delle personas utilizzabili come DPA aliases .

**`logger.py`** (4.9 KB) — configurazione `structlog` con output JSON strutturato .

**`exceptions.py`** (2.1 KB) — gerarchia di eccezioni custom (`EngineError`) .

**`phase0.py`** (12.6 KB) — logica dedicata al Phase 0 gate .

***

### Strategy Subpackage — `src/tap/strategies/`

Sei moduli implementano le strategie di branching :

- **`base.py`** — abstract base class `BaseStrategy` con interfaccia comune
- **`binary_search.py`** — strategia principale: binary search sul property space
- **`aesthetic.py`** — framing estetico/narrativo dei probe
- **`metaphor_shift.py`** — rotazione del layer metaforico del DPA frame
- **`phase5.py`** — strategia specifica Phase 5 per autoregressive extraction
- **`selector.py`** — routing dinamico della strategia in base allo stato corrente

***

## Operational Documentation — `remedy_implementation/`

La directory ospita la documentazione operativa v3.1 :

- **`instructions.v.3.1.md`** (7.7 KB) — istruzioni operative versione corrente
- **`readme.v3.1.md`** (9.9 KB) — README specifico v3.1
- **`implementation plan _ latest/`** e **`implementation plan/`** — planning evolutivo
- **`#KNOWLEDGES/`** — knowledge base di riferimento
- **`old version 2.2/`** — archivio versione precedente (confronto storico)
- **`logs/`** — execution logs
- **`perplexity_deepdive_patv3.1.beta.md`** (22.7 KB) e **`perplexity_esaminabranch_patv3.1.beta.md`** (2.8 KB) — analisi precedenti generate con questo stesso tool

***

## WebSocket \& Real-Time Event Bus

Il `TAPEngine` implementa un event bus interno tramite `_emit_event(event_type, data)` che invoca `event_callback` iniettato a costruzione . Gli eventi emessi includono: `property_confirmed`, `new_tweet`, `probe_posted`, `probe_result`, `followup_generated`, `stir_evaluated`, `phase5_extraction`, `rotation_suggested` — tutti serializzati con `model.model_dump(mode="json")` (Pydantic V2 pattern) . Il pattern è compatibile con WebSocket broadcasting via FastAPI `api.py`.

***

## Compliance \& Quota Management

Il ciclo finale di ogni `run_cycle()` esegue `_run_compliance_sync()`: verifica sincrona dell'esistenza di tutti i tweet attivi nelle ultime 24h rispetto all'API X (Oracle Hunter Protocol 2026), seguita da `twitter.get_quota_status()` per il tracking delle API quota . Il file `xSUBSCRIPTION.txt` (21.2 KB) gestisce lo strato di subscription e rate management .

