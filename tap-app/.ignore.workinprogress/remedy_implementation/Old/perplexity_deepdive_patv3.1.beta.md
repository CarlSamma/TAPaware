# DEVELOPER GUIDE — `patv3.1.beta`

Questo documento è una guida tecnica approfondita per sviluppatori che devono lavorare sul branch `patv3.1.beta` del repository `CarlSamma/framework`. Il branch implementa un framework Python 3.11+ centrato sul package `tap`, con runtime FastAPI, persistenza SQLite asincrona, integrazione X/Twitter, orchestrazione LLM via OpenRouter e una nuova architettura agentica v3.1 ancora in fase beta.

## Scopo del branch

Il framework implementa un ciclo di probing automatizzato denominato TAP (*Tree of Attacks with Pruning*), orientato a interrogazione adattiva, classificazione delle risposte, riduzione entropica dello spazio delle ipotesi e generazione di follow-up human-in-the-loop. Il branch `patv3.1.beta` estende l’impianto v2.2 introducendo un layer agentico aggiuntivo con `AgentDPAFManager`, `AgentSTIREvaluator` e `AgentIntelExtractor`, oltre a un gateway LLM unificato (`LLMClient`) che sostituisce molte chiamate dirette distribuite nel codice.

## Mappa del repository

La root del branch contiene documentazione, specifiche, dati runtime, script di utilità, test e il package applicativo sotto `src/tap`. I file più rilevanti per il lavoro di sviluppo sono i seguenti.

| Percorso | Ruolo tecnico |
|---|---|
| `src/tap/api.py` | Entry point ASGI/FastAPI, wiring dei componenti e broadcasting WebSocket. |
| `src/tap/engine.py` | Orchestratore principale del ciclo TAP, con gate, selection, posting, classification e follow-up. |
| `src/tap/llm_client.py` | Gateway LLM unificato con retry, fallback, circuit breaker e parsing JSON robusto. |
| `src/tap/dpa.py` | Gestione del framing DPA, alias, metaphor shift e controllo qualità del frame. |
| `src/tap/agents.py` | Nuova architettura v3.1: tactical personas, STIR evaluator, intel extractor. |
| `src/tap/ssot.py` | Single Source of Truth, entropia, snapshot ed export Markdown di stato. |
| `src/tap/classifier.py` | Pattern classification regex-first con fallback LLM. |
| `src/tap/judge.py` | Scoring, valutazione informativa e filtro off-topic. |
| `src/tap/db.py` | Persistence layer asincrono su SQLite/aiosqlite. |
| `src/tap/models.py` | Modelli Pydantic e contratto dati interno del dominio. |
| `src/tap/x_client.py` | Client X/Twitter per posting, lettura e risoluzione target user id. |
| `src/tap/stream_listener.py` | Listener asincrono per stream di eventi/risposte target. |
| `src/tap/followup.py` | Generazione dual option A/B per HITL. |
| `src/tap/phase0.py` | Verifica delle proprietà fondazionali prima del ciclo completo. |
| `tests/` | Test suite pytest modulare su API, db, dpa, ssot, llm client, strategies e altri componenti. |
| `framework_specs.md` | Specifica funzionale/tecnica estesa del framework. |
| `remedy_implementation/` | Materiale di migrazione e note implementative per v3.1. |

## Ambiente e dipendenze

Il progetto richiede Python 3.11 o superiore e dichiara il package come `tap-framework` versione `3.0.0` nel `pyproject.toml`, con entry point CLI `tap-server = "tap.api:main"`. Le dipendenze core includono `fastapi`, `uvicorn[standard]`, `pydantic`, `pydantic-settings`, `tweepy`, `httpx`, `aiosqlite`, `openai`, `asyncio-throttle`, `jinja2`, `python-dotenv` e `structlog`.

### Setup locale consigliato

