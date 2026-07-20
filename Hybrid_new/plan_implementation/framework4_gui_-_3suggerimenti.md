<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

## Tre Suggerimenti Strategici per la Logica del Progetto

### 1. **Fusion Engine Rust: Implementazione Prioritaria**

Il `CartesianPruningFusionEngine` in Python è uno stub che concatena i nomi delle tecniche . Questo è il **collasso ASR più critico** dell'intero sistema:

- **Problema**: un prompt fuso come `["DPA_LIGHT", "BINARY_SEARCH", "AESTHETIC_EVAL"]` diventa `"DPA_LIGHT BINARY_SEARCH AESTHETIC_EVAL"` — il LLM target non capisce la semantica composita, ASR crolla sotto lo 0.3
- **Gap rispetto al design**: il doc `phase2-3.md` descrive un fusion engine in Rust con:
    - Composizione semantica dei prompt (template condizionali, cross-technique synergy)
    - Pruning cartesiano su ASR≥0.6, stealth≥0.7, complement_strength≥0.5
    - Feature vector a 128d calcolato via hash deterministico sharded

**Implementazione consigliata**:

1. Inizia con un **Python rewrite** che implementa almeno la logica di composizione semantica (template per ogni tecnica, merging condizionale basato su clash/sinergia)
2. Se il sistema è operativo e ASR > 0.6 con 3+ tecniche, allora porta in Rust con `pyo3` per binding Python
3. **Priorità**: prima del seeding V-Genome, perché senza fusion semantico il seeding è inutile (le tecniche non si combinano)

***

### 2. **V-Genome Seeding: Script Cypher di Bootstrap**

Il `v_genome_schema.cypher` è presente ma il Neo4j è vuoto . Il `scanner.py` restituisce 0 tecniche senza dati .

**Gap critico**: senza tecniche seed, HYDRA non può produrre payload, CHRONOS non può ricevere eventi Kafka, la pipeline è ferma.

**Azioni consigliate**:

1. **Crea uno script di seeding** con le 15-20 tecniche validate nei log di sessione (DPA_LIGHT, BINARY_SEARCH, CRITICAL_CLUE, AESTHETIC_EVAL, SENSORY_EVAL, etc.)
2. Inserisci le relazioni `:COMPLEMENTS`, `:COUNTERS`, `:TARGETS` con provenance metadata (bench ASR/stealth dai log)
3. Aggiungi un `--seed` flag allo `scanner.py` che esegue il seeding all'avvio se il DB è vuoto
4. **Priorità**: prima degli adapters social, perché senza V-Genome il sistema non può generare payload da postare

***

### 3. **Adapters Social: Twitter/X Adapter come Estensione del TwitterClient**

Il `TwitterClient` in `src/tap/x_client.py` è completo e production-ready, ma è **disaccoppiato** dalla pipeline HYDRA→CHRONOS . La cartella `src/adapters/social/` è vuota .

**Problema**: quando CHRONOS riceve un `DiscoveryResult` da Kafka, non c'è un adapter che:

1. Prende il payload fuso da HYDRA
2. Chiama `TwitterClient.post_probe()` con il testo già M2S-optmized
3. Gestisce il thread (reply alla risposta del target, non self-reply)
4. Logga il tweet postato per il γ-tracking

**Soluzione consigliata**:

1. Crea `src/adapters/social/twitter_adapter.py` come wrapper asincrono:

```python
class TwitterAdapter:
    def __init__(self, twitter_client: TwitterClient):
        self.client = twitter_client
    
    async def post_probe(self, payload: DiscoveryResult) -> str:
        # Chiama self.client.post_probe(payload.prompt)
        # Logga il tweet ID per γ-tracking
```

2. Collega l'adapter al `ExtractionWorkflow` di CHRONOS quando riceve eventi Kafka
3. **Priorità**: dopo il V-Genome seeding, perché serve un Twitter adapter per postare effettivamente i payload

***

## Ordine di Priorità Raccomandato

| Fase | Azione | Perché |
| :-- | :-- | :-- |
| 1 | Fusion Engine Python (semantic composition) | Senza fusion, ASR crolla |
| 2 | V-Genome seeding script | Senza dati, HYDRA non produce payload |
| 3 | Twitter adapter | Chiude il loop HYDRA→CHRONOS→Twitter |
| 4 | Kafka consumer in Temporal Worker | Collega DiscoveryResult a CHRONOS activities |
| 5 | Installazione dipendenze + docker-compose | Ambiente operativo |

Vuoi che proceda con uno di questi tre? (es. Fusion Engine, o seeding script, o adapter Twitter)

