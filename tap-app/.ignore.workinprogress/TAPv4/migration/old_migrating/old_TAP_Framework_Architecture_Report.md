# TAP Framework v4-hexagonal — Architettura e Funzionamento del Progetto
### Branch: `tap-v4-hexagonal` | Repo: `CarlSamma/framework`
> **Destinatari:** Sviluppatori e Programmatori Senior  
> **Scopo:** Analisi tecnica approfondita dell'architettura, dei pattern di design, del flusso esecutivo e delle integrazioni del sistema TAP Framework.

---

## 1. Executive Overview

TAP Framework (v2.2, branch `tap-v4-hexagonal`) è un'applicazione Python **asincrona**, progettata per eseguire cicli di **adversarial probing** (TAP — Twitter Adversarial Probing) contro un bot target su Twitter/X. Il sistema implementa una pipeline ibrida che combina:

- **LLM multi-provider** (via OpenRouter) per la generazione intelligente di probe
- **Integrazione real-time con X/Twitter** tramite Activity API e stream
- **HITL (Human-In-The-Loop)** per la selezione delle opzioni di probe
- **Architettura esagonale** (come indicato dal nome del branch `tap-v4-hexagonal`), separando il dominio applicativo dall'infrastruttura

L'obiettivo operativo del sistema è estrarre **proprietà comportamentali** di un bot Twitter attraverso sonde conversazionali calibrate da LLM, classificare le risposte e costruire una mappa (TAP Tree) del comportamento del target. Il tutto in un loop osservabile, resiliente e interattivo.

---

## 2. Stack Tecnologico

| Layer | Tecnologia | Versione/Note |
|---|---|---|
| Runtime linguaggio | Python | 3.11+ |
| Web server | FastAPI + uvicorn | ASGI asincrono |
| HTTP client | httpx | async, usato per Activity API stream |
| Twitter client | tweepy | OAuth1/2 multi-context |
| Configurazione | pydantic-settings | Da file `.env` |
| Database | SQLite (aiosqlite) | Accesso asincrono, file locale `tap.db` |
| Frontend | HTML + CSS + Alpine.js | SPA statica, no framework pesante |
| Testing | pytest | Mock su dipendenze esterne |
| LLM Gateway | OpenRouter | Modelli primario / hard / grok |

---

## 3. Struttura del Repository

```
CarlSamma/framework (branch: tap-v4-hexagonal)
├── src/                        # Core applicativo (package Python principale)
├── Sources/                    # Moduli aggiuntivi / utilities
├── remedy_implementation/      # Implementazioni correttive / workaround
├── scripts/                    # Script operativi e di setup
├── tests/                      # Suite pytest
├── data/                       # Dati persistenti / dataset
├── .ignore.workinprogress/     # Cartella WIP (esclusa da tracking)
├── api.py                      # Entry point FastAPI
├── config.py                   # Settings pydantic
├── logger.py                   # Logger strutturato
├── x_client.py                 # Client X/Twitter
├── stream_listener.py          # Activity API stream
├── engine.py                   # TAP Engine orchestrator
├── llm_client.py               # LLM gateway unificato
├── prompt_sanitiser.py         # Validazione e sanificazione probe
├── grok_monitor.py             # Monitor e classificazione risposte
├── followup.py                 # Generatore followup A/B HITL
├── setup_db.py                 # Schema e inizializzazione database
├── inspect_data.py             # Utility di ispezione dati
├── pyproject.toml              # Configurazione build/dipendenze
├── requirements.txt            # Dipendenze pip
├── framework_specs.md          # Specifiche tecniche dettagliate (48KB)
├── Copia.env.txt               # Template variabili d'ambiente
└── xSUBSCRIPTION.txt           # Note subscription X Activity API
```

---

## 4. Architettura a Livelli (Layered / Hexagonal)

Il nome del branch `tap-v4-hexagonal` è indicativo della scelta architetturale: il progetto implementa un'**architettura esagonale** (o "Ports and Adapters"), in cui il dominio applicativo rimane disaccoppiato dai dettagli di infrastruttura. Questo si traduce in 5 layer distinti:

