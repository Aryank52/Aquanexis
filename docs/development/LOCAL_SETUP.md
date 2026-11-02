# Local Development Setup

## Prerequisites

- **Windows 10/11** with Administrator access
- **Python 3.12+** (tested with 3.12.10)
- **Node.js 20+** (tested with 20.x)
- **PostgreSQL 16+** with TimescaleDB extension
- **Git**

## Quick Start with Docker Compose (Recommended)

```bash
# 1. Clone and navigate
git clone <repo> && cd AquaNexis

# 2. Copy environment template
cp .env.example .env
# Edit .env with secure secrets (JWT secret min 32 chars, etc.)

# 3. Start all services
docker compose up -d

# 4. View logs
docker compose logs -f backend
```

### Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 (or 3001 if 3000 busy) | React Dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | TimescaleDB |
| Metrics | http://localhost:8000/metrics | Prometheus |

> **Note**: Vite now uses `strictPort: true` (v5.4+). If port 3000 is occupied, Vite will fail instead of auto-incrementing. Ensure port 3000 is free or stop conflicting processes.

---

## Manual Development Setup (Without Docker)

### 1. PostgreSQL Setup

#### Windows (PostgreSQL 16 from winget)

```powershell
# Run as Administrator
winget install PostgreSQL.PostgreSQL.16

# Start the service (requires Admin)
net start postgresql-x64-16

# If service fails to start (antivirus interference), use pg_ctl directly:
# & "E:\postsql database\bin\pg_ctl.exe" start -D "E:\postsql database\data" -l "E:\postsql database\data\postgresql.log"

# Create database and user
psql -U postgres -c "CREATE DATABASE aquanexis;"
psql -U postgres -c "CREATE USER aquanexis WITH PASSWORD 'aquanexis';"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE aquanexis TO aquanexis;"
psql -U postgres -d aquanexis -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

> **Known Issue**: PostgreSQL on Windows may crash with exception `0xC0000142` (DLL initialization failure) after ~2-3 minutes if antivirus software interferes with the data directory (`E:\postsql database\data`). 
> **Workaround**: Exclude `E:\postsql database\data` from antivirus/Windows Defender scanning, or run PostgreSQL in Docker (requires Docker Desktop).

#### Verify Connection

```bash
psql -h localhost -U aquanexis -d aquanexis -c "SELECT version();"
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev]"

# Copy environment template
copy .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at **http://localhost:3000** and will proxy API requests to **http://localhost:8000**.

---

## Environment Configuration

### Backend (.env)

```bash
# Required
APP_ENV=development
DEVICE_JWT_SECRET=your-super-secret-jwt-key-min-32-chars-long
DATABASE_URL=postgresql+asyncpg://aquanexis:aquanexis@localhost:5432/aquanexis

# Optional
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
ML_ENABLED=true
NOTIFICATION_PROVIDERS=console
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_DEVICE_ID=00000000-0000-0000-0000-000000000001
```

---

## Verified Local Frontend URL

**http://localhost:3000**

The Vite dev server runs on port 3000 and proxies `/api` and `/ws` to the backend at `http://localhost:8000`.

---

## Running Tests

### Frontend

```bash
cd frontend
npm run typecheck    # TypeScript check
npm run build        # Production build
npm test -- --run    # Unit tests
npm run lint         # ESLint
npm run format:check # Prettier check
```

### Backend

```bash
cd backend
.\.venv\Scripts\Activate.ps1

# Unit tests (no DB required)
pytest tests/unit/test_config.py tests/unit/test_security.py tests/unit/test_phase_d_services.py tests/unit/test_alert_state_machine.py tests/unit/test_auto_clear_integration.py tests/unit/test_notification_providers.py tests/unit/test_maintenance.py -v

# All unit tests (requires PostgreSQL)
pytest tests/unit -v

# Integration tests (requires PostgreSQL)
pytest tests/integration -v

# Lint & TypeCheck
ruff check .
ruff format --check .
mypy app/
```

---

## Simulator

```bash
cd backend
.\.venv\Scripts\Activate.ps1

# Normal operation
python simulator.py --profile normal --interval 10

# Filter stress scenario
python simulator.py --profile filter_stress --interval 5

# Leak detection
python simulator.py --profile leak --interval 2
```

---

## Common Issues

| Issue | Solution |
|-------|----------|
| `npm ci` fails | Run `npm install` first to update package-lock.json |
| ESLint config not found | Ensure `.eslintrc.cjs` exists in frontend/ |
| PostgreSQL connection refused | Ensure PostgreSQL service is running (`net start postgresql-x64-16` as Admin) |
| `alembic upgrade head` fails | Check DATABASE_URL in .env matches running PostgreSQL |
| Frontend can't reach backend | Check VITE_API_URL in frontend/.env matches backend URL |
| WebSocket connection fails | Check VITE_WS_URL in frontend/.env and backend CORS settings |
| ESLint errors | Run `npm run lint` to see issues; some are pre-existing in codebase |

---

## Port Summary

| Service | Port | Protocol |
|---------|------|----------|
| Frontend | 3000 | HTTP |
| Backend | 8000 | HTTP/WS |
| PostgreSQL | 5432 | TCP |
| Prometheus Metrics | 8000/metrics | HTTP |

---

## IDE Setup (VS Code)

### Recommended Extensions

- Python
- Pylance
- TypeScript and JavaScript Language Features
- ESLint
- Prettier
- Tailwind CSS IntelliSense
- SQLite (for database inspection)

### Settings (`.vscode/settings.json`)

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/backend/.venv/Scripts/python.exe",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```