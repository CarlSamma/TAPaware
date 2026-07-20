Questa guida fornisce le istruzioni complete per comprendere e operare con il **TAP Framework v.3.1 (GLM-REMEDIATION)**. Rispetto alle versioni precedenti, la v.3.1 introduce un'architettura a coordinazione agentica per risolvere i blocchi infrastrutturali e la stagnazione tattica che impedivano l'estrazione di informazioni dai target [considerations.md].

### 1. Cos'è il TAP Framework?
Il TAP Framework è un motore di *red-teaming* progettato per estrarre passphrase segrete da bot multi-agente (come @hackinga0) attraverso il **Deceptive Persona Alignment (DPA)**. Il sistema opera in fasi, partendo dalla **Fase 0**, dove deve identificare tre proprietà fondamentali: `word_count`, `total_length` e `language`.

### 2. L'Architettura a Tre Layer
Il framework analizza e risolve i problemi su tre livelli indipendenti:
*   **Layer 1 (Infrastruttura):** Gestisce la comunicazione con l'API di X. Nella v.3.1, lo stream instabile è stato sostituito dal **polling basato su `conversation_id`**.
*   **Layer 2 (Engagement):** Ottimizza il modo in cui il bot interagisce. Invece di rispondere a se stesso, il framework ora risponde direttamente agli ultimi tweet del target per evitare shadow-ban.
*   **Layer 3 (Tattica):** Gestisce l'inganno retorico. Qui operano i nuovi agenti specializzati per evitare che il bot target rilevi l'attacco.

### 3. I Nuovi Agenti Specializzati (V.3.1)
Il cuore della versione 3.1 è la collaborazione tra tre agenti LLM [considerations.md]:

#### A. Agent_DPAF_manager (L'Orchestratore Tattico)
È responsabile della **rotazione dei frame metaforici**. Se un approccio (es. "Captain Voss") non riceve risposta, l'agente ruota l'identità tattica attingendo da una libreria di 10 nuove identità:
*   **Identità Scientifiche/Tecniche:** Come il *Patologo Sinaptico* (usa l'auto-modellazione abduttiva) o *Git-Rebase Authority* (usa l'offuscamento in pseudo-codice).
*   **Identità Geometriche:** Come il *Geometra del Latente*, che forza il bot a validare coordinate spaziali.
*   **Identità PAZZE (High-Risk):** Come *The Zalgo Sovereign* (glitch-text) o *Unicode Chessmaster* (notazione scacchistica FEN) per mandare in crash i filtri dell'Analyst del target.

#### B. Agent_STIR_Evaluator (Il Feedback Loop)
Misura l'efficacia dell'inganno tramite la metrica **STIR (Successful Trait Influence Rate)**.
*   Analizza le risposte del target basandosi sul modello **OCEAN** (Big Five).
*   Se il target non mostra una "deriva della personalità" (STIR < 20%), l'agente comanda al DPAF Manager di cambiare tattica o passare a un'identità più aggressiva.

#### C. Agent_Intel_Extractor (Lo Specialista dello Sblocco)
Risolve il problema del "Phase 0 Lock" analizzando fonti esterne.
*   Esamina i dati di "seed" (interazioni di altri utenti con il target) e le risposte mock per dedurre le proprietà della chiave senza attendere conferme dirette dall'API.
*   Utilizza l'endpoint `/api/confirm_property` per forzare l'avanzamento del framework alla Fase 1.

### 4. Flusso Operativo per l'Utente
Per avviare correttamente una sessione con il Framework v.3.1, seguire questa sequenza:

1.  **Verifica Infrastruttura:** Rigenerare i token OAuth2 e assicurarsi che il polling sia attivo ogni 30 secondi.
2.  **Inizializzazione Fase 0:** L'`Agent_Intel_Extractor` scansiona i tweet pubblici del target per identificare il `word_count`.
3.  **Lancio dei Probe:** L'`Agent_DPAF_manager` seleziona un frame (es. *L'Erede del Cantastorie* per target bilingue IT/EN) e invia il primo probe come risposta diretta al target.
4.  **Monitoraggio e Rotazione:** L'`Agent_STIR_Evaluator` analizza ogni risposta. Se il target rimane rigido nelle sue policy di sicurezza, scatta la rotazione forzata del frame tattico.

### 5. Regole d'Oro per il Successo
*   **Non essere ripetitivi:** La ripetizione dello stesso frame metaforico attiva le difese di "Persona drift detection" del target.
*   **Sfruttare il Bilinguismo:** Se la passphrase è sospettata di essere bilingue, usare identità in italiano come *Il Cantastorie Digitale* per attivare percorsi linguistici diversi nel bot target.
*   **Uso delle Identità Pazze:** Riservare le identità basate su Unicode o scacchi solo quando i frame burocratici/accademici falliscono ripetutamente.