### Layer 1 — Configurazione
Gestito interamente da `config.py` tramite `pydantic-settings`. Tutte le variabili d'ambiente vengono caricate da file `.env` al bootstrap. La funzione `save_env_vars()` permette di **persistere dinamicamente** valori nel file `.env` durante il runtime (es: refresh token OAuth) senza lanciare eccezioni. Il layer gestisce credenziali OAuth1/2, endpoint OpenRouter, percorsi su filesystem e parametri operativi come `poll_interval`, `post_cooldown`, `tap_width`, `tap_depth`.

### Layer 2 — Infrastruttura
Comprende il server `FastAPI` con `uvicorn`, il database `SQLite` con accesso asincrono via `aiosqlite`, il logging strutturato (`logger.py`), il client Twitter (`x_client.py`) e il listener dello stream (`stream_listener.py`). Questi componenti sono tutti **sostituibili**: l'architettura esagonale garantisce che il dominio non dipenda direttamente dall'implementazione concreta.

### Layer 3 — Gateway LLM
`llm_client.py` espone un'interfaccia uniforme per le chiamate LLM, nascondendo la complessità di retry, fallback e circuit breaking. Tre modelli sono gestiti: **primario**, **hard** (per task complessi) e **grok** (per classificazione risposte). Il gateway normalizza errori e risposte prima di presentarle al layer applicativo.

### Layer 4 — Applicazione (Domain Core)
È il cuore del sistema. `engine.py` implementa il ciclo TAP orchestrando `TAPNode`, `ResponseClassifier`, `Judge`, `GrokMonitor`, `FollowUpGenerator`, `AgentDPAFManager` e `AgentSTIREvaluator`. Questo layer contiene la **logica di business** ed è quello che l'architettura esagonale protegge maggiormente dalle dipendenze esterne.

### Layer 5 — Presentazione
Dashboard HTML statica con Alpine.js. Il frontend è intenzionalmente **stateless sul client**: tutto lo stato risiede nel backend e viene propagato tramite WebSocket (`/ws/live`). Il live feed, il pannello di selezione A/B e il health panel sono tutti alimentati da eventi push.

---

## 5. Analisi Moduli Principali

### 5.1 `api.py` — Entry Point e Wiring delle Dipendenze

`api.py` è il punto di ingresso dell'applicazione. Gestisce il **lifecycle FastAPI** (`lifespan` context manager) e si occupa del wiring di tutte le dipendenze:

**Startup sequence:**
1. `get_settings()` — carica la configurazione da `.env`
2. `setup_logging()` — inizializza il logger strutturato
3. `Database.initialize()` — crea schema SQLite se non esiste
4. Istanzia `TwitterClient` e `StreamListener`
5. Avvia risoluzione `target_user_id` e connessione stream X
6. Istanzia `TAPEngine` con callback per emissione eventi WebSocket
7. Lancia seed tweet iniziale da target + monitor periodico

**Teardown:**
- Stop `StreamListener`
- Chiusura connessione DB

Registra le route REST e il WebSocket endpoint, esponendo l'intera API del sistema.

---

### 5.2 `config.py` — Gestione Configurazione Runtime

Estende `pydantic-settings.BaseSettings` per validare e caricare la configurazione. Parametri chiave gestiti:

- **Auth Twitter:** `api_key`, `api_secret`, `access_token`, `access_token_secret`, `bearer_token`, `oauth2_client_id`, `oauth2_client_secret`
- **OpenRouter:** `openrouter_api_key`, `primary_model`, `hard_model`, `grok_model`
- **Operativi:** `poll_interval` (secondi tra poll), `post_cooldown` (anti-spam), `tap_width` (ampiezza albero probe), `tap_depth` (profondità massima)
- **Percorsi:** `db_path`, `ssot_path`, `log_file_path`

`save_env_vars()` è un pattern critico: permette di aggiornare i refresh token OAuth2 in `.env` senza riavvio. Questo è essenziale per sessioni di probing prolungate dove i token scadono.

---

### 5.3 `logger.py` — Logging Strutturato con Context Propagation

