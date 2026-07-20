# ==============================================================================
# Multi-stage Dockerfile per APP_Opzione_Ibrida
# Targets: base | hydra | tap | adapters | chronos
#
# PYTHONPATH=/app/src  ->  consente import diretti:
#   from tap.config import Settings
#   from hydra.v_genome import VGenome
# ==============================================================================

# ------------------------------------------------------------------------------
# BASE
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Installa requirements (prima requirements.txt se esiste, poi hybrid)
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt 2>/dev/null || true
RUN pip install --no-cache-dir -r requirements-hybrid.txt

# Copia sorgenti, entrypoints e scripts
COPY src/ ./src/
COPY entrypoints/ ./entrypoints/
COPY scripts/ ./scripts/

# CRITICO: /app/src nel PYTHONPATH per import diretti tipo 'from tap.config import ...'
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# ------------------------------------------------------------------------------
# HYDRA-API  (src/tap/api.py)
# http://localhost:8000/docs
# ------------------------------------------------------------------------------
FROM base AS hydra
EXPOSE 8000
CMD ["uvicorn", "tap.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

# ------------------------------------------------------------------------------
# TAP ENGINE  (entrypoints/run_engine.py)
# Loop HITL-driven: si avvia, si connette a DB/Neo4j e aspetta trigger API
# ------------------------------------------------------------------------------
FROM base AS tap
CMD ["python", "/app/entrypoints/run_engine.py"]

# ------------------------------------------------------------------------------
# ADAPTERS / Stream Listener  (entrypoints/run_stream.py)
# Ascolta reply X/Twitter a @HackingA0
# ------------------------------------------------------------------------------
FROM base AS adapters
CMD ["python", "/app/entrypoints/run_stream.py"]

# ------------------------------------------------------------------------------
# CHRONOS Worker  (entrypoints/run_chronos.py)
# Temporal worker — idle-loop se src/chronos/worker.py non ancora implementato
# ------------------------------------------------------------------------------
FROM base AS chronos
CMD ["python", "/app/entrypoints/run_chronos.py"]
