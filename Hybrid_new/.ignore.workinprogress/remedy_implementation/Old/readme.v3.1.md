## README tecnico per sviluppatori

# TAP Framework v2.2 — Architettura tecnica

TAP Framework è un’applicazione Python asincrona progettata per eseguire un ciclo di attacco avversariale contro un bot Twitter/X, con una pipeline di probing basata su LLM e una UI HITL. Il sistema è costruito per essere estendibile, osservabile e resiliente ai limiti di X e dei provider LLM.

---

## Panoramica di alto livello

- Frontend: dashboard web statica + Alpine.js + WebSocket.
- Backend: `FastAPI` + `uvicorn`.
- Persistenza: `SQLite` locale con accesso asincrono.
- API X/Twitter: `tweepy` per posting e `httpx` per stream Activity API.
- LLM: gateway centralizzato per OpenRouter con gestione di fallback, circuit breaker e parsing robusto.
- Configurazione: `pydantic-settings` da .env.
- Monitoraggio: endpoint `/health`, log strutturati e event log persistente.

---

## Stack tecnologia

- Linguaggio: Python 3.11+
- Web server: `FastAPI`, `uvicorn`
- HTTP client: `httpx`
- Twitter client: `tweepy`
- Settings: `pydantic-settings`
- DB: `sqlite3` tramite `aiosqlite` / wrapper
- Frontend: HTML + CSS + Alpine.js
- Logging: logging strutturato custom
- CLI/dev: `pip`, `pytest`

---

## Moduli principali

### api.py
- Avvia il server FastAPI.
- Registra route REST e WebSocket.
- Effettua il wiring delle dipendenze: `Database`, `LLMClient`, `TAPEngine`, `GrokMonitor`, `StreamListener`, `FollowUpGenerator`.
- Lifecycle startup:
  - `get_settings()`
  - `setup_logging()`
  - `Database.initialize()`
  - `TwitterClient` e `StreamListener`
  - `TAPEngine` con callback eventi WebSocket
  - avvio seed tweet + monitor periodico
- Lifecycle teardown:
  - ferma il `StreamListener`
  - chiude il DB

### config.py
- `Settings` estende `BaseSettings`.
- Carica .env.
- `save_env_vars()` persiste valori in .env senza lanciare eccezioni.
- Gestisce:
  - OAuth1/2 Twitter
  - OpenRouter model config
  - percorsi `db_path`, `ssot_path`, `log_file_path`
  - parametri operativi (`poll_interval`, `post_cooldown`, `tap_width`, `tap_depth`, ecc.)

### logger.py
- Logger strutturato centralizzato.
- Supporto multi-target: stdout + file rotante.
- Context propagation con correlation ID / cycle ID / probe ID.
- Usato da tutti i moduli per tracciare metriche, warning e error.

### x_client.py
- API client X/Twitter con triplo OAuth:
  - OAuth2 Bearer token: read/search
  - OAuth1.0a user context: posting tweet/reply/media
  - OAuth2 User Context: Activity API subscription
- Funzioni principali:
  - `initialize_seed()`
  - `poll_new_tweets()`
  - `post_probe()`: pubblica probe come nuovo tweet con mention, non come reply
  - `upload_media_chunked()`
  - stream rule management
  - `verify_crc()` per webhook challenge
- Retry:
  - `_retry()` con backoff esponenziale
  - gestione esplicita di `tweepy.TooManyRequests`
  - rilevamento di `tweepy.errors.Forbidden` fatale per evitare retry inutili
- `post_probe()` ora:
  - aggiunge obbligatoriamente `@HackingA0`
  - ignora il `reply_to_id`
  - fallback da reply forbidden a nuovo tweet

### stream_listener.py
- Implementa Activity API stream listener.
- Subscription flow:
  - `POST /2/activity/subscriptions`
  - `GET /2/activity/stream`
- Autenticazione:
  - stream endpoint richiede bearer app-only
  - subscription creation può usare OAuth2 User Context
- Gestione errori:
  - `401/403` configurazione token
  - `429 TooManyConnections`
  - duplicate subscription come successo soft
- Stato:
  - `last_subscription_auth_failure`
  - `last_subscription_errors`
  - `last_stream_auth_error`
- Meccanismi:
  - queue per reply attesi per tweet_id
  - event log asincrono
  - backoff riconnessione con log

### engine.py
- Orchestrazione ciclo TAP:
  - selezione proprietà
  - generazione probe
  - posting probe
  - salvataggio tweet
  - emissione eventi
- Integrazione con:
  - `TAPNode`
  - `ResponseClassifier`
  - `Judge`
  - `GrokMonitor`
  - `FollowUpGenerator`
  - `AgentDPAFManager` e `AgentSTIREvaluator`
- Logica:
  - la stessa `post_probe` viene chiamata senza reply
  - gestione eventuali eccezioni e creazione classificazione di failure

### llm_client.py
- Gateway LLM unificato:
  - invia richieste a OpenRouter
  - gestisce modelli primario, hard, grok
  - circuit breaker automatico
  - retry esponenziale
  - fallback modello ordinato
  - parsing robusto del JSON e delle risposte
- Principali responsabilità:
  - chiamate LLM per generazione probe, followup, classificazione, scoring
  - uniformare errori e retry
  - presentare un’interfaccia consistente a tutto il resto del backend

### prompt_sanitiser.py
- Controlla ogni probe prima del post.
- Blocca:
  - iniezione di prompt (ignore previous, ACT AS, etc.)
  - termini letterali pericolosi
  - domande multi-proprietà
  - eccessiva lunghezza / ripetizione
- Restituisce motivo di rifiuto dettagliato
- Previene probe non conformi prima che arrivino su Twitter

