# AquaNexis — Production Deployment Runbook

This runbook documents containerized deployment and production configuration with PostgreSQL and TimescaleDB.

---

## 1. System Architecture

```text
[ Client Browser / ESP32 Edge Devices ]
                   │
                   ▼ (HTTP/REST & WebSocket)
             [ NGINX Proxy ]
             (Port 80 / 443)
             ┌─────┴─────┐
             ▼           ▼
      [ Frontend ]  [ FastAPI Backend ]
      (Port 3000)   (Port 8000)
                         │
                         ▼ (SQLAlchemy / asyncpg)
              [ TimescaleDB (PostgreSQL 16) ]
                         │
                         ▼
                [ Persistent Volume ]
```

---

## 2. Docker Compose Deployment

### Step 1: Clone & Configure Environment
```bash
git clone https://github.com/aquanexis/aquanexis.git
cd aquanexis

# Copy example environment configuration
cp .env.example .env
```

Ensure production secrets in `.env`:
```ini
APP_ENV=production
DEMO_MODE=false
POSTGRES_USER=aquanexis
POSTGRES_PASSWORD=<SECURE_DATABASE_PASSWORD>
POSTGRES_DB=aquanexis
DATABASE_URL=postgresql+asyncpg://aquanexis:<SECURE_DATABASE_PASSWORD>@timescaledb:5432/aquanexis
DEVICE_JWT_SECRET=<MINIMUM_32_CHARACTERS_HEX_SECRET>
API_KEY_SALT=<MINIMUM_16_CHARACTERS_SALT>
```

### Step 2: Build & Start Services
```bash
docker compose up -d --build
```

### Step 3: Verify Services
```bash
docker compose ps
docker compose logs -f backend
```

Check health status:
```bash
curl -sf http://localhost:8000/health
```

### Step 4: Run Database Migrations
Migrations are applied automatically upon container startup, or manually via:
```bash
docker compose exec backend alembic upgrade head
```

---

## 3. Database Maintenance & Backup

### Create TimescaleDB Backup:
```bash
docker compose exec timescaledb pg_dump -U aquanexis -d aquanexis -Fc > backup_$(date +%Y%m%d).dump
```

### Restore Backup:
```bash
docker compose exec -T timescaledb pg_restore -U aquanexis -d aquanexis < backup_20261104.dump
```

