# AquaNexis — Predictive Water Intelligence Platform

> **Sense → Validate → Understand → Detect → Predict → Alert → Protect → Assist**

AquaNexis is a production-minded intelligent water purification intelligence system that combines multi-parameter sensing, purification performance measurement, filter health diagnostics, and safety-critical protection into a coherent, modular platform.

## 🎯 Core Capabilities

| Domain | Features |
|--------|----------|
| **Water Sensing** | 9+ parameters: TDS, EC, pH, Turbidity, Temperature, Flow, Pressure, Tank Level, Leak, Pump Current |
| **Water Intelligence** | AquaScore (0-100), Trend Analysis, Statistical Anomaly Detection |
| **Filter Intelligence** | Filter Stress Index (FSI), Filter Health Index (FHI), RUL Prediction with Explainable Output |
| **Purification Performance** | Rejection Rate, Recovery Ratio, Efficiency Tracking |
| **System Diagnostics** | Pressure Fouling, Leak Probability, Tank Stagnation, Pump Energy Degradation |
| **Safety Protection** | Validated Leak/Overpressure/Dry-run/Overcurrent Actions with Audit Trail |
| **Alert Management** | State Machine (NORMAL → INFO/WARN/CRIT → ACK → RESOLVED) with Deduplication |
| **Maintenance Workflows** | Guided Filter Replacement, Calibration, Post-Maintenance Verification |

## 🏗 Architecture

```
ESP32 / Sensors
      ↓ Wi-Fi / HTTPS
FastAPI Backend
      ↓ PostgreSQL + TimescaleDB
Analytics / ML Layer
      ↓
Decision + Alert Engine
      ↓
React Frontend (TanStack Query)
```

### Backend (FastAPI)
- **Modular Monolith** with clean domain boundaries
- **Async SQLAlchemy 2.0** + TimescaleDB for time-series
- **Pydantic v2** for validation & OpenAPI
- **Structured JSON Logging** with request correlation
- **JWT Device Auth** + API Key Admin Auth

### Frontend (React + TypeScript)
- **TanStack Query** for server state
- **Tailwind CSS** with design tokens
- **uPlot** for high-performance time-series charts
- **Custom SVG Gauges** for metrics
- **WCAG 2.1 AA** accessible

### ML Pipeline
- **Deterministic Baselines First** (no data required)
- **Statistical Models** when data accumulates
- **Model Registry** with versioning & promotion
- **Explainable Predictions** (coefficients/SHAP-ready)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Or: Python 3.12+, Node.js 20+, PostgreSQL 16+ with TimescaleDB

### With Docker Compose (Recommended)

```bash
# Clone and navigate
git clone <repo> && cd AquaNexis

# Copy environment template
cp .env.example .env
# Edit .env with secure secrets (JWT secret, etc.)

# Start all services
docker compose up -d

# View logs
docker compose logs -f backend
```

### Services
| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React Dashboard |
| Backend API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Database | localhost:5432 | TimescaleDB |
| Metrics | http://localhost:8000/metrics | Prometheus |

### Manual Development Setup

```bash
# Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
python -m uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

## 📁 Repository Structure

```
AquaNexis/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/v1/         # REST endpoints
│   │   ├── domain/         # Pure domain models
│   │   ├── services/       # Business logic
│   │   ├── repositories/   # Data access
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── analytics/      # AquaScore, trends, anomalies
│   │   ├── ml/             # FSI, FHI, RUL models
│   │   ├── safety/         # Safety subsystem
│   │   └── infrastructure/ # Config, DB, logging, security
│   ├── tests/              # Unit & integration tests
│   └── alembic/            # Database migrations
├── frontend/               # React frontend
│   ├── src/
│   │   ├── app/            # App shell, routing
│   │   ├── pages/          # Route pages
│   │   ├── components/     # UI components
│   │   ├── features/       # Feature logic
│   │   ├── api/            # API client
│   │   ├── hooks/          # Custom hooks
│   │   └── state/          # Client state
│   └── tests/
├── docs/                   # Documentation
│   ├── PRD.md              # Product Requirements
│   ├── TRD.md              # Technical Requirements
│   ├── architecture.md     # Architecture decisions
│   ├── backend-schema.md   # Database & API schemas
│   ├── app-flow.md         # User journeys & data flows
│   ├── uiux-brief.md       # Design system
│   ├── implementation-plan.md
│   └── stack-decision.md   # Technology choices
├── context/                # Project context for AI
│   ├── rules.md            # Development rules
│   ├── brain.md            # Architectural knowledge
│   └── memory.md           # Durable project facts
├── tasks/
│   └── task.md             # Task checklist
├── docker-compose.yml
└── .github/workflows/      # CI/CD pipelines
```

## 🧪 Testing

```bash
# Backend tests
cd backend && pytest -v --cov=app

# Frontend tests
cd frontend && npm test

# E2E tests (requires running services)
cd frontend && npm run test:e2e
```

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| [PRD](docs/PRD.md) | Product requirements & success metrics |
| [TRD](docs/TRD.md) | Technical specifications & API contracts |
| [Architecture](docs/architecture.md) | System design & context map |
| [Backend Schema](docs/backend-schema.md) | Database tables & API schemas |
| [App Flow](docs/app-flow.md) | User journeys & data flows |
| [UI/UX Brief](docs/uiux-brief.md) | Design system & components |
| [Implementation Plan](docs/implementation-plan.md) | Slice-by-slice delivery plan |
| [Stack Decisions](docs/stack-decision.md) | Technology choices & rationale |

## 🔧 Configuration

Key environment variables (see `.env.example`):

```bash
# Required
DEVICE_JWT_SECRET=              # Min 32 chars, rotate quarterly
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Optional
APP_ENV=development             # development|staging|production
ALLOWED_ORIGINS=http://localhost:3000
ML_ENABLED=true
NOTIFICATION_PROVIDERS=console  # console|email|webhook
```

## 🛡 Security

- **Never commit secrets** - use `.env` (gitignored)
- **Rotate JWT secrets** quarterly
- **TLS termination** at reverse proxy (nginx/Traefik)
- **Device-scoped JWT** with short expiry (24h)
- **Rate limiting** per device/IP
- **Audit logging** for all mutations

## 📊 Observability

- **Metrics**: Prometheus at `/metrics`
- **Logs**: Structured JSON to stdout
- **Health**: `/health` (liveness), `/ready` (readiness)
- **Tracing**: OpenTelemetry ready (planned)

## 🤝 Contributing

1. Read [Development Rules](context/rules.md)
2. Follow [Architecture Boundaries](docs/architecture.md#3-layer-architecture)
3. Write tests for new features
4. Update documentation with changes
5. Run CI checks before PR

## 📄 License

Proprietary - All rights reserved.

---

**Built with engineering rigor for water intelligence.**