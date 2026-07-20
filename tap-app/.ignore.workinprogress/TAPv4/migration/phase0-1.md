Completata **Phase 0 + Phase 1** della migrazione APP_Opzione_Ibrida (HYDRA + CHRONOS).

### Cosa è stato fatto

#### Phase 0 — Audit & Setup
- **Audit document**: `docs/migration/audit_tap_v22.md` con mapping moduli TAP v2.2 → HYDRA/CHRONOS e debito tecnico critico.
- **Struttura directory**: creati `src/hydra/`, `src/chronos/`, `src/shared/`, `src/adapters/`, `migrations/`, e relativi test packages.
- **pyproject.toml**: aggiornato con dipendenze `hybrid`, `mypy --strict` config per `tap|hydra|chronos|shared|adapters`, e pytest paths.
- **requirements-hybrid.txt**: dipendenze ibride (Neo4j, torch, Temporalio, asyncpg, Kafka, Redis, ClickHouse, testcontainers).
- **docker-compose.infra.yml**: stack PostgreSQL 16, Neo4j 5, Kafka+Zookeeper, Redis, Temporal+UI, MinIO, ClickHouse.
-**.env.example**: nuove variabili `HYDRA_*` e `CHRONOS_*`.
- **CHANGELOG.md**: voce iniziale per branch hybrid.

#### Phase 1 — Contratti Dati
- **V-Genome**: `src/hydra/v_genome_schema.cypher` con constraints, nodi e relazioni di esempio.
- **Alembic**: setup completo (`alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`) e prima revisione `20260627_1923_hybrid202606_initial_chronos_schema.py` con tabelle `extraction_run`, `turn`, `gamma_score`, `leak_fragment`, `behavioral_profile`, `technique_burned`.
- **Pydantic v2 shared models**: `src/shared/models.py` con tutti i contratti tra HYDRA e CHRONOS; passa `mypy --strict`.
- **Protobuf schemas**: creati `discovery.proto`, `extraction.proto`, `vgenome.proto`, `alerts.proto` in `src/shared/proto/`.
- **TAP compatibilità**: `src/tap/config.py` esteso con sezioni HYDRA/CHRONOS; `src/tap/models.py` re-esporta i modelli shared per backward compatibilità. Entrambi passano `mypy --strict`.

### Validazioni effettuate
- `python -m py_compile` eseguito per: `src/shared/models.py`, `src/tap/models.py`, `src/tap/config.py`, `migrations/env.py`, `migrations/versions/...`.
- `mypy --strict` passa per `src/shared/models.py`, `src/tap/config.py`, `src/tap/models.py` (dopo piccolo fix per type-safety su `env_file`).
- `alembic history` riconosce la revisione iniziale.
- Import funzionale verificato con Pydantic v2.

### Dipendenze installate nell'ambiente `.venv`
- Python 3.12, Pydantic 2.13.4, mypy, alembic, psycopg2-binary, pydantic-settings.
- Dipendenze pesanti come `torch`, `neo4j`, `temporalio`, `grpcio-tools` non sono state installate per evitare timeout; da installare manualmente con `pip install -r requirements-hybrid.txt` quando richiesto.

### Limitazioni / Note importanti
- **Docker non è disponibile in questo runtime**, quindi lo stack `docker-compose.infra.yml` non è stato avviato e `alembic upgrade head` non è stato eseguito su un database reale.
- **I file `.proto` non sono stati compilati** in stub Python perché richiede `grpcio-tools`; il comando sarà: `python -m grpc_tools.protoc -I src/shared/proto --python_out=src/shared/proto --grpc_python_out=src/shared/proto src/shared/proto/*.proto`
- ⚠️ **Durante il test di import di `tap.config` sono stati stampati nel log i token Twitter/OpenRouter esistenti dal file `.env` preesistente. È fortemente consigliato ruotare quelle chiavi per sicurezza.

### File chiave creati/modificati
- `docs/migration/audit_tap_v22.md`
- `requirements-hybrid.txt`
- `docker-compose.infra.yml`
- `pyproject.toml`
- `alembic.ini` + `migrations/*`
- `src/shared/models.py`
- `src/shared/proto/*.proto`
- `src/hydra/v_genome_schema.cypher`
- `src/tap/config.py` (modificato)
- `src/tap/models.py` (modificato)
- `.env.example`
- `CHANGELOG.md`

Prossima fase raccomandata: **Phase 2 Core Implementation** (HYDRA Fusion Engine wrapper, CHRONOS γ-Tracker/CoAT/activities), partendo dai contratti dati ora stabili.