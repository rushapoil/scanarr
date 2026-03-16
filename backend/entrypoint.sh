#!/bin/sh
set -e

# Ensure persistent directories exist
mkdir -p "${CONFIG_DIR:-/config}"
mkdir -p "${DATA_DIR:-/manga}"

echo "[Scanarr] Running database migrations..."
alembic upgrade head

echo "[Scanarr] Starting server on port ${PORT:-8080}..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8080}" \
    --workers 1 \
    --log-level "${LOG_LEVEL:-info}"
