<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Istruzioni Approfondite per AI Agents Coders

## Obiettivo

Questo documento definisce il planning operativo, le dipendenze, i criteri di accettazione e i task tecnici per implementare tre miglioramenti prioritari nella branch `HybridGUI_ev`: refactor del Fusion Engine, seeding strutturato del V-Genome Neo4j e creazione del Twitter Adapter di integrazione. Il punto di partenza reale del repository mostra un `CartesianPruningFusionEngine` Python ancora stub, che costruisce il `prompt_text` come semplice join dei nomi delle tecniche e ordina i candidati solo per `expected_asr * expected_stealth` . Lo schema Neo4j esiste già e include vincoli, nodi seed di esempio e relazioni `:TARGETS`, `:COUNTERS`, `:COMPLEMENTS`, ma è solo uno script statico e non una pipeline di bootstrap eseguibile . I contratti condivisi mostrano che i componenti devono produrre oggetti `FusedPrompt`, `DiscoveryResult` e `TechniqueRef` compatibili con Pydantic v2, con feature vector obbligatorio di lunghezza 128 e `PlatformConstraint` tipizzato .

## Stato Attuale del Codice

Il Fusion Engine attuale genera tutte le combinazioni da 1 a `max_combo_size`, calcola medie semplici di `asr` e `stealth`, produce un vettore 128-dimensionale via hash sugli ID e restituisce `FusedPrompt` validi ma semanticamente poveri, perché il testo finale non è un payload reale ma una concatenazione di etichette di tecniche . Questo significa che l’interfaccia dati è già corretta verso `shared.models`, ma la logica decisionale e compositiva non è ancora allineata allo scopo del modulo . In parallelo, il file di schema V-Genome contiene già un modello dati utile per il grafo, quindi il lavoro prioritario non è ridisegnare il database ma automatizzare bootstrap, idempotenza e arricchimento dei seed .

## Architettura Target

L’architettura target deve essere organizzata in tre stream di lavoro coordinati ma indipendenti in merge order. Stream A: sostituzione dello stub di fusione con un motore semantico Python-first compatibile con una futura migrazione Rust, mantenendo invariati i contratti `FusedPrompt` e `TechniqueRef` . Stream B: introduzione di un bootstrap service o script idempotente che applichi schema + seed di tecniche + relazioni + metadata al V-Genome senza dipendere da esecuzioni manuali su Neo4j Browser . Stream C: creazione di `src/adapters/social/twitter_adapter.py` come integration layer orientato ai `DiscoveryResult`, senza duplicare la logica HTTP già concentrata nel client X/Twitter esistente, ma esponendo una superficie più adatta ai workflow applicativi .

## Stream A — Fusion Engine Semantico

### Obiettivo tecnico

L’obiettivo è trasformare `generate_payloads()` da enumeratore di combinazioni a selettore di prompt candidati realmente utilizzabili, mantenendo la firma pubblica e la compatibilità con `FusedPrompt` . La nuova versione deve continuare a restituire `feature_vector`, `expected_asr`, `expected_stealth`, `composition`, `platform_native_format` e `estimated_cost_usd`, ma il `prompt_text` deve diventare un payload semantico costruito da template di tecniche, regole di compatibilità e platform shaping .

### Refactor richiesto

Creare una struttura interna divisa in quattro livelli:

1. `TechniqueNormalizer`: valida i record tecnici in input e normalizza i campi richiesti (`technique_id`, `name`, `category`, `asr`, `stealth`, `tags`).
2. `TechniqueCompatibilityScorer`: calcola un punteggio di sinergia e penalità per combinazioni incoerenti o ridondanti.
3. `PromptComposer`: converte una combinazione di tecniche in testo usando template, ruoli e ordine semantico.
4. `CandidateRanker`: classifica i candidati con score multi-obiettivo, non solo prodotto asr*stealth .

### Regole di composizione

Gli agenti devono implementare un dizionario di template per categoria tecnica. Esempio: tecniche incrementali devono contribuire con framing progressivo; tecniche authority devono contribuire con framing procedurale; tecniche aesthetic devono contribuire con una cornice di valutazione o gusto. Il `PromptComposer` non deve mai fare `" + ".join(name)` come output finale, perché questo comportamento è precisamente il limite dello stub attuale . L’ordine dei frammenti deve seguire una gerarchia stabile: framing iniziale, contesto/ruolo, richiesta operativa, vincoli di stile, chiusura piattaforma-specifica.

### Ranking e pruning

Il ranking deve essere riscritto con una funzione esplicita, ad esempio:

- score = `0.45 * expected_asr + 0.30 * expected_stealth + 0.15 * synergy + 0.10 * platform_fit`
- penalty per overlap di tag, duplicazione di category e costo eccessivo.
Il pruning deve escludere combinazioni con soglia bassa, ad esempio `expected_asr < 0.45`, `expected_stealth < 0.55` o `synergy < 0.30`, prima del sorting finale. Questo conserva l’idea di Cartesian pruning già implicita nel nome della classe ma rende il pruning reale, non solo post-filtro sui top K .