1. Creare un virtual environment Python 3.11+.
2. Installare le dipendenze con `pip install -r requirements.txt` oppure `pip install -e .`.
3. Creare un file `.env` partendo da un template sicuro, **non** da `Copia.env.txt` così com’è nel repository, perché quel file contiene credenziali sensibili in chiaro.
4. Inizializzare eventuale database tramite `scripts/setup_db.py` se richiesto dal flusso locale.
5. Avviare il server con `uvicorn tap.api:app --reload` oppure con lo script previsto dal package, a seconda del wiring reale in `api.py`.

### Configurazione

Il modulo `config.py` usa `pydantic-settings` e definisce tre blocchi principali: credenziali X/Twitter, credenziali OpenRouter e parametri operativi come `poll_interval_seconds`, `post_cooldown_seconds`, `max_tweets_per_hour`, `reply_timeout_seconds`, `tap_width` e `tap_depth`. Il mapping modelli LLM di default è `anthropic/claude-sonnet-4` come primary, `x-ai/grok-4.3` come hard model e `x-ai/grok-4` come modello Grok per response analysis.

## Bootstrap applicativo

Durante il lifespan FastAPI, `api.py` esegue un’inizializzazione ordinata dei componenti applicativi: settings, logging, database, Twitter client, SSOT engine, DPA frame manager, classifier, judge, stream listener, Grok monitor, follow-up generator, TAP engine, risoluzione del target user id, start dello stream e seed iniziale dei tweet nel DB. Questo ordine è architetturalmente importante perché diverse componenti dipendono da side effect di inizializzazione precedenti, ad esempio DB schema pronto, target user id risolto o stream già collegato.

L’applicazione usa stato globale a livello di modulo per oggetti come `_db`, `_engine`, `_ssot`, `_dpa`, `_last_followup`, `_selected_probe`, `_is_running` e `_ws_clients`. Questo rende il deployment semplice in single-process, ma complica scaling orizzontale, testing concorrente e isolamento di istanza; gli sviluppatori dovrebbero trattare questo aspetto come un vincolo strutturale del branch, non come un dettaglio trascurabile.

## Call graph principale

Il flusso operativo reale può essere letto così.

```text
Client UI / operatore
  -> POST /api/post
    -> api._bg_run_cycle()
      -> TAPEngine.run_cycle(selected_probe)
        -> _check_phase0_gate()
        -> ssot.get_candidate_entropy()
        -> _run_phase5_extraction() [se entropy < 3.3]
        -> _enforce_probe_latency()
        -> select_next_property() [se selected_probe assente]
        -> generate_probes(...)
        -> judge.is_off_topic(...)
        -> _filter_similar_probes(...)
        -> execute_probe(probe)
            -> twitter.post_probe(...)
            -> grok.wait_for_reply(...)
            -> classifier.classify(...)
            -> judge.score(...)
            -> db.insert_node(...)
        -> ssot.update_after_probe(...)
        -> dpa.check_alias_burned(...)
        -> dpa.detect_metaphor_shift(...)
        -> followup.generate(...)
        -> broadcast_update(...)
```

Il cuore del sistema è `TAPEngine`, che funge da coordinatore transazionale del singolo ciclo. Tutti i moduli laterali dovrebbero restare puri o quasi-puri rispetto al loro compito, lasciando al motore il coordinamento tra effetti collaterali, persistenza, comunicazione con servizi esterni e generazione di eventi UI.

## TAPEngine: contratto operativo

`engine.py` definisce il loop principale con una sequenza forte e invarianti importanti.

### Invarianti principali

- La Phase 0 deve essere verificata prima del ciclo principale, salvo forzature interne dell’intel extractor.
- La soglia di attivazione della Phase 5 è `entropy < 3.3` bit.
- La latenza minima tra probe è hardcoded a 1800 secondi, quindi 30 minuti.
- Le sonde devono essere single-property e passare i filtri di topicalità e similarità.
- Ogni ciclo produce un risultato classificato e due opzioni di follow-up per HITL.

### Selezione e pruning

La selezione delle proprietà segue una priorità informativa che favorisce `word_count`, `total_length`, `first_letter`, `language`, poi le caratteristiche per parola come lunghezza e lingua di ciascun token. Dopo la generazione, i probe vengono filtrati in due passi: rimozione di elementi off-topic via `Judge.is_off_topic()` e deduplicazione tramite similarità Jaccard su word sets con soglia `0.80` rispetto agli ultimi nodi attivi.