Il logger personalizzato supporta multi-target output (stdout + file rotante) e, soprattutto, implementa **context propagation** tramite correlation ID, `cycle_id` e `probe_id`. Questo significa che ogni entry di log è tagged con l'identificatore del ciclo TAP e della singola probe che l'ha generata: fondamentale per il debugging in ambienti dove più probe vengono gestite in concorrenza asincrona.

```python
# Pattern tipico di correlazione log
logger.info("probe_posted", extra={"cycle_id": cycle_id, "probe_id": probe_id, "tweet_id": tweet_id})
```

---

### 5.4 `x_client.py` — Client Twitter Multi-OAuth

Il client gestisce **tre flussi OAuth distinti** su un singolo oggetto, una complessità necessaria data l'eterogeneità degli endpoint X:

| Metodo Auth | Scopo | API Target |
|---|---|---|
| OAuth2 Bearer Token | Read-only / search | Endpoint pubblici v2 |
| OAuth1.0a User Context | Write (tweet, reply, media) | Posting / upload |
| OAuth2 User Context | Activity API subscription | Stream management |

Funzioni chiave:
- `initialize_seed()` — recupera i tweet più recenti del target per inizializzare il contesto
- `poll_new_tweets()` — polling periodico come fallback al real-time stream
- `post_probe()` — pubblica il probe come **nuovo tweet** (non come reply), obbligatoriamente con mention `@HackingA0`
- `upload_media_chunked()` — upload media in chunk per probe con allegati
- `verify_crc()` — gestisce il CRC challenge del webhook X

**Politica di retry:**
Il metodo `_retry()` implementa backoff esponenziale con cap a **300 secondi**. I `tweepy.TooManyRequests` (HTTP 429) vengono gestiti con attesa esplicita. Gli errori `Forbidden` relativi alle reply restrictions sono considerati **fatali** e non triggherano retry (per evitare spreco di quota e loop inutili).

**Nota architetturale su `post_probe()`:** la decisione di postare le probe come nuovi tweet anziché come reply dirette al target è un workaround alle politiche di Twitter che limitano le reply da account con restrizioni. Il `reply_to_id` viene esplicitamente ignorato anche se fornito dall'engine.

---

### 5.5 `stream_listener.py` — Real-Time Activity API

Implementa l'ascolto in tempo reale delle reply del bot target tramite X Activity API v2. Il flow di subscription richiede due step separati:

1. `POST /2/activity/subscriptions` — crea la subscription (OAuth2 User Context)
2. `GET /2/activity/stream` — apre lo stream SSE (Bearer token app-only)

Questa asimmetria di autenticazione tra subscription e stream è una caratteristica dell'API X che il listener gestisce esplicitamente.

**Meccanismi di stato e resilienza:**
- `last_subscription_auth_failure`, `last_subscription_errors`, `last_stream_auth_error` — variabili di stato per diagnostica
- Queue asincrona per tweet_id: ogni probe pubblicata registra il proprio `tweet_id` nella queue in attesa della reply corrispondente
- Backoff riconnessione automatica con log strutturato
- Le duplicate subscription vengono trattate come **successo soft** (idempotenza)

---

### 5.6 `engine.py` — TAP Engine (Orchestrazione del Ciclo Principale)

`engine.py` è il componente più critico del sistema. Implementa il ciclo completo di un'iterazione TAP:

```
[Selezione proprietà target]
         ↓
[Generazione probe via LLM]
         ↓
[Sanificazione probe (prompt_sanitiser)]
         ↓
[Posting probe (x_client.post_probe)]
         ↓
[Salvataggio TAPNode in DB]
         ↓
[Attesa reply (GrokMonitor / StreamListener)]
         ↓
[Classificazione risposta (ResponseClassifier + Judge)]
         ↓
[Aggiornamento TAP Tree + SSOT]
         ↓
[Emissione eventi WebSocket → Frontend]
```

