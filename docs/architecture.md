# Scanarr — Architecture

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│  Browser / Mobile                                           │
│  React + TypeScript (Vite, Tailwind, TanStack Query)        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP  /api/v1/*
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI  (Python 3.12)                                     │
│  ├── /manga          CRUD + search trigger                  │
│  ├── /chapter        per-chapter monitoring/search          │
│  ├── /queue          download queue                         │
│  ├── /history        event log                              │
│  ├── /calendar       upcoming releases                      │
│  ├── /settings       Prowlarr, clients, profiles            │
│  └── /system         status, tasks, disk space             │
└───────┬──────────────────────────────────────┬──────────────┘
        │ SQLAlchemy (async)                   │ httpx
┌───────▼──────────┐              ┌────────────▼────────────┐
│  SQLite           │              │  External APIs          │
│  /config/         │              │  ┌─ MangaDex (metadata)│
│  scanarr.db       │              │  ├─ Prowlarr (search)  │
│  (Alembic)        │              │  └─ Download clients   │
└──────────────────┘              └─────────────────────────┘
```

## Key Design Decisions

### Authentication
- HTTP Basic Auth for all endpoints (username + bcrypt-hashed password)
- X-Api-Key header as alternative (stored plaintext in app_config — it's an access token, not a secret)
- Both auth methods can be disabled via `AUTH_REQUIRED=false`

### Secret Storage
- Download client passwords, Prowlarr API keys → Fernet-encrypted in SQLite
- Fernet key → `/config/secret.key` (chmod 600, never in DB or env)
- User password → bcrypt hash in `.env` / `AUTH_PASSWORD_HASH`

### Database
- SQLite + aiosqlite for async I/O
- Alembic for versioned migrations (`alembic upgrade head` on container start)
- `render_as_batch=True` for SQLite ALTER TABLE support

### Background Jobs (APScheduler)
| Job | Interval | Purpose |
|---|---|---|
| RSS Monitor | 60 min | Poll indexers, grab new releases |
| Queue Sync | 30 sec | Update download progress |
| Metadata Refresh | 24 h | Refresh manga info from MangaDex |

### Quality Matching
Releases are scored against the QualityProfile and LanguageProfile assigned to each manga. The best matching release above the "cutoff" quality is grabbed automatically.

## File Layout

```
/config/
  scanarr.db        SQLite database
  secret.key        Fernet encryption key (600)
  covers/           Cached cover images
  logs/
    scanarr.log     Rotating JSON log (10 MB × 5)

/manga/
  {Manga Title}/
    {Manga Title} - Chapitre 001 - {Chapter Title}.cbz
```
