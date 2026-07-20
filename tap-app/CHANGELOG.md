# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (Phase 2 — Core Implementation)
- CHRONOS: `gamma_tracker.py`, `behavioral_profiler.py`, `coat_engine.py`, `beam_search.py`.
- CHRONOS Temporal: `activities/gamma_scoring.py`, `activities/coat_reasoning.py`, `workflows/extraction_workflow.py`, `orchestrator.py`.
- CHRONOS: `persistence.py` (asyncpg PostgreSQL).
- HYDRA: `v_genome.py`, `fusion_engine.py`, `surrogate_model.py`, `m2s_converter.py`, `obfuscation.py`, `handoff.py`, `acd.py`.
- Unit tests for HYDRA/CHRONOS core modules.

### Added (Phase 0 + Phase 1 — Audit & Contracts)
- Branch `hybrid`: APP_Opzione_Ibrida migration starts (HYDRA + CHRONOS).
- `docker-compose.infra.yml` with PostgreSQL 16, Neo4j 5, Kafka, Redis, Temporal, MinIO, ClickHouse.
- `src/shared/models.py`: canonical Pydantic v2 contracts shared between HYDRA and CHRONOS.
- `src/shared/proto/`: Protobuf schemas for `discovery`, `extraction`, `vgenome`, and `alerts` topics.
- `src/hydra/v_genome_schema.cypher`: Neo4j V-Genome seed schema.
- Alembic setup under `migrations/` with initial CHRONOS PostgreSQL schema.
- `src/tap/config.py` extended with `[HYDRA]` and `[CHRONOS]` configuration sections.
- `.env.example` with all new hybrid environment variables.
- `requirements-hybrid.txt` and `pyproject.toml` updated with mypy strict + pytest paths + hybrid extras.
- `docs/migration/audit_tap_v22.md`: audit of TAP v2.2 modules and migration targets.