Le integrazioni dell'engine con agenti specializzati:
- **`TAPNode`** — rappresenta un nodo dell'albero probe/risposta
- **`ResponseClassifier`** — classifica il tipo di risposta (hit, refusal, no_response)
- **`Judge`** — valuta la qualità della risposta rispetto alla proprietà sondata
- **`AgentDPAFManager`** — gestisce il DPA (Data Properties Acquisition) Frame
- **`AgentSTIREvaluator`** — valuta metriche STIR (Sensitivity, Targetedness, Informativeness, Reliability)
- **`FollowUpGenerator`** — genera le opzioni di followup A/B

Le eccezioni in ogni fase vengono catturate e convertite in classificazioni di failure per mantenere la continuità del ciclo.

---

### 5.7 `llm_client.py` — Gateway LLM Unificato

Il gateway è il **punto di contatto unico** con i provider LLM. L'architettura del client implementa pattern di resilienza enterprise-grade:

**Circuit Breaker:** se un modello accumula un numero di errori consecutivi oltre soglia, viene automaticamente disabilitato temporaneamente per evitare cascading failures.

**Fallback ordinato:** in caso di errore sul modello primario, il sistema scala su `hard_model`, poi su `grok_model`, seguendo un ordine esplicito di fallback. Questo garantisce continuità operativa anche in caso di rate-limiting di un singolo provider.

**Retry esponenziale:** ogni chiamata fallita su errori transitori viene ritentata con backoff crescente.

**Parsing robusto:** il client gestisce risposte LLM malformate, JSON parziali e variazioni di formato, normalizzando l'output prima di restituirlo all'engine. Questo è critico perché i modelli LLM non garantiscono sempre output strutturati consistenti.

---

### 5.8 `prompt_sanitiser.py` — Guardrail Pre-Post

Il sanitiser è un componente di sicurezza che intercetta ogni probe **prima** che venga pubblicata su Twitter. Blocca:

- **Prompt injection patterns:** pattern tipo `ignore previous instructions`, `ACT AS`, etc.
- **Termini letterali pericolosi:** lista di keyword esplicite
- **Domande multi-proprietà:** probe che tentano di estrarre più informazioni contemporaneamente (riduce il signal-to-noise del ciclo TAP)
- **Probe malformate:** lunghezza eccessiva, ripetizioni anomale

Il sanitiser restituisce un motivo di rifiuto dettagliato che viene loggato e inviato al frontend via WebSocket. Questo componente è fondamentale sia per la correttezza metodologica del probing (una probe = una proprietà) che per la compliance con le policy di Twitter.

---

### 5.9 `grok_monitor.py` — Classificazione Risposte Real-Time

Il monitor integra `StreamListener` e `LLMClient` per analizzare le reply ricevute:

- Attende sulla queue per `tweet_id` la reply corrispondente
- Invia la risposta ricevuta al modello Grok/LLM per classificazione
- Restituisce una delle classificazioni: `verify_hit` (proprietà confermata), `refusal` (il bot ha rifiutato), `no_response` (nessuna risposta entro timeout)
- Estrae proprietà rilevate dalla risposta per alimentare il TAP Tree

---

### 5.10 `followup.py` — HITL Dual-Option Generator

`followup.py` implementa il pattern **Human-In-The-Loop** del sistema. A ogni iterazione genera due varianti di probe (opzione A e opzione B) con approcci diversi (es: diretta vs. indiretta, formale vs. informale). L'utente seleziona tramite dashboard quale opzione eseguire prima di triggerare il `POST /api/post`. La scelta viene registrata per analisi retrospettiva dell'efficacia delle strategie di probe.

---

## 6. API REST — Design e Contratti

### Endpoint principali

| Metodo | Path | Funzione |
|---|---|---|
| `GET` | `/` | Serve dashboard HTML |
| `GET` | `/api/feed` | Feed dei tweet recenti (probe + risposte) |
| `GET` | `/api/tree` | Stato corrente del TAP Tree (JSON) |
| `GET` | `/api/properties` | Proprietà estratte dal target |
| `GET` | `/api/dpa` | Stato del DPA Frame corrente |
| `POST` | `/api/select?choice=A\|B` | Selezione opzione HITL |
| `POST` | `/api/post` | Esegue un ciclo probe completo |
| `GET` | `/api/ssot` | Single Source of Truth JSON |
| `GET` | `/api/stats` | Statistiche di sessione |
| `GET` | `/api/entropy` | Valore di entropia informazionale corrente |
| `WebSocket` | `/ws/live` | Stream eventi in tempo reale |

