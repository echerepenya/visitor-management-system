**Visitor Management System**

The system for managing visitor access to a residential complex. It includes a **FastAPI** backend (REST API + admin panel) and a **Telegram bot** for notifications and interactions (e.g. visitor requests, guard approvals, alerts).

### Tech Stack

- **Backend** — Python 3.12, **FastAPI**, Uvicorn, SQLAlchemy 2 + asyncpg, Alembic (migrations), SQLAdmin (admin interface), Pydantic Settings, Passlib (bcrypt)
- **Telegram Bot** — Python + **Aiogram 3**
- **Database** — PostgreSQL 15
- **Deployment** — Docker + Docker Compose

### Quick Start (Development)

1. Clone the repo  
   ```bash
   git clone https://github.com/echerepenya/visitor-management-system.git
   cd visitor-management-system
   ```

2. Environment variables  
   ```bash
   cp .env.example .env
   ```
   Fill in at least:
   - `BOT_TOKEN` (from @BotFather)
   - `SECRET_KEY` (generate a strong random string)
   - `SUPERUSER_PASSWORD`
   - `LIVING_COMPLEX_NAME` and `GUARD_CONTACT_PHONE` (optional but recommended)
   - Database credentials (defaults are fine for dev)

3. Run in development mode (hot-reload + exposed ports)  
   ```bash
   docker compose -f docker-compose.dev.yml up --build
   ```

   - Backend → http://localhost:8000  
   - Admin panel → http://localhost:8000/admin  
   - Database → localhost:5432 (for tools like pgAdmin)

### Production Deployment

1. Prepare `.env` (use strong secrets, never commit it).

2. Create the external proxy network (if you use Traefik, Nginx Proxy Manager, etc.):  
   ```bash
   docker network create proxy_net
   ```

3. Start production services  
   ```bash
   docker compose up -d --build
   ```

   Services run on the internal + `proxy_net` networks (no ports exposed to the host).  
   The backend is ready to be routed through your reverse proxy.

**Database backups** (production)  
The included `db_backup.sh` script creates daily compressed dumps and uploads them to Google Drive via **rclone**.  
Configure rclone and add the script to cron (example: `0 3 * * * /path/to/db_backup.sh`).

### Project is Open for Contributions

We welcome bug fixes, new features, documentation, translations, and improvements!

**Correct way to contribute:**

1. **Fork** the repository.
2. Create a feature branch from `master`:
   ```bash
   git checkout -b feature/your-awesome-feature
   ```
3. Make your changes (keep them focused and clean).
4. Commit with a clear message.
5. Push the branch to your fork.
6. Open a **Pull Request** to the `master` branch of the original repo.

Please follow PEP 8 style and add a short description of your changes in the PR.

---

Thank you for using/contributing to the project!  
Any questions or ideas — open an issue or contact me directly.