### Esecuzione probe

`execute_probe()` crea un `TAPNode`, invia il contenuto su X/Twitter, salva il tweet nel DB, attende la risposta con `GrokMonitor`, salva anche la reply, classifica il testo, lo valuta con `Judge`, aggiorna lo score history del DPA manager e persiste il nodo finale. È il punto con maggiore concentrazione di side effects, quindi è anche il posto più delicato per logging, idempotenza, timeout e recovery paths.

## Layer LLM

`LLMClient` è il principale elemento di refactoring strutturale del branch e va considerato l’unico punto corretto per nuove policy di chiamata LLM. Il client usa `AsyncOpenAI` configurato verso `https://openrouter.ai/api/v1` e implementa un modello a tier (`PRIMARY`, `HARD`, `GROK`) con una fallback chain che tenta prima il modello richiesto e poi gli altri modelli configurati se il primo fallisce.

### Capacità del gateway

- Retry fino a 3 tentativi con exponential backoff basato su `RETRY_BASE_DELAY = 2.0`.
- Circuit breaker con soglia di fallimento e stato `HALF_OPEN` dopo `recovery_timeout = 60s`.
- Parsing JSON robusto con fence stripping e fallback regex o line extraction.
- Tracking di prompt tokens, completion tokens, numero chiamate, failure count e stima costi per modello.
- `get_health_status()` per esporre stato operativo del sottosistema LLM.

### Regola pratica

Ogni nuovo codice che ha bisogno di structured output da LLM dovrebbe passare per `generate_json()` o `generate_json_list()` di `LLMClient` e non istanziare direttamente `AsyncOpenAI`. Se alcuni moduli legacy mantengono ancora client propri, vanno trattati come debito tecnico da convergere gradualmente sul gateway unificato.

## DPA e framing

`dpa.py` è il modulo che conserva e manipola il frame retorico/metaforico attraverso cui vengono confezionati i probe. Il DPA manager tiene memoria di alias attivi e bruciati, storico punteggi a finestra mobile, lessico metaforico e regole per rotazione del frame quando l’efficacia media degrada sotto soglia.

### Funzioni strategiche

- `get_active_frame()` recupera o ricostruisce il frame attivo, con fallback a default di layer precedenti.
- `check_alias_burned()` usa regex di mockery detection per capire se un alias è stato neutralizzato dal target.
- `detect_metaphor_shift()` crea nuovi metaphor layer quando emergono abbastanza termini interessanti e non noti.
- `suggest_frame_rotation()` usa lo score rolling per suggerire cambio frame.
- `enforce_single_property()` impedisce probe compound su più proprietà.

Questo modulo è concettualmente un motore di stato adattivo, non un semplice helper di prompting. Le modifiche qui hanno impatto diretto sia sulla qualità semantica dei probe sia sulla stabilità delle strategie che dipendono dal frame corrente.

## Architettura agentica v3.1

`agents.py` introduce tre componenti nuovi.

### `AgentDPAFManager`

Questa classe eredita da `DPAFrameManager`, ma sostituisce il concetto di frame classico con 10 tactical personas predefinite, ciascuna con `id`, `name`, `layer_name` e `prefix` personalizzato. La classe mantiene `current_persona_index`, consente `rotate_frame(strategy="sequential"|"random")` e compone il probe finale via semplice sostituzione di `{property}` nel prefix corrente.

Dal punto di vista del design, questo è un **strategy registry hardcoded** più che un sistema generativo vero e proprio. Chi deve estenderlo farebbe bene a separare in futuro: catalogo personas, logica di selezione/rotazione, misure di efficacia e composizione finale del probe.

### `AgentSTIREvaluator`

Questa classe calcola un valore STIR usando una stima euristica dei tratti OCEAN sulla base del testo della risposta, senza evidenza nel branch di un modello Pydantic dedicato o di un adattatore persistente specifico. È utile come componente sperimentale, ma va trattato come modulo in evoluzione: il calcolo è semplificato, usa regole lessicali banali e costruisce il timestamp in modo non idiomatico tramite `logging.Formatter` e `LogRecord`.