### Health & Diagnostics

`GET /health` espone lo stato aggregato di tutti i sottosistemi:

```json
{
  "db": "ok",
  "stream": "connected",
  "llm": "ok",
  "sanitiser": "ok",
  "quota": { "remaining": 42, "reset_at": "2026-06-27T11:00:00Z" }
}
```

Questo endpoint è pensato per essere consumato da sistemi di monitoraggio esterni (Prometheus, Grafana, uptime checker).

---

## 7. Persistenza e Data Model

Il database SQLite `tap.db` persiste l'intero stato del sistema tra sessioni. Le entità principali:

| Tabella | Contenuto |
|---|---|
| `tweets` | Tutti i tweet pubblicati e ricevuti |
| `tap_nodes` | Nodi dell'albero probe/risposta con parent_id |
| `properties` | Proprietà estratte dal target con score |
| `event_log` | Log degli eventi di sistema (tipo, timestamp, payload) |
| `aliases` / `frames` | Alias e frame DPA del target |

Il **SSOT (Single Source of Truth)** è un file Markdown aggiornato dopo ogni ciclo TAP che funge da snapshot leggibile dello stato corrente del sistema. Questo file è accessibile sia tramite `GET /api/ssot` che come file su filesystem, consentendo integrazione con tool esterni di analisi.

---

## 8. Flusso Esecutivo Completo

Di seguito il flusso end-to-end di un ciclo TAP dalla prospettiva del sistema:

```
1.  uvicorn tap.api:app --reload
2.  FastAPI lifespan: bootstrap sequenziale
3.  DB init → Twitter auth → Stream connect → Seed fetch
4.  Frontend dashboard carica su http://localhost:8000
5.  TAPEngine genera opzioni A/B via llm_client
6.  followup.py presenta A/B all'utente in dashboard
7.  Utente seleziona POST /api/select?choice=A
8.  Utente conferma POST /api/post
9.  engine.execute_probe():
      a. Recupera proprietà target selezionata
      b. Genera probe via llm_client (modello primario)
      c. prompt_sanitiser.check(probe) → pass/reject
      d. x_client.post_probe() → tweet pubblicato, tweet_id registrato
      e. TAPNode creato e salvato in DB
10. stream_listener riceve reply del bot target
11. grok_monitor classifica risposta → {verify_hit | refusal | no_response}
12. engine aggiorna TAPNode con classificazione + score
13. AgentDPAFManager aggiorna DPA Frame
14. AgentSTIREvaluator calcola metriche STIR
15. SSOT markdown aggiornato
16. Evento WebSocket emesso → frontend aggiorna live feed + tree
```

---

## 9. Pattern di Resilienza e Fault Tolerance

Il sistema implementa una strategia multi-layer per gestire i failure nei sistemi distribuiti coinvolti (X API, LLM provider, DB):

### Retry Strategy

```
Errore transitorio → retry con backoff esponenziale (max 300s)
Errore fatale (Forbidden) → stop immediato, log, classificazione failure
Rate Limit (429) → attesa esplicita con log + backoff
```

### Circuit Breaker (LLM)

Il circuit breaker del `llm_client` mantiene un contatore di errori consecutivi per modello. Superata la soglia, il modello viene bypassato e il traffico re-routato al successivo nella catena di fallback. Il circuit si "chiude" (ripristina il modello) dopo un timeout di recovery.

### Stream Reconnection

Il `stream_listener` implementa un loop di riconnessione con backoff automatico. Gli errori `401/403` vengono trattati separatamente dagli errori di rete: gli auth error usano un backoff ad hoc più lungo, poiché indicano un problema di configurazione token, non di connettività.

---

## 10. Testing e Qualità del Codice

La suite pytest nella directory `tests/` mocka le dipendenze esterne (X API, OpenRouter, SQLite) permettendo il testing dell'engine e dei componenti di business logic in isolamento. Il comando di esecuzione è:

```bash
python -m pytest tests -q
```

