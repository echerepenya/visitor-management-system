# Visitor Management System (VMS) 🏢

A full-stack access management system for residential complexes. It includes a FastAPI backend, a Vue 3 dashboard for security personnel, and an Aiogram 3 Telegram bot for resident notifications and approvals.

## 🚀 Production Deployment

The project is fully containerized and ready for production via Docker Compose.

### 1. Prerequisites
This setup assumes you are using a reverse proxy (e.g., **Nginx Proxy Manager**, Traefik, or Nginx) to handle SSL and routing. The configuration expects an external network named `proxy_net`.

Create the network if it doesn't exist:
```bash
docker network create proxy_net
```

### 2. Configure Environment Variables
Copy the template and fill in your actual values:
```bash
cp .env.example .env
nano .env
```
*Key required fields: `BOT_TOKEN`, `DB_PASSWORD`, and `VITE_API_URL`.*

### 3. Launch
```bash
docker compose up -d --build
```
Once started, the `backend` and `frontend` services will be available within the `proxy_net`. Configure your Proxy Manager to route traffic to:
- **Frontend:** container `vms-frontend`, port `80`
- **Backend:** container `vms-backend`, port `8000`

---

## 🛠 Local Development

To run the project locally with hot-reload enabled, use the development compose file:
```bash
docker compose -f docker-compose.dev.yml up --build
```

- **Backend API:** [http://localhost:8000](http://localhost:8000)
- **Admin Panel:** [http://localhost:8000/admin](http://localhost:8000/admin)
- **Frontend:** [http://localhost:80](http://localhost:80)

---

## 📋 Core Environment Variables

| Variable | Description |
| :--- | :--- |
| `BOT_TOKEN` | Telegram Bot token from @BotFather |
| `SUPERUSER_PASSWORD` | Password for the SQLAdmin dashboard |
| `VITE_API_URL` | Public API URL (required for the frontend to communicate with the backend) |
| `DB_PASSWORD` | PostgreSQL database password |
| `REDIS_URL` | Redis connection string (defaults to `redis://redis:6379/0`) |

---

## 💾 Database Backups

The project includes a `db_backup.sh` script that creates compressed PostgreSQL dumps and uploads them to Google Drive via **rclone**.

**Setup:**
1. Configure `rclone` (the remote must be named `gdrive`).
2. Add the script to your crontab:
```bash
0 3 * * * /path/to/project/db_backup.sh
```

---

## 🏗 Project Structure

- `backend/` — FastAPI application, SQLAlchemy, SQLAdmin.
- `frontend/` — Vue 3 + Vite (Guard Dashboard).
- `telegram-bot/` — Aiogram 3 bot for resident notifications.
- `docker-compose.yml` — Primary production configuration.