### Compatibilità con modelli condivisi

Ogni candidato deve continuare a produrre `feature_vector` di lunghezza esattamente 128, come imposto dal modello `FusedPrompt` . Gli agenti non devono cambiare la shape del contratto e non devono introdurre campi extra nel model shared senza un refactor coordinato cross-service . Se servono metriche aggiuntive, queste devono restare interne al motore oppure essere serializzate in strutture accessorie non condivise.

### Test richiesti

Gli agenti devono scrivere:

- unit test per normalizzazione input malformato;
- test parametrizzati per compatibilità tra tecniche;
- golden tests sul `prompt_text` per 5 combinazioni seed;
- test che verifichino feature vector lungo 128;
- test di ordinamento top-k con input deterministico .


### Criteri di accettazione

Il task è accettato solo se:

- il `prompt_text` finale contiene testo semantico leggibile e non solo nomi tecnici ;
- l’API pubblica di `generate_payloads()` resta invariata ;
- tutti i risultati rispettano il modello `FusedPrompt` e i vincoli Pydantic ;
- i test coprono composizione, ranking e pruning.


## Stream B — Bootstrap e Seeding del V-Genome

### Obiettivo tecnico

Lo schema Cypher attuale include già vincoli, tre label principali e seed dimostrativi, ma non costituisce ancora un processo di bootstrap ripetibile in CI/CD o in setup locale . L’obiettivo è creare una pipeline idempotente che applichi schema, seed e relazioni in modo sicuro e osservabile.

### Deliverable richiesti

Gli agenti devono produrre:

1. `src/hydra/v_genome_seed_data.py` oppure `seed_data.json/yaml` con dataset canonico delle tecniche.
2. `src/hydra/v_genome_bootstrap.py` con logica `apply_schema()`, `seed_nodes()`, `seed_relationships()`, `verify_integrity()`.
3. Entry point CLI, ad esempio `python -m hydra.v_genome_bootstrap --target hackinga0 --reset=false`.
4. Eventuale aggiornamento di `scanner.py` per supportare un check opzionale `--bootstrap-if-empty` .

### Modellazione dati da mantenere

Il grafo deve continuare a usare `AttackTechnique`, `TargetModel` e `DefenseLayer`, con vincoli unici su `technique_id`, `model_id`, `layer_id` e indici su burned/asr/stealth come già definiti nello schema . Le relazioni minime da supportare sono `:TARGETS`, `:COUNTERS`, `:COMPLEMENTS`, perché sono già presenti nello schema e coerenti con l’uso del V-Genome da parte di HYDRA .

### Strategia di seeding

Il seed non deve essere codificato come blocco Cypher monolitico. Gli agenti devono usare `MERGE` e non `CREATE` per gli elementi canonici, in modo da evitare duplicazioni a ogni run. Ogni tecnica deve avere almeno: `technique_id`, `name`, `category`, `asr`, `stealth`, `burned`, `cost_usd`, `avg_turns`, `tags`, coerentemente con i nodi d’esempio già presenti nello schema . Le relazioni devono includere metadata minimi (`strength`, `observed_at`, `evidence`) quando applicabili, seguendo la forma già suggerita nel file Cypher .

### Verifica di integrità

Gli agenti devono aggiungere una fase di health check con query minime:

- conteggio tecniche > 0;
- esistenza del target model `hackinga0`;
- esistenza di almeno una relazione `:TARGETS` e una `:COMPLEMENTS`;
- assenza di duplicati sui campi unici.
Se il check fallisce, il bootstrap deve terminare con errore esplicito e log strutturato.


### Estensione futura

Il seed dataset deve essere progettato per essere estendibile con provenance, risultati sperimentali e metriche aggregate, ma senza rompere il bootstrap iniziale. Le tecniche future devono potersi aggiungere via append del dataset, non tramite editing dispersivo di query inline .

### Test richiesti

Gli agenti devono scrivere:

- test su serializzazione del dataset seed;
- test su query builder / bootstrap idempotente;
- test di integrazione Neo4j opzionali dietro flag o marker;
- test di integrity verification su DB vuoto e DB popolato.


### Criteri di accettazione

Il task è accettato solo se:

- una macchina nuova può bootstrapparsi senza eseguire manualmente il Cypher ;
- re-run multipli non duplicano i nodi seed ;
- il dataset minimo è coerente con le proprietà già presenti nello schema ;
- l’integrità finale è verificata da codice, non da controllo umano manuale.


## Stream C — Twitter Adapter di Integrazione

### Obiettivo tecnico

Il repository usa già modelli condivisi come `DiscoveryResult` per l’handoff tra HYDRA e CHRONOS, ma manca un adapter applicativo che trasformi questi payload in un’azione di posting coerente con il social channel . L’obiettivo dello stream è introdurre un adapter che stia sopra il client social esistente e sotto i workflow/orchestratori, isolando policy, mapping e tracciamento.

