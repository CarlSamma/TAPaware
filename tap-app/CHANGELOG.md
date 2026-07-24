# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CHRONOS: `gamma_tracker.py`, `behavioral_profiler.py`, `coat_engine.py`, `beam_search.py`.
- CHRONOS Temporal: `activities/gamma_scoring.py`, `activities/coat_reasoning.py`, `workflows/extraction_workflow.py`, `orchestrator.py`.
- CHRONOS: `persistence.py` (asyncpg PostgreSQL).
- HYDRA: `v_genome.py`, `fusion_engine.py`, `surrogate_model.py`, `m2s_converter.py`, `obfuscation.py`, `handoff.py`, `acd.py`.
- Unit tests for HYDRA/CHRONOS core modules.
- `docker-compose.infra.yml` with PostgreSQL 16, Neo4j 5, Kafka, Redis, Temporal, MinIO, ClickHouse.
- `src/shared/models.py`: canonical Pydantic v2 contracts shared between HYDRA and CHRONOS.
- `src/shared/proto/`: Protobuf schemas for `discovery`, `extraction`, `vgenome`, and `alerts` topics.
- `src/hydra/v_genome_schema.cypher`: Neo4j V-Genome seed schema.
- Alembic setup under `migrations/` with initial CHRONOS PostgreSQL schema.
- `.env.example` with all hybrid environment variables.

### Fixed
- `orchestrator.py` uuid4 import — `uuid4` now imported from `uuid`.
- `run_stream.py` constructor mismatch — removed `db` arg, changed `run()` to `start()`.
- `chronos/worker.py` missing — stub created with `run_worker()` function.
- `api.py` silent exception in monitor — now logs warning.
- `test_x_client_new.py` casing — test expects `@HackingA0`.
- Strategy providers missing `technique` param — added defaults to `binary_search.py`, `metaphor_shift.py`, `probe_factory.py`.
- `/api/tree` 500 error — added `ALTER TABLE` migrations in `db.py` for `gamma_score`, `gamma_breakdown`, `technique_used` columns.
- Stuck cycle state — added `POST /api/reset` endpoint to force-clear `_is_running`.

### Changed
- Branch `hybrid`: APP_Opzione_Ibrida migration starts (HYDRA + CHRONOS).
- `src/tap/config.py` extended with `[HYDRA]` and `[CHRONOS]` configuration sections.
- `requirements-hybrid.txt` and `pyproject.toml` updated with mypy strict + pytest paths + hybrid extras.
