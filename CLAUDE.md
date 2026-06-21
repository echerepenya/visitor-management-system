# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Visitor Management System (VMS) — a residential complex access management platform. Three services:
- **backend/** — FastAPI REST API + SQLAdmin + WebSocket server
- **frontend/** — Vue 3 SPA served by Nginx (guard dashboard + Telegram mini app)
- **telegram-bot/** — Aiogram 3 bot (resident-facing interface + notifications)

## Running the Stack

**Development (hot-reload, ports exposed):**
```bash
docker compose -f docker-compose.dev.yml up --build
# Backend API + admin: http://localhost:8000
# Frontend:            http://localhost:80
# PostgreSQL:          localhost:5432
```

**Production:**
```bash
docker network create proxy_net   # only once
docker compose up -d --build
# Reverse proxy routes frontend (80) and backend (8000) via proxy_net
```

**Environment setup:**
```bash
cp .env.example .env   # fill in DB_USER, DB_PASSWORD, BOT_TOKEN, SECRET_KEY, API_KEY, etc.
```

## Database Migrations

Alembic migrations run automatically on container startup (`entrypoint.sh`). For manual use:
```bash
# Inside backend container or with backend venv active
alembic upgrade head
alembic revision --autogenerate -m "description"
```

## Architecture & Key Patterns

### Service Communication

- **Frontend → Backend**: Axios over HTTP (`VITE_API_URL`), WebSocket at `/ws/notifications`
- **Bot → Backend**: HTTP with static `X-API-Key` header (from `API_KEY` env var)
- **Backend → Bot**: Redis stream `vms_stream` — bot polls via `stream_listener.py`

### Authentication Flows

1. **Guards** (dashboard): username/password → JWT (`Authorization: Bearer`)
2. **Residents** (Telegram mini app): Telegram `initData` HMAC-SHA256 verified in `security.py` → JWT
3. **Bot API calls**: Static `X-API-Key` header

### Guest Request Lifecycle

```
Resident creates request (bot) → NEW
  → Guard sees in dashboard (WebSocket push)
  → Guard marks complete → COMPLETED
    → Backend publishes to Redis stream → Bot notifies resident
  OR scheduler marks stale → EXPIRED (runs every 1 minute via APScheduler)
```

### Admin Panel

SQLAdmin at `/admin`, protected by the same authentication backend. Default superuser: `sadmin` / value of `SUPERUSER_PASSWORD` env var. Created automatically on startup if missing.

### Key Backend Files

| File | Role |
|------|------|
| `backend/src/main.py` | App init, middleware, routers, admin views registration, superuser creation |
| `backend/src/database.py` | SQLAlchemy async engine, Redis client, `DbSessionMiddleware` |
| `backend/src/config.py` | Pydantic `BaseSettings` — all env vars |
| `backend/src/security.py` | JWT creation/verification, bcrypt hashing, Telegram `initData` verification |
| `backend/src/scheduler.py` | APScheduler — `check_expired_requests()` every 60s |
| `backend/src/services/websocket_manager.py` | Broadcast to all connected guard dashboards |
| `telegram-bot/src/services/stream_listener.py` | Reads `vms_stream` Redis stream, dispatches bot notifications |

## Tech Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), asyncpg, Alembic, SQLAdmin, APScheduler, python-jose, passlib/bcrypt
- **Frontend**: Vue 3, Vite, Pinia, Vue Router, Axios, Tailwind CSS 4
- **Bot**: Python 3.12, Aiogram 3, Redis FSM storage, httpx
- **Infra**: PostgreSQL 15, Redis 7, Docker Compose, Nginx (frontend)

## Database Schema Summary

- `users` — residents and guards; residents link to `apartments`; guards have `username`/`hashed_password`
- `apartments` → `buildings` (many-to-one)
- `guest_requests` — type enum: `guest_car`, `taxi`, `delivery`, `guest_foot`; status: `new`, `completed`, `expired`
- `cars` — resident vehicles (license plate)
- `audit_log`, `user_activity_log` — audit trail

## Backup

`db_backup.sh` dumps PostgreSQL → gzip → uploads via rclone to Google Drive. Run via cron; prunes local copies older than 7 days and remote copies older than 30 days.
