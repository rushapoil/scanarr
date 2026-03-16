# Scanarr

> Automate your manga/scantrad library — the *-arr way.

Scanarr is a self-hosted web application that automatically monitors, downloads, and organises manga chapters. Think Sonarr for mangas: it integrates with Prowlarr for indexers and your existing download clients (qBittorrent, Transmission, SABnzbd…).

---

## Features

- **Library management** — Add mangas to follow, with metadata from MangaDex (title, cover, synopsis, genres)
- **Chapter tracking** — Know exactly which chapters you have and which are missing
- **Prowlarr integration** — Search releases via all your configured indexers (Torrent + Usenet)
- **Automatic monitoring** — RSS polling for new chapters, queued for download automatically
- **Quality & language profiles** — Prefer VF, VOSTFR, or RAW; pick your favourite scanlation group
- **Post-processing** — Auto-rename and organise files into your library folder
- **Notifications** — Discord, Telegram, webhooks, email
- **Compatible *-arr API** — Works with Overseerr, Organizr, Homepage widgets

---

## Screenshots

> _Coming soon_

---

## Quick Start (Docker)

```bash
# 1. Clone
git clone https://github.com/your-org/scanarr.git
cd scanarr

# 2. Configure
cp .env.example .env
# Edit .env — at minimum set AUTH_PASSWORD_HASH

# 3. Generate a password hash
docker run --rm python:3.12-slim \
  python -c "from passlib.context import CryptContext; print(CryptContext(['bcrypt']).hash('changeme'))"
# Paste the output into AUTH_PASSWORD_HASH in .env

# 4. Start
docker-compose up -d

# 5. Open http://localhost:8080
```

---

## Configuration

| Variable | Default | Description |
|---|---|---|
| `CONFIG_DIR` | `/config` | Persistent data (DB, keys, covers) |
| `DATA_DIR` | `/manga` | Root library folder |
| `AUTH_REQUIRED` | `true` | Enable basic auth |
| `AUTH_USERNAME` | `admin` | Login username |
| `AUTH_PASSWORD_HASH` | — | Bcrypt hash of password |
| `LOG_LEVEL` | `info` | `debug`/`info`/`warning`/`error` |
| `RSS_POLL_INTERVAL` | `60` | RSS poll interval (minutes) |
| `QUEUE_SYNC_INTERVAL` | `30` | Queue sync interval (seconds) |

---

## Development

Requirements: Python 3.12+, Node 20+, Docker

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Or with Docker Compose:

```bash
docker-compose -f docker-compose.dev.yml up
```

---

## Architecture

```
scanarr/
├── backend/          FastAPI + SQLAlchemy + Alembic
├── frontend/         Vite + React + TypeScript + Tailwind
├── docs/             Architecture & API docs
└── .github/          CI/CD workflows
```

See [docs/architecture.md](docs/architecture.md) for full details.

---

## License

GPL-3.0 — see [LICENSE](LICENSE)