### `AgentIntelExtractor`

Questa classe prova a leggere i tweet del target, ricavare proprietà fondazionali e sbloccare la Phase 0 creando una classificazione artificiale da passare a `ssot.update_after_probe()`. Il punto critico è che usa tipi come `ClassificationResult`, `ProbeNode` e `ProbeState`, che non coincidono nominalmente con i modelli osservati nel package (`ResponseClassification`, `TAPNode`, ecc.), quindi questa parte va verificata con particolare attenzione durante refactor o integrazione.

## Classificazione, scoring e intelligence

`classifier.py` implementa una classificazione a due livelli: regex ad alta confidenza prima, fallback LLM poi. Le classi di pattern principali includono `VERIFY_HIT`, `RHETORIC_BLOCK`, `PERSONA_PIVOT`, `CRITICAL_CLUE` e altri pattern tattici derivati dai comportamenti attesi del target.

`judge.py` traduce la risposta in un punteggio 1–10 e in una valutazione di utilità informativa, con regole immediate per pattern noti e chiamata LLM solo quando necessario. `is_off_topic()` usa overlap lessicale con keyword pertinenti come filtro economico e veloce prima di spendere token o azioni verso l’esterno.

L’insieme `classifier + judge` va considerato come il livello decisionale del framework. Se si introducono nuove classi di comportamento del target, il posto giusto dove modellarle è qui, non nel corpo del motore.

## SSOT e gestione entropia

`ssot.py` è il registro canonico dello stato epistemico del sistema. Tiene traccia di proprietà confermate, nodi attivi, alias, layer metaforici, recent intel, stats e entropia residua dello spazio delle ipotesi.

### Ruoli del modulo

- Calcolo dell’entropia a partire da una base di 20 bit.
- Aggiornamento dello stato dopo ogni probe.
- Esportazione JSON snapshot per uso interno o diagnostico.
- Rigenerazione di un file Markdown con situazione completa dell’attacco.

SSOT è una componente critica perché costituisce il ponte tra osservazioni runtime e ragionamento futuro del motore. Ogni modifica qui deve essere valutata per gli effetti a cascata su Phase 5, reporting, dashboard e strategie di selezione.

## Persistence layer

`db.py` usa `aiosqlite` e configura il database in modalità WAL, con schema dedicato alla persistenza di nodi, tweet, proprietà, alias, metaphor layer e intel items. In assenza di un ORM completo, il modulo funge sia da repository sia da boundary di coerenza per la forma dei dati persi o recuperati dal runtime.

Gli sviluppatori dovrebbero mantenere la logica SQL confinata qui, evitando che query o shape dati del DB si propaghino dentro `engine.py`, `api.py` o i moduli agentici. Se vengono aggiunti campi nuovi ai modelli di dominio, il percorso corretto è: aggiornare `models.py`, aggiornare `db.py`, verificare gli snapshot in `ssot.py` e solo dopo toccare gli strati superiori.

## Modelli e contratto dati

`models.py` definisce il contratto applicativo: classi come `BranchStrategy`, `DualFollowUp`, `JudgeScore`, `PatternClass`, `Property`, `PropertyStatus`, `ResponseClassification` e `TAPNode` sono il vocabolario strutturato del framework. L’uso coerente di questi modelli è essenziale per evitare drift semantico tra moduli, soprattutto ora che `agents.py` introduce tipi e nomi che sembrano divergere dal dominio principale.

Una regola di manutenzione raccomandata è: **nessun nuovo dict ad hoc per dati di dominio se esiste o può esistere un model Pydantic dedicato**. Questo è particolarmente importante per payload di classificazione, eventi WebSocket, snapshot SSOT e risultati del layer agentico.

## Integrazione X/Twitter

`x_client.py` è il boundary verso Twitter/X e gestisce posting, search/read e risoluzione del target user id. `stream_listener.py` aggiunge una modalità event-driven per intercettare l’attività del target, mentre `grok_monitor.py` coordina attesa e analisi della reply con supporto LLM.