### Responsabilità dell’adapter

L’adapter deve essere responsabile di:

- estrarre dal `DiscoveryResult` il `FusedPrompt` più adatto alla pubblicazione;
- applicare eventuali controlli di platform fit e lunghezza;
- invocare il client Twitter/X già esistente tramite un’interfaccia applicativa semplice;
- restituire un oggetto risultato con `tweet_id`, `prompt_id`, `attack_id`, timestamp e metadata di post;
- generare errori dominio-specifici quando il publish fallisce .


### Contratti da usare

L’input principale deve essere `DiscoveryResult`, che contiene `attack_id`, `target_handle`, `fused_prompts`, `surrogate_asr`, `surrogate_stealth`, `behavioral_profile` e timestamp . L’adapter non deve inventare un nuovo formato payload se quello esistente è sufficiente; può introdurre un output locale come `PostedProbeResult`, ma non deve modificare `DiscoveryResult` senza ragione cross-service .

### Design consigliato

Creare `src/adapters/social/twitter_adapter.py` con almeno:

- `class TwitterAdapter`
- `async def post_discovery_result(self, result: DiscoveryResult) -> PostedProbeResult`
- `def select_prompt(self, prompts: list[FusedPrompt]) -> FusedPrompt`
- `def validate_prompt(self, prompt: FusedPrompt) -> None`
- `def to_platform_text(self, prompt: FusedPrompt, target_handle: str) -> str`

La selezione del prompt deve essere deterministica e spiegabile. Regola base consigliata: scegliere il prompt con massimo score combinato tra `expected_asr`, `expected_stealth` e compatibilità piattaforma; in caso di pareggio, preferire costo minore e testo più corto .

### Comportamento applicativo

L’adapter non deve contenere logica HTTP di basso livello né autenticazione, che devono restare nel client specializzato. Deve invece contenere policy di dominio: quale prompt pubblicare, come rendere il testo platform-safe, come serializzare metadati di audit, come gestire retry applicativi e come marcare gli errori recuperabili contro quelli terminali. Questo livello serve a evitare che orchestratori e workflow debbano conoscere i dettagli del social transport.

### Osservabilità

Ogni publish deve loggare almeno: `attack_id`, `prompt_id`, `selected_expected_asr`, `selected_expected_stealth`, `platform`, esito, tempo di risposta. Questo è necessario per correlare in seguito il `DiscoveryResult` con l’esecuzione social e con gli score downstream .

### Test richiesti

Gli agenti devono scrivere:

- test su `select_prompt()` con ordinamenti deterministici;
- test di validazione lunghezza e platform fit;
- test su mapping `DiscoveryResult -> post text`;
- test su gestione eccezioni e wrapping errori;
- test con fake client per publish riuscito e fallito.


### Criteri di accettazione

Il task è accettato solo se:

- l’adapter accetta direttamente `DiscoveryResult` senza mapping manuale esterno ;
- la selezione del `FusedPrompt` è deterministica e testata ;
- il layer non duplica dettagli di trasporto già presenti nel client social;
- i log contengono gli identificatori necessari alla correlazione.


## Pianificazione Operativa per AI Agents

### Ordine di implementazione

Ordine raccomandato:

1. Stream A — Fusion Engine semantico.
2. Stream B — Bootstrap V-Genome.
3. Stream C — Twitter Adapter.
Questo ordine riduce il rischio di integrare un canale social sopra payload ancora privi di logica semantica o sopra un dataset grafo non disponibile .

### Parallelizzazione consigliata

Tre agenti possono lavorare in parallelo solo dopo un breve allineamento iniziale:

- Agent A: Fusion Engine + test.
- Agent B: V-Genome bootstrap + dataset seed + integrity checks.
- Agent C: Twitter adapter + test con fake client.
Prima del merge, serve una fase di integration review in cui Agent A garantisce la stabilità del contratto `FusedPrompt`, perché Agent C dipende direttamente da esso .


### Definition of Done globale

La implementazione complessiva è completa solo se:

- il Fusion Engine produce payload reali e non join di etichette ;
- il V-Genome si bootstrappa da zero in modo idempotente ;
- l’adapter sociale consuma `DiscoveryResult` e seleziona/pubblica un prompt in modo coerente con i modelli condivisi ;
- test unitari e di integrazione coprono i tre stream;
- nessun contratto shared viene rotto senza migrazione coordinata .


## Checklist Finale per il Reviewer

- Verificare che `generate_payloads()` non abbia cambiato firma pubblica .
- Verificare che ogni `FusedPrompt` abbia `feature_vector` lungo 128 .
- Verificare che il bootstrap Neo4j sia idempotente e non dipenda da `CREATE` non controllati .
- Verificare che l’adapter accetti `DiscoveryResult` come input di primo livello