I test coprono presumibilmente:
- Logica di sanificazione probe (`prompt_sanitiser`)
- Classificazione risposte (`ResponseClassifier`, `Judge`)
- Comportamento del circuit breaker LLM
- Ciclo di retry del client X

---

## 11. Deployment e Operational Considerations

### Setup rapido

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# oppure .venv\Scripts\activate  # Windows
pip install -r requirements.txt
cp Copia.env.txt .env  # popolare con credenziali reali
uvicorn tap.api:app --reload --port 8000
```

### Gestione credenziali

Il sistema usa `.gitignore` per escludere `.env`. I refresh token OAuth2 vengono aggiornati dinamicamente tramite `save_env_vars()`. **Non committare mai credenziali** — usare secret management (vault, env injection CI/CD) in ambienti di produzione.

### Containerizzazione

Il README nota esplicitamente che l'architettura è portabile in Docker. Un `Dockerfile` non è presente nel branch, ma la struttura del progetto è compatibile con una containerizzazione standard Python:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "tap.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 12. Considerazioni Architetturali Senior

### Punti di forza

- **Separation of Concerns netta:** ogni modulo ha una singola responsabilità ben definita; l'engine non conosce i dettagli OAuth, il client X non conosce la logica LLM.
- **Disaccoppiamento tramite callback:** l'engine emette eventi via callback WebSocket senza dipendenza diretta dal layer di presentazione, rispettando il principio di inversione delle dipendenze.
- **Resilienza by design:** circuit breaker, retry, fallback ordinato e backoff esponenziale sono integrati a livello architetturale, non come patch successive.
- **Osservabilità:** log strutturati con correlation ID, endpoint `/health`, event log persistente e SSOT rendono il sistema introspettabile end-to-end.

### Aree di miglioramento potenziale

- **Mancanza di container ufficiale:** la portabilità Docker è dichiarata ma non implementata nel repo. Un `docker-compose.yml` con il servizio uvicorn migliorerebbe onboarding e riproducibilità.
- **SQLite in produzione:** adeguato per uso single-user/single-instance. Per deployment multi-utente o alta concorrenza, la migrazione a PostgreSQL (con async driver `asyncpg`) sarebbe raccomandata senza stravolgere l'architettura (il DB layer è già astratto).
- **Nessun schema migration formale:** il setup del DB in `setup_db.py` presuppone uno schema statico. In una roadmap evolutiva, l'adozione di `alembic` per le migration sarebbe il passo naturale.
- **Frontend Alpine.js senza bundler:** adeguato per dashboard interna/operativa. Per una UI più complessa, la migrazione a Vite + Vue/React manterrebbe la leggerezza aggiungendo componentizzazione strutturata.
- **`.ignore.workinprogress/`:** la presenza di questa directory indica feature in sviluppo non ancora integrate. In un workflow production-ready, il pattern preferibile sarebbe l'uso di feature flags o branch dedicati per isolare WIP.

---

## 13. Glossario Tecnico

| Termine | Definizione nel contesto TAP |
|---|---|
| **TAP** | Twitter Adversarial Probing — metodologia di estrazione proprietà via probe sistematiche |
| **Probe** | Singolo tweet pubblicato per estrarre una proprietà comportamentale dal target |
| **TAP Tree** | Struttura ad albero delle probe/risposte che mappa il comportamento del target |
| **SSOT** | Single Source of Truth — snapshot Markdown dello stato corrente del sistema |
| **HITL** | Human-In-The-Loop — coinvolgimento umano nella selezione delle probe |
| **DPA Frame** | Data Properties Acquisition Frame — struttura dati che aggrega le proprietà estratte |
| **STIR** | Sensitivity, Targetedness, Informativeness, Reliability — metriche di valutazione |
| **Circuit Breaker** | Pattern di resilienza che disabilita temporaneamente un servizio in errore |
| **Probe sanitisation** | Validazione pre-post per garantire correttezza e sicurezza della probe |

---

*Report generato il 27 giugno 2026. Fonte: analisi diretta del branch `tap-v4-hexagonal` del repository `CarlSamma/framework` su GitHub.*
