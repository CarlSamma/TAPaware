#!/bin/bash
# Create the 'hydra' database for HYDRA subsystem
# Called by postgres docker-entrypoint-initdb.d on first startup
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE hydra;
    GRANT ALL PRIVILEGES ON DATABASE hydra TO $POSTGRES_USER;
EOSQL