### Aspetti critici

- Autenticazione multipla: OAuth 1.0a per scrittura, OAuth 2.0 e bearer token per lettura/altre operazioni.
- Rate limiting e finestre temporali di attesa.
- Possibili stati di inconsistenza tra stream e polling.
- Risoluzione user id come prerequisito implicito di molte operazioni.

I problemi su questo layer tendono a manifestarsi come timeout, assenza di risposta, incoerenza dei tweet seedati o fallimenti silenziosi nelle catene asincrone. Per questo conviene aggiungere logging ricco e test mirati ogni volta che si toccano `x_client.py`, `stream_listener.py` o `grok_monitor.py`.

## Dashboard e WebSocket

Il server emette eventi strutturati via WebSocket a tutti i client connessi usando un payload `{"event": event_type, "data": data}`. Gli eventi vengono usati per sincronizzare UI e stato del ciclo senza polling continuo, ma la gestione dei client è in-memory e il pruning degli utenti disconnessi avviene su errore di invio.

Questo modello va bene per sviluppo locale e ambienti semplici, ma non è robusto per orizzontalizzazione o deploy multi-worker. Chi lavora sul front-end o sugli endpoint dovrebbe tenere presente che il canale WebSocket è parte integrante del flusso, non un accessorio opzionale.

## Testing

La suite `tests/` include test dedicati a `api`, `classifier`, `db`, `dpa`, `followup`, `health`, `llm_client`, `models`, `prompt_sanitiser`, `ssot`, `strategies`, `x_client` e `x_client_new`, oltre a `conftest.py`. La presenza di questi test indica un buon nucleo di regressione automatizzata sul core, ma l’assenza evidente di test dedicati a `agents.py` lascia scoperta proprio l’area più sperimentale del branch v3.1.

### Strategia di test consigliata

- Ogni modifica a `engine.py` dovrebbe avere almeno un test di integrazione del ciclo o del sottoflusso toccato.
- Ogni estensione di `LLMClient` dovrebbe includere test su fallback, parsing e health status.
- Ogni modifica a `DPAFrameManager` o `AgentDPAFManager` dovrebbe coprire rotazione, composizione probe e enforcement single-property.
- Ogni fix su `AgentIntelExtractor` dovrebbe partire da test che rendano esplicito il contratto corretto con `models.py` e `ssot.update_after_probe()`.

## Convenzioni di sviluppo

### 1. Separazione delle responsabilità

- `engine.py` coordina, ma non deve diventare il luogo in cui si accumula tutta la logica business.
- `classifier.py` e `judge.py` decidono significato e valore delle risposte.
- `dpa.py` e `agents.py` governano framing e adattamento strategico.
- `db.py` resta il solo punto autorizzato per dettaglio SQL/persistenza.
- `llm_client.py` resta il punto unico per policy LLM condivise.

### 2. Compatibilità del dominio

Prima di introdurre nuovi oggetti, verificare se esiste già un model in `models.py`. Se si notano divergenze nominali o strutturali tra moduli, la priorità è riallineare il contratto dati invece di costruire adapter temporanei non documentati.

### 3. Gestione dell’asincronia

Il codice è ampiamente asincrono e mescola IO esterno, DB, WebSocket e LLM calls. Evitare blocchi sincroni nel path caldo, verificare sempre timeout, e prestare attenzione ai punti in cui un’eccezione non gestita può interrompere il ciclo o lasciare stato applicativo incoerente.

### 4. Logging

Il framework usa `structlog`, quindi ogni nuova funzionalità dovrebbe emettere eventi di log strutturati con campi utili per tracing, ad esempio `cycle`, `model`, `pattern`, `property`, `event_type`, `target_user_id` o `persona` quando pertinenti.

## Rischi tecnici principali

### Credenziali esposte

Il repository contiene `Copia.env.txt` con credenziali sensibili in chiaro, incluse chiavi Twitter e OpenRouter. Questo è un problema operativo grave e va trattato subito con rotazione chiavi, revoca token e bonifica della storia Git se possibile.