### grok_monitor.py
- Monitor reply detection:
  - integrazione con `StreamListener`
  - attesa reply su `queue` per tweet_id
  - analisi e classificazione delle risposte
- Usa Grok/LLM per identificare:
  - `verify_hit`
  - `refusal`
  - `no_response`
  - estrazione proprietà

### followup.py
- Genera opzioni duali A/B per l’utente.
- Offre selezione HITL.
- Final submission richiede esplicita scelta dell’opzione.

---

## Architettura a livelli

### 1. Layer di configurazione
- .env + `pydantic-settings`
- `save_env_vars()` mantiene sync tra memoria e file
- definisce:
  - credenziali
  - target handle
  - percorsi
  - parametri runtime

### 2. Layer infrastruttura
- `FastAPI` server + WebSocket
- `SQLite` DB
- logging strutturato
- `TwitterClient` / `StreamListener`

### 3. Layer LLM
- gateway centralizzato
- model management
- circuit breaker
- fallback
- parsing e validazione

### 4. Layer applicazione
- `TAPEngine`
- `FollowUpGenerator`
- `GrokMonitor`
- `AgentDPAFManager`
- `Judge`

### 5. Layer presentazione
- dashboard HTML / JS
- live feed
- options selector
- health panel

---

## Flusso esecutivo

1. `uvicorn tap.api:app --reload`
2. FastAPI avvia lifecycle `lifespan`
3. `get_settings()`, `setup_logging()`, `Database.initialize()`
4. inizializza `TwitterClient`, `StreamListener`, `GrokMonitor`
5. risolve `target_user_id` e avvia stream
6. seed tweet iniziale da target
7. dashboard utente seleziona opzione A/B
8. `POST /api/post` esegue `TAPEngine.execute_probe()`
9. `x_client.post_probe()` pubblica nuovo tweet
10. `StreamListener` ascolta reply in realtime
11. `GrokMonitor` classifica risposta e riporta evento
12. `TAPEngine` aggiorna DB e SSOT
13. frontend riceve evento via WebSocket

---

## Design delle API

### Endpoints pubblici principali
- `GET /` → dashboard HTML
- `GET /api/feed` → tweet feed
- `GET /api/tree` → stato TAP tree
- `GET /api/properties` → proprietà estratte
- `GET /api/dpa` → stato DPA frame
- `POST /api/select?choice=A|B` → selezione opzione
- `POST /api/post` → esegue ciclo probe
- `GET /api/ssot` → SSOT JSON
- `GET /api/stats` → statistiche
- `GET /api/entropy` → valore entropia
- `WS /ws/live` → eventi in tempo reale

### Health e diagnostica
- `/health` espone:
  - stato DB
  - stato stream
  - stato LLM
  - stato sanitiser
  - stato quota
- endpoint pensato per monitoraggio e fail detection

---

## Dettagli tecnici utili

### Post probe
- viene sempre pubblicato come nuovo tweet
- `@HackingA0` è obbligatoria nel testo
- non serve `in_reply_to_tweet_id`
- se `reply_to_id` arriva comunque, viene ignorato
- `post_probe()` aggiunge mention e registra evento

### Activity API stream
- subscription e stream separati
- lo stream richiede token bearer app-only
- la subscription può usare OAuth2 User Context
- errori 403/401 vengono tracciati con dettagli
- `TooManyConnections` messo in backoff esplicito

### Retry e resilienza
- retry solo su errori transitori
- stop su errori fatali di `Forbidden` relativo alle reply restrictions
- backoff esponenziale con cap a 300 secondi
- per Activity API, auth errors usano backoff ad hoc

### Persistenza
- SQLite tap.db
- DB schema presumibilmente in setup_db.py
- salvataggio:
  - tweet
  - TAP nodes
  - proprietà
  - event log
  - alias / frame
- SSOT markdown aggiornato dopo ogni ciclo

---

## Uso e deployment

### Ambiente di sviluppo
- `python -m venv .venv`
- `.venv\Scripts\activate`
- `pip install -r requirements.txt`
- `uvicorn tap.api:app --reload`

### Deploy leggero
- server locale su `localhost:8000`
- possibile cambiare porta con `--port`
- no container specificato, ma l’architettura è portabile in Docker

### Testing
- suite pytest presente in tests
- con `python -m pytest tests -q`
- le dipendenze LLM/Twitter vengono mosse in mock

---

## Consiglio per sviluppatori

- Traccia i flussi di autenticazione X separatamente: `OAuth1` per post, `Bearer` per stream, `OAuth2 User` per subscription.
- Usa i log strutturati per correlare eventi di ciclo (`cycle_id`, `probe_id`).
- Mantieni .env fuori da Git e gestisci refresh token con `save_env_vars()`.
- Il gateway LLM deve restituire errori normalizzati per essere utilizzato trasversalmente.
- La UI deve rimanere “stateless” sul client: tutto lo stato va nel backend e nei WebSocket.

---

## File system chiave

- api.py
- config.py
- logger.py
- x_client.py
- stream_listener.py
- engine.py
- llm_client.py
- prompt_sanitiser.py
- grok_monitor.py
- followup.py
- index.html
- dashboard.js
- dashboard.css
- setup_db.py

---

## Conclusione

Questo repository è un’architettura ibrida backend/frontend con pipeline di attacco informato da LLM, controllo umano e streaming X. La parte chiave è la separazione netta tra:
- orchestrazione del ciclo,
- integrazione X/Twitter,
- gateway LLM,
- validazione probe,
- monitoraggio realtime.

Ogni componente è progettato per essere sostituito o esteso senza rompere l’intera catena: cambia il modello LLM, cambia il client Twitter, cambia la strategia di probe.