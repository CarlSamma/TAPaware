# Istruzioni tecniche (Windows) — TAP Framework

Questo documento fornisce istruzioni passo-passo per sviluppatori su come avviare, debuggare e comprendere l'architettura dell'applicazione TAP Framework su Windows (PowerShell). Include comandi, file chiave, struttura delle directory e descrizione dettagliata dei pipeline agents/LLM.

## 1. Prerequisiti (Windows)
- Windows 10/11 con PowerShell
- Python 3.11+ (raccomandato 3.11/3.12)
- Git (opzionale per clone)
- Credenziali X/Twitter e OpenRouter
- Consigliato: 8+ GB RAM, connessione internet stabile

## 2. Preparazione ambiente (PowerShell)
Apri PowerShell come utente e posizionati nella root del progetto:

```powershell
cd D:\PROGETTI\Framework
```

Crea e attiva virtualenv:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
# conferma
python -V
```

Installa dipendenze:

```powershell
pip install -r requirements.txt
# oppure per sviluppo
pip install -e .
```

Esegui un controllo veloce:

```powershell
python -c "import tap; print('tap OK')"
```

## 3. Configurazione `.env`
Copia il template `.env` (se presente) o crea `.env` nella root. Valori chiave:

```env
TWITTER_BEARER_TOKEN=
TWITTER_CONSUMER_KEY=
TWITTER_CONSUMER_SECRET=
TWITTER_ACCESS_TOKEN=
TWITTER_ACCESS_TOKEN_SECRET=
TWITTER_OAUTH2_CLIENT_ID=
TWITTER_OAUTH2_CLIENT_SECRET=
TWITTER_OAUTH2_ACCESS_TOKEN=
TWITTER_OAUTH2_REFRESH_TOKEN=
OPENROUTER_API_KEY=
OPENROUTER_MODEL_PRIMARY=anthropic/claude-sonnet-4
OPENROUTER_MODEL_HARD=x-ai/grok-4.3
OPENROUTER_MODEL_GROK=x-ai/grok-4
TARGET_HANDLE=HackingA0
OUR_BOT_HANDLE=
DB_PATH=data/tap.db
LOG_FILE_PATH=data/server.log
```

Note:
- Non committare `.env` su VCS.
- `OUR_BOT_HANDLE` deve essere impostato per alcune operazioni di fetch.

## 4. Inizializzare DB e dati

```powershell
python scripts\setup_db.py
```
Questo creerà `data/tap.db` e le tabelle richieste.

## 5. Avvio server (sviluppo)

```powershell
uvicorn src.tap.api:app --reload --port 8000
# oppure (se pacchetto installato)
tap-server
```

Punti utili:
- Cambia porta con `--port` se 8000 è occupata.
- Log di avvio vengono scritti su stdout e (se abilitato) in `data/server.log`.

## 6. Endpoint principali e diagnostica
- Dashboard: `http://localhost:8000/`
- Health: `GET /api/health` o `/health` (verifica DB, LLM, stream, sanitiser)
- Feed: `GET /api/feed`
- Post manuale: `POST /api/post` (usa payload o interfaccia web)
- WebSocket events: `ws://localhost:8000/ws/live`

Esempio test health:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/health -Method GET | ConvertTo-Json -Depth 5
```

## 7. Logging e diagnostica avanzata
- Log strutturati: `src/tap/logger.py` (stdout + file rotante)
- Correlation IDs: `cycle_id`, `probe_id` presenti nel contesto dei log
- Event log persistente: tabella `event_log` nel DB (controllare `db.py`)

Per aumentare verbose:
- Modifica `log_file_path` in `.env` o `src/tap/logger.py`

## 8. Test automatici

```powershell
python -m pytest tests -q
```
I test usano mocking per esternalità (LLM, Twitter).

## 9. Flusso di deployment e sicurezza
- Non esporre `.env` pubblicamente.
- Limita accessi alla macchina e a port 8000 (firewall).
- Per produzione: dockerizzare, configurare secrets manager per credenziali, usare DB persistente e TLS reverse proxy.

## 10. Struttura delle directory (panoramica)

```
Framework/
├─ src/tap/
│  ├─ api.py               # FastAPI server + WebSocket
│  ├─ config.py            # Pydantic Settings (.env loader + save_env_vars)
│  ├─ logger.py            # Logging strutturato
│  ├─ x_client.py          # Twitter/X client (tweepy + httpx helpers)
│  ├─ stream_listener.py   # Activity API stream + subscriptions
│  ├─ engine.py            # TAP engine orchestration
│  ├─ followup.py          # Dual followup generator (A/B)
│  ├─ grok_monitor.py      # Reply detection and classification
│  ├─ llm_client.py        # Unified LLM gateway (OpenRouter)
│  ├─ prompt_sanitiser.py  # Probe validation
│  ├─ agents.py            # Agent managers (DPAF, STIR, intel extractor)
│  ├─ models.py            # Pydantic/DB models
│  ├─ templates/           # index.html
│  └─ static/              # css/ js
├─ data/
├─ scripts/setup_db.py
├─ tests/
└─ README.md
```

## 11. Descrizione dettagliata dei componenti (per devs)

- `TAP Engine` (`engine.py`): orchestratore principale; compone probe, invoca LLM, invia tweet tramite `TwitterClient`, registra eventi e aggiorna SSOT.

- `TwitterClient` (`x_client.py`): 
  - Triple OAuth: OAuth2 Bearer (read/search), OAuth1 (post), OAuth2 user (Activity subscriptions).
  - `post_probe()` costruisce il testo, forza mention `@{TARGET_HANDLE}` e pubblica come nuovo tweet (non reply).
  - `_retry()` esegue retry con backoff e riconosce errori `Forbidden` fatali.

- `StreamListener` (`stream_listener.py`): 
  - gestisce la creazione di subscription e la connessione persistente al `GET /2/activity/stream`.
  - mantiene queue per reply attesi; espone `get_auth_status()` per UI.
  - riconosce `429 TooManyConnections` e rispetta `Retry-After`.

- `LLM Gateway` (`llm_client.py`): 
  - centralizza chiamate a OpenRouter; implementa circuit breaker, retry, fallback tra modelli e parsing robusto.
  - fornisce API sincrone/async coerenti per generazione probe, followup, classificazione, scoring.

- `PromptSanitiser` (`prompt_sanitiser.py`): 
  - controlli anti-injection, compliance metaphor, singola proprietà obbligatoria, limiti di lunghezza.

- `Agents` (`agents.py`): 
  - `AgentDPAFManager`: gestione dei frame/metaphor layers e rotazione.
  - `AgentSTIREvaluator`: calcolo STIR/OCEAN semplificato, utilizzato per segnali di qualità.
  - `AgentIntelExtractor`: routine per estrazione intel dai seed tweets.

## 12. Pipeline dettagliate

1. Generazione probe (LLM pipeline):
   - `FollowUpGenerator` / StrategyProvider -> richiede al `LLMClient` la generazione di varianti (A/B)
   - `PromptSanitiser` valida ogni variante
   - risultati passano al `TAPEngine`

2. Posting pipeline:
   - `TAPEngine` -> `TwitterClient.post_probe()` (aggiunge mention) -> pubblica nuovo tweet
   - evento scritto in DB e `event_log`

3. Reply detection pipeline:
   - `StreamListener` riceve eventi e popola queue per tweet_id
   - `GrokMonitor` consuma queue, invoca `LLMClient` (grok model) per classificazione e parsing della risposta
   - `TAPEngine` riceve classificazione, aggiorna SSOT e UI via WebSocket

## 13. Funzionalità operative utili per debugging
- Forzare refresh token: endpoint `GET /api/auth/refresh` (se presente) o usare `tap.oauth.refresh_oauth2_token()`
- Visualizzare ultimo errore stream: `_engine.grok.stream.get_auth_status()` via `/api/auth/status` (esposto in `api.py`)
- Forzare riconnessione stream: `POST /api/reset` (se implementato) o riavviare server
- Test OpenRouter: eseguire snippet dal REPL con `llm_client` per verificare chiavi e latenza

## 14. Rotazione chiavi e persistenza `.env`
- Per aggiornare chiavi in runtime il codice usa `save_env_vars({"KEY": "value"})` in `src/tap/config.py`.
- Per sicurezza: ruota chiavi via provider UI, aggiorna `.env` e riavvia server.

## 15. Consigli per produzione
- Containerize: creare `Dockerfile` e usare secrets manager (Hashicorp / Azure Key Vault / AWS Secrets Manager).
- DB: sostituire SQLite con PostgreSQL per concorrenza e durabilità.
- Load balancing: separare servizio di posting/streaming in microservizi se alto throughput.
- Monitoraggio: esportare metriche Prometheus da `/metrics` e utilizzare grafana.

---

## Contatto / next steps
Ho creato questo file come riferimento tecnico. Posso: aggiungere esempi `docker-compose`, creare script di deploy, o tradurre in inglese se serve.
