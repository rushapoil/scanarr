FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# ── The dist/ folder is copied into the backend image at build time ──────────
# This stage is used as a source for the multi-stage backend Dockerfile.
FROM scratch AS export
COPY --from=builder /app/dist /dist
