# AquaNexis Backend

FastAPI-based backend for the AquaNexis Predictive Water Intelligence Platform.

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 16+ with TimescaleDB extension
- Docker & Docker Compose (recommended)

### Local Development with Docker Compose

```bash
# From project root
docker compose up -d postgres backend

# View logs
docker compose logs -f backend

# Run tests
docker compose exec backend pytest -v
```

### Local Development without Docker

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment Variables

See `.env.example` for all required variables. Key variables:

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `DEVICE_JWT_SECRET` | JWT signing secret (min 32 chars) | Yes |
| `API_KEY_SALT` | Salt for API key hashing | Yes |
| `APP_ENV` | Environment (development/staging/production) | No |
| `ALLOWED_ORIGINS` | CORS origins | No |

## Project Structure

```
backend/
├── app/
│   ├── api/v1/endpoints/     # API route handlers
│   ├── domain/               # Pure domain models (no framework deps)
│   ├── services/             # Business logic orchestration
│   ├── repositories/         # Data access layer
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── analytics/            # AquaScore, trends, anomalies
│   ├── ml/                   # ML models (FSI, FHI, RUL)
│   ├── safety/               # Safety subsystem (isolated)
│   ├── infrastructure/       # Config, DB, logging, security
│   └── main.py               # FastAPI application entry
├── tests/
│   ├── unit/                 # Unit tests (fast, no DB)
│   └── integration/          # Integration tests (with DB)
├── alembic/                  # Database migrations
├── pyproject.toml            # Dependencies & tool config
├── Dockerfile                # Multi-stage Docker build
└── .env.example              # Environment template
```

## API Endpoints

### Health
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe (checks DB, config, models)
- `GET /health/detailed` - Detailed health info
- `GET /metrics` - Prometheus metrics

### Devices (planned)
- `POST /api/v1/devices` - Provision new device
- `GET /api/v1/devices/{id}` - Get device info
- `PUT /api/v1/devices/{id}` - Update device config

### Telemetry (planned)
- `POST /api/v1/telemetry` - Ingest sensor reading (device auth)
- `GET /api/v1/devices/{id}/telemetry/latest` - Latest reading
- `GET /api/v1/devices/{id}/telemetry/history` - Historical data

### Water Quality (planned)
- `GET /api/v1/devices/{id}/water-quality` - AquaScore + components
- `GET /api/v1/devices/{id}/trends` - Trend analysis
- `GET /api/v1/devices/{id}/anomalies` - Anomaly detection

### Filter Health (planned)
- `GET /api/v1/devices/{id}/filter-health` - FSI, FHI, RUL
- `GET /api/v1/devices/{id}/rul` - RUL prediction with confidence

### Diagnostics (planned)
- `GET /api/v1/devices/{id}/diagnostics` - Pressure, flow, leak, tank, pump

### Alerts (planned)
- `GET /api/v1/devices/{id}/alerts` - Active + historical alerts
- `POST /api/v1/alerts/{id}/acknowledge` - Acknowledge alert
- `POST /api/v1/alerts/{id}/resolve` - Resolve alert

### Maintenance (planned)
- `POST /api/v1/maintenance/filter-replacement` - Record replacement
- `POST /api/v1/maintenance/calibration` - Record calibration
- `GET /api/v1/maintenance/history` - Maintenance history

## Database

### Schema
- `devices` - Device registry and configuration
- `sensor_readings` - Raw telemetry (TimescaleDB hypertable)
- `water_quality_scores` - Computed AquaScore + components
- `filter_health` - FSI, FHI, RUL predictions
- `purification_performance` - Rejection rate, recovery, efficiency
- `system_diagnostics` - Pressure, flow, leak, tank, pump diagnostics
- `alerts` - Alert state machine with deduplication
- `maintenance_events` - Filter replacement, calibration, verification
- `model_artifacts` - ML model registry

### Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check for pending migrations
alembic check
```

## Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/unit/test_health.py -v

# Run integration tests only
pytest tests/integration/ -v
```

## Code Quality

```bash
# Lint
ruff check .

# Format
ruff format .

# Type check
mypy app

# All checks (run in CI)
ruff check . && ruff format --check . && mypy app && pytest -v
```

## Development Guidelines

### Architecture Rules
1. **Domain layer purity** - No framework imports in `domain/`, `analytics/`, `ml/`, `safety/`
2. **Dependency direction** - Inner layers don't depend on outer layers
3. **Immutability** - Raw sensor readings never modified after insertion
4. **Provenance** - Every derived value traces to source data + config + model version

### Adding New Features
1. Define domain models in `domain/`
2. Create Pydantic schemas in `schemas/`
3. Implement repository in `repositories/`
4. Implement service logic in `services/`
5. Add API endpoints in `api/v1/endpoints/`
6. Write tests in `tests/`
7. Create migration if schema changes

### Security
- Never commit secrets
- Rotate `DEVICE_JWT_SECRET` quarterly
- Use `SecretStr` for sensitive config values
- Validate all inputs with Pydantic

## Deployment

### Docker
```bash
docker build -t aquanexis-backend ./backend
docker run -p 8000:8000 --env-file .env aquanexis-backend
```

### Production Checklist
- [ ] `APP_ENV=production`
- [ ] Strong `DEVICE_JWT_SECRET` (64+ chars)
- [ ] TLS termination (nginx/Traefik)
- [ ] Database connection pooling tuned
- [ ] Log aggregation configured
- [ ] Metrics scraping configured
- [ ] Backup/restore tested
- [ ] Migration rollback plan documented