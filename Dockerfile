# ── Stage 1: Build frontend ───────────────────────────────────────────────────
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --prefer-offline
COPY frontend/ ./
RUN npm run build

# ── Stage 2: Install Python deps (separate layer for cache) ───────────────────
FROM python:3.12-slim AS python-deps

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Stage 3: Runtime image ────────────────────────────────────────────────────
FROM python:3.12-slim

# curl for HEALTHCHECK
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python packages
COPY --from=python-deps /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=python-deps /usr/local/bin /usr/local/bin

# Backend application
COPY backend/ ./

# Compiled frontend (served as static files by FastAPI)
COPY --from=frontend-builder /frontend/dist ./frontend/dist

RUN chmod +x ./entrypoint.sh

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CONFIG_DIR=/config \
    DATA_DIR=/manga \
    PORT=8080

VOLUME ["/config", "/manga"]
EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -sf "http://localhost:${PORT}/api/v1/system/health" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