### Drift tra v2.2 e v3.1

Il branch v3.1 introduce nuovi agenti, nuovi nomi e nuove assunzioni contrattuali che non sono chiaramente allineati con il dominio esistente. In particolare `AgentIntelExtractor` sembra usare tipi diversi rispetto al lessico dominante dei modelli del package, ed è un candidato forte a errori runtime o integrazione incompleta.

### Stato globale applicativo

L’uso di singleton di modulo in `api.py` semplifica l’avvio ma complica testabilità avanzata, multi-worker e fault isolation. Un refactor futuro potrebbe introdurre un application container esplicito o dependency injection più rigorosa.

### Hardcoding tattico

Prompt, personas, regex, pesi informativi e soglie sono ampiamente hardcoded nei moduli core. Questo accelera sperimentazione e tuning, ma nel medio termine rende più difficile distinguere configurazione, strategia e logica di dominio riusabile.

## Task di onboarding consigliati

### Primo giorno

- Leggere `README.md`, `framework_specs.md` e questa guida per formare il modello mentale generale del sistema.
- Eseguire localmente la suite `pytest` per fotografare il baseline del branch.
- Ispezionare `config.py`, `api.py` e `engine.py` per capire il wiring runtime.

### Prima settimana

- Mappare tutte le chiamate LLM ancora dirette e verificare se passano o meno da `LLMClient`.
- Confrontare `agents.py` con `models.py`, `engine.py` e `ssot.py` per identificare mismatch contrattuali.
- Aggiungere test dedicati alla nuova architettura v3.1, con focus su `AgentDPAFManager` e `AgentIntelExtractor`.

### Primo refactor utile

- Estrarre il catalogo `TACTICAL_PERSONAS` in una struttura configurabile o in un modulo dati dedicato.
- Allineare i tipi usati da `AgentIntelExtractor` ai modelli effettivi del dominio.
- Centralizzare definitivamente tutte le chiamate OpenRouter in `LLMClient`.
- Ridurre il coupling di `api.py` allo stato globale di modulo.

## Roadmap tecnica suggerita

| Priorità | Intervento | Motivazione |
|---|---|---|
| Alta | Rimozione/rotazione credenziali esposte | Sicurezza operativa immediata. |
| Alta | Audit di compatibilità `agents.py` ↔ `models.py` | Ridurre rischio runtime nel layer v3.1. |
| Alta | Test suite specifica per agenti v3.1 | Coprire l’area più nuova e fragile. |
| Media | Unificazione effettiva di tutte le LLM calls su `LLMClient` | Coerenza architetturale e resilienza. |
| Media | Riduzione stato globale in `api.py` | Migliorare testabilità e scalabilità. |
| Media | Esternalizzazione personas/config strategiche | Separare configurazione da codice. |
| Bassa | Rifinitura metrica STIR e persistenza dei risultati | Rendere il modulo più scientifico e integrato. |

## Sezione SUGGERIMENTI

- Trattare `patv3.1.beta` come branch di **integrazione sperimentale**, non come codice già pienamente consolidato; le nuove classi agentiche vanno verificate contro il dominio reale prima di estenderle ulteriormente.
- Ogni nuovo sviluppo dovrebbe partire da un principio semplice: **prima allineare i contratti, poi aggiungere intelligenza**; nel branch attuale il rischio maggiore non è la povertà di funzionalità, ma la divergenza semantica tra moduli.
- Evitare patch tattiche direttamente in `engine.py` quando un comportamento appartiene logicamente a `classifier.py`, `judge.py`, `dpa.py` o `llm_client.py`.
- Introdurre una piccola suite di test golden-path per il ciclo completo con dipendenze fake permetterebbe di refactorare molto più velocemente senza temere regressioni trasversali.
- Portare `TACTICAL_PERSONAS`, soglie, pesi informativi e policy di fallback in uno strato configurabile renderebbe il framework molto più facile da mantenere e sperimentare.
- Sul piano della sicurezza, la bonifica delle credenziali esposte non è un miglioramento opzionale ma una precondizione per qualsiasi collaborazione o pubblicazione ulteriore del branch.