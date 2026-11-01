# AquaNexis — Technical Requirements Document

## 1. System Architecture

### 1.1 High-Level Components
```
┌─────────────┐     HTTPS/TLS      ┌──────────────┐     ┌─────────────┐
│  ESP32      │ ─────────────────▶ │  FastAPI     │ ───▶ │ PostgreSQL  │
│  Sensors    │  Device JWT Auth   │  Backend     │      │  (Timescale)│
└─────────────┘                    └──────┬───────┘      └─────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
             ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
             │  Analytics  │         │    ML       │         │  Decision   │
             │  Engine     │         │  Pipeline   │         │  + Alert    │
             └─────────────┘         └─────────────┘         └──────┬──────┘
                                                                    │
                    ┌───────────────────────────────────────────────┘
                    ▼
             ┌─────────────┐
             │   React     │
             │   Frontend  │
             │ (TanStack   │
             │  Query)     │
             └─────────────┘
```

### 1.2 Communication Protocols
- **Device → Backend**: HTTPS POST `/api/v1/telemetry` with JSON body, Device JWT in Authorization header
- **Backend → Frontend**: REST API + WebSocket (`/ws/realtime`) for live updates
- **Internal**: Direct function calls (same process); gRPC if ML splits to separate service

### 1.3 Data Flow
```
Sensor Reading
      │
      ▼
┌─────────────┐
│  Validate   │ ──▶ Quality flags (range, rate, cross-sensor, stuck)
└─────────────┘
      │
      ▼
┌─────────────┐
│  Persist    │ ──▶ Raw reading (immutable) + Quality assessment
│  (Raw)      │
└─────────────┘
      │
      ▼
┌─────────────┐
│  Derive     │ ──▶ AquaScore, FSI, FHI, Performance metrics
└─────────────┘
      │
      ▼
┌─────────────┐
│  Detect     │ ──▶ Anomalies, threshold breaches, trend shifts
└─────────────┘
      │
      ▼
┌─────────────┐
│  Predict    │ ──▶ RUL, failure risk, confidence bands
└─────────────┘
      │
      ▼
┌─────────────┐
│  Alert      │ ──▶ State machine transitions, notifications
└─────────────┘
      │
      ▼
┌─────────────┐
│  Protect    │ ──▶ Safety actions (validated, logged, isolated)
└─────────────┘
```

## 2. Backend Specification (FastAPI)

### 2.1 Project Structure
```
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── telemetry.py
│   │   │   │   ├── devices.py
│   │   │   │   ├── water_quality.py
│   │   │   │   ├── filter_health.py
│   │   │   │   ├── diagnostics.py
│   │   │   │   ├── alerts.py
│   │   │   │   ├── maintenance.py
│   │   │   │   └── health.py
│   │   │   └── router.py
│   │   └── deps.py
│   ├── domain/
│   │   ├── devices.py
│   │   ├── readings.py
│   │   ├── water_quality.py
│   │   ├── filter_health.py
│   │   ├── diagnostics.py
│   │   ├── alerts.py
│   │   └── maintenance.py
│   ├── services/
│   │   ├── device_service.py
│   │   ├── telemetry_service.py
│   │   ├── water_quality_service.py
│   │   ├── filter_health_service.py
│   │   ├── diagnostics_service.py
│   │   ├── alert_service.py
│   │   └── maintenance_service.py
│   ├── repositories/
│   │   ├── device_repo.py
│   │   ├── reading_repo.py
│   │   ├── alert_repo.py
│   │   └── maintenance_repo.py
│   ├── models/
│   │   ├── device.py
│   │   ├── reading.py
│   │   ├── water_quality.py
│   │   ├── filter_health.py
│   │   ├── diagnostics.py
│   │   ├── alert.py
│   │   └── maintenance.py
│   ├── schemas/
│   │   ├── telemetry.py
│   │   ├── device.py
│   │   ├── water_quality.py
│   │   ├── filter_health.py
│   │   ├── diagnostics.py
│   │   ├── alert.py
│   │   └── maintenance.py
│   ├── analytics/
│   │   ├── aquascore.py
│   │   ├── trends.py
│   │   └── anomalies.py
│   ├── ml/
│   │   ├── models/
│   │   ├── features.py
│   │   ├── filter_stress.py
│   │   ├── filter_health.py
│   │   ├── rul.py
│   │   └── registry.py
│   ├── safety/
│   │   ├── leak_protection.py
│   │   ├── pressure_protection.py
│   │   ├── flow_protection.py
│   │   └── energy_protection.py
│   ├── infrastructure/
│   │   ├── database.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   ├── security.py
│   │   └── websocket.py
│   └── main.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── alembic/
│   ├── versions/
│   └── env.py
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── Dockerfile
└── .env.example
```

### 2.2 API Endpoints (v1)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (DB, ML, config) |
| POST | `/api/v1/telemetry` | Ingest sensor reading (device auth) |
| GET | `/api/v1/devices/{id}` | Device info + sensor config |
| PUT | `/api/v1/devices/{id}` | Update device config (admin) |
| GET | `/api/v1/devices/{id}/telemetry/latest` | Latest reading with quality |
| GET | `/api/v1/devices/{id}/telemetry/history` | Paginated history with downsampling |
| GET | `/api/v1/devices/{id}/water-quality` | AquaScore + component scores + trends |
| GET | `/api/v1/devices/{id}/filter-health` | FSI, FHI, RUL, explanation |
| GET | `/api/v1/devices/{id}/diagnostics` | Pressure, flow, leak, pump, tank |
| GET | `/api/v1/devices/{id}/alerts` | Active + history with filters |
| POST | `/api/v1/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/api/v1/alerts/{id}/resolve` | Resolve alert |
| POST | `/api/v1/maintenance/filter-replacement` | Record filter replacement |
| POST | `/api/v1/maintenance/calibration` | Record calibration |
| GET | `/api/v1/maintenance/history` | Maintenance events |
| WS | `/ws/realtime/{device_id}` | Live telemetry, alerts, state |

### 2.3 Database Schema (PostgreSQL + TimescaleDB)

```sql
-- Devices
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    serial_number VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(128),
    firmware_version VARCHAR(32),
    sensor_config JSONB NOT NULL DEFAULT '{}',
    calibration JSONB NOT NULL DEFAULT '{}',
    safety_config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(32) NOT NULL DEFAULT 'offline',
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Raw Sensor Readings (TimescaleDB hypertable)
CREATE TABLE sensor_readings (
    id BIGSERIAL,
    device_id UUID NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    tds DOUBLE PRECISION,
    ec DOUBLE PRECISION,
    ph DOUBLE PRECISION,
    turbidity DOUBLE PRECISION,
    temperature DOUBLE PRECISION,
    flow DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    tank_level DOUBLE PRECISION,
    leak_detected BOOLEAN,
    pump_current DOUBLE PRECISION,
    permeate_flow DOUBLE PRECISION,
    reject_flow DOUBLE PRECISION,
    uv_state BOOLEAN,
    vibration DOUBLE PRECISION,
    quality_flags JSONB NOT NULL DEFAULT '{}',
    overall_quality VARCHAR(16) NOT NULL DEFAULT 'GOOD',
    PRIMARY KEY (device_id, timestamp, id)
);

SELECT create_hypertable('sensor_readings', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Water Quality Scores
CREATE TABLE water_quality_scores (
    id BIGSERIAL,
    device_id UUID NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    aquascore SMALLINT NOT NULL,  -- 0-100
    tds_score SMALLINT,
    ph_score SMALLINT,
    turbidity_score SMALLINT,
    temp_score SMALLINT,
    trend_1h DOUBLE PRECISION,
    trend_24h DOUBLE PRECISION,
    trend_7d DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,
    anomaly_flags JSONB DEFAULT '{}',
    PRIMARY KEY (device_id, timestamp, id)
);
SELECT create_hypertable('water_quality_scores', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Filter Health
CREATE TABLE filter_health (
    id BIGSERIAL,
    device_id UUID NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    fsi DOUBLE PRECISION NOT NULL,  -- 0-100 Filter Stress Index
    fhi DOUBLE PRECISION NOT NULL,  -- 0-100 Filter Health Index
    rul_days DOUBLE PRECISION,      -- Remaining Useful Life
    rul_confidence_lower DOUBLE PRECISION,
    rul_confidence_upper DOUBLE PRECISION,
    model_name VARCHAR(64) NOT NULL,
    model_version VARCHAR(32) NOT NULL,
    dataset_version VARCHAR(32),
    input_features JSONB NOT NULL,
    explanation JSONB,
    PRIMARY KEY (device_id, timestamp, id)
);
SELECT create_hypertable('filter_health', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Purification Performance
CREATE TABLE purification_performance (
    id BIGSERIAL,
    device_id UUID NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    rejection_rate DOUBLE PRECISION,  -- 0-1
    recovery_ratio DOUBLE PRECISION,  -- 0-1
    permeate_quality DOUBLE PRECISION,
    feed_quality DOUBLE PRECISION,
    efficiency DOUBLE PRECISION,
    PRIMARY KEY (device_id, timestamp, id)
);
SELECT create_hypertable('purification_performance', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- System Diagnostics
CREATE TABLE system_diagnostics (
    id BIGSERIAL,
    device_id UUID NOT NULL REFERENCES devices(id),
    timestamp TIMESTAMPTZ NOT NULL,
    pressure_trend DOUBLE PRECISION,
    flow_trend DOUBLE PRECISION,
    leak_probability DOUBLE PRECISION,
    tank_fill_rate DOUBLE PRECISION,
    tank_empty_rate DOUBLE PRECISION,
    pump_efficiency DOUBLE PRECISION,
    pump_current_trend DOUBLE PRECISION,
    fouling_indicator DOUBLE PRECISION,
    PRIMARY KEY (device_id, timestamp, id)
);
SELECT create_hypertable('system_diagnostics', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Alerts
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id),
    alert_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,  -- INFO, WARNING, CRITICAL
    trigger_source VARCHAR(64) NOT NULL,
    dedupe_key VARCHAR(128) NOT NULL,
    trigger_value DOUBLE PRECISION,
    threshold_value DOUBLE PRECISION,
    explanation JSONB,
    state VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, ACKNOWLEDGED, RESOLVED
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ,
    acknowledged_by VARCHAR(128),
    resolved_at TIMESTAMPTZ,
    resolved_by VARCHAR(128),
    resolved_reason VARCHAR(256),
    UNIQUE (device_id, dedupe_key, state) WHERE state IN ('ACTIVE', 'ACKNOWLEDGED')
);

CREATE INDEX idx_alerts_device_state ON alerts(device_id, state);
CREATE INDEX idx_alerts_created ON alerts(created_at DESC);

-- Maintenance Events
CREATE TABLE maintenance_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id),
    event_type VARCHAR(32) NOT NULL,  -- FILTER_REPLACEMENT, CALIBRATION, VERIFICATION
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    performed_by VARCHAR(128),
    pre_metrics JSONB,
    post_metrics JSONB,
    notes TEXT,
    verified BOOLEAN DEFAULT FALSE,
    verification_data JSONB
);

CREATE INDEX idx_maintenance_device ON maintenance_events(device_id, performed_at DESC);

-- Model Artifacts Registry
CREATE TABLE model_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(64) NOT NULL,
    version VARCHAR(32) NOT NULL,
    dataset_version VARCHAR(32),
    artifact_path VARCHAR(512) NOT NULL,
    metrics JSONB,  -- MAE, RMSE, precision, recall, etc.
    status VARCHAR(16) NOT NULL DEFAULT 'staging',  -- staging, production, archived
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    promoted_at TIMESTAMPTZ,
    UNIQUE (name, version)
);
```

### 2.4 Configuration (Environment Variables)

```bash
# Application
APP_ENV=development          # development, staging, production
APP_HOST=0.0.0.0
APP_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/aquanexis
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Device Authentication
DEVICE_JWT_SECRET=change-me-in-production
DEVICE_JWT_ALGORITHM=HS256
DEVICE_JWT_EXPIRY_HOURS=24

# API Security
API_KEY_SALT=change-me
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW_SECONDS=60

# ML
MODEL_ARTIFACT_DIR=/app/models
ML_ENABLED=true

# Notifications
NOTIFICATION_PROVIDERS=console  # console, email, webhook
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
WEBHOOK_URL=

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json  # json, console

# Safety
SAFETY_ENABLED=true
SAFETY_ACTION_TIMEOUT_SECONDS=5
```

### 2.5 Device Telemetry Payload

```json
{
  "device_id": "uuid",
  "timestamp": "2026-10-31T12:00:00Z",
  "readings": {
    "tds": 45.2,
    "ec": 72.1,
    "ph": 7.1,
    "turbidity": 0.3,
    "temperature": 23.5,
    "flow": 1.2,
    "pressure": 350.0,
    "tank_level": 78.0,
    "leak_detected": false,
    "pump_current": 0.85,
    "permeate_flow": 1.0,
    "reject_flow": 0.2,
    "uv_state": true,
    "vibration": 0.02
  }
}
```

Response:
```json
{
  "accepted": true,
  "reading_id": "uuid",
  "quality_assessment": {
    "overall": "GOOD",
    "flags": {
      "tds": {"range": "OK", "rate": "OK", "cross_sensor": "OK"},
      "ph": {"range": "OK", "rate": "SUSPECT", "cross_sensor": "OK"}
    }
  },
  "derived": {
    "aquascore": 92,
    "fsi": 23.5,
    "fhi": 87.2,
    "rul_days": 145
  }
}
```

## 3. Frontend Specification (React + TypeScript)

### 3.1 Project Structure
```
frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── providers.tsx
│   │   └── routes.tsx
│   ├── pages/
│   │   ├── landing/
│   │   │   └── LandingPage.tsx
│   │   ├── dashboard/
│   │   │   └── DashboardPage.tsx
│   │   ├── water-quality/
│   │   │   └── WaterQualityPage.tsx
│   │   ├── purification-performance/
│   │   │   └── PurificationPerformancePage.tsx
│   │   ├── filter-health/
│   │   │   └── FilterHealthPage.tsx
│   │   ├── diagnostics/
│   │   │   └── DiagnosticsPage.tsx
│   │   ├── alerts/
│   │   │   └── AlertsPage.tsx
│   │   ├── maintenance/
│   │   │   └── MaintenancePage.tsx
│   │   ├── device-health/
│   │   │   └── DeviceHealthPage.tsx
│   │   └── readiness/
│   │       └── ReadinessPage.tsx
│   ├── components/
│   │   ├── ui/           # Primitive components (Button, Card, Badge, etc.)
│   │   ├── layout/       # Header, Sidebar, Footer
│   │   ├── charts/       # Chart wrappers
│   │   ├── dashboard/    # Dashboard-specific composites
│   │   ├── water-quality/
│   │   ├── filter-health/
│   │   ├── diagnostics/
│   │   ├── alerts/
│   │   └── maintenance/
│   ├── features/
│   │   ├── telemetry/
│   │   ├── water-quality/
│   │   ├── filter-health/
│   │   ├── diagnostics/
│   │   ├── alerts/
│   │   └── maintenance/
│   ├── api/
│   │   ├── client.ts
│   │   ├── endpoints.ts
│   │   └── websocket.ts
│   ├── hooks/
│   │   ├── useTelemetry.ts
│   │   ├── useWaterQuality.ts
│   │   ├── useFilterHealth.ts
│   │   ├── useDiagnostics.ts
│   │   ├── useAlerts.ts
│   │   └── useMaintenance.ts
│   ├── state/
│   │   ├── device.ts
│   │   └── ui.ts
│   ├── charts/
│   │   ├── AquaScoreGauge.tsx
│   │   ├── FilterHealthChart.tsx
│   │   ├── RULChart.tsx
│   │   ├── TrendChart.tsx
│   │   ├── DiagnosticsPanel.tsx
│   │   └── index.ts
│   ├── types/
│   │   ├── api.ts
│   │   ├── telemetry.ts
│   │   ├── water-quality.ts
│   │   ├── filter-health.ts
│   │   ├── diagnostics.ts
│   │   ├── alerts.ts
│   │   └── maintenance.ts
│   ├── utils/
│   │   ├── formatters.ts
│   │   ├── validators.ts
│   │   ├── constants.ts
│   │   └── helpers.ts
│   └── styles/
│       ├── globals.css
│       ├── variables.css
│       └── theme.css
├── public/
├── tests/
│   ├── components/
│   ├── pages/
│   └── e2e/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── Dockerfile
└── .env.example
```

### 3.2 Key UI Components

| Component | Purpose | Location |
|-----------|---------|----------|
| `AquaScoreGauge` | Circular gauge 0-100 with color bands | `charts/` |
| `FilterHealthCard` | FSI, FHI, RUL with trend sparklines | `dashboard/` |
| `SystemStateBadge` | NORMAL/DEGRADED/CRITICAL with pulse | `dashboard/` |
| `ActiveAlertBanner` | Latest critical alert with acknowledge | `dashboard/` |
| `SensorValueCard` | Value + unit + freshness + quality badge | `dashboard/` |
| `TrendChart` | Multi-series line chart with downsampling | `charts/` |
| `DiagnosticsPanel` | Pressure, flow, leak, pump, tank grids | `charts/` |
| `AlertTimeline` | State machine visualization | `alerts/` |
| `MaintenanceWizard` | Stepper for filter replacement/calibration | `maintenance/` |
| `ReadinessChecklist` | Engineering board with status indicators | `readiness/` |

### 3.3 State Management
- **Server State**: TanStack Query (React Query) — caching, deduping, prefetching, invalidation
- **Client State**: React Context + useReducer for UI state (sidebar, modals, toasts)
- **WebSocket State**: Custom hook managing connection, reconnection, message routing

### 3.4 Chart Library
- **Primary**: `uPlot` for high-performance time-series (downsampling built-in)
- **Gauges**: Custom SVG components (lightweight, animated)
- **Fallback**: Recharts for complex compositions if needed

### 3.5 Styling
- **Tailwind CSS** with custom design tokens
- **CSS Variables** for theming (light/dark)
- **No component library** — build primitives to avoid bundle bloat

## 4. Firmware Specification (ESP32)

### 4.1 Sensor Interface
| Sensor | Interface | Library | Calibration |
|--------|-----------|---------|-------------|
| TDS/EC | Analog (GPIO32) | Custom | Two-point |
| pH | Analog (GPIO33) | Custom | Two-point buffer |
| Turbidity | Analog (GPIO34) | Custom | Formazin reference |
| Temperature | OneWire (GPIO25) | DallasTemperature | Factory |
| Flow | Pulse (GPIO26) | Interrupt counting | K-factor |
| Pressure | I2C (0x28) | MS5837 library | Factory |
| Tank Level | Analog (GPIO35) | Custom | Empty/full points |
| Leak | Digital (GPIO27) | GPIO interrupt | Threshold |
| Pump Current | I2C (0x40) | INA219 library | Shunt calibration |

### 4.2 Firmware Architecture
```
main.cpp
├── SensorManager       # Polling, calibration, quality flags
├── TelemetryBuilder    # JSON assembly, timestamp (NTP)
├── NetworkManager      # WiFi, MQTT/HTTPS, reconnection
├── AuthManager         # Device JWT, token refresh
├── SafetyController    # Local safety fallback (valve control)
├── OTAUpdater          # Firmware updates
└── Diagnostics         # Self-test, sensor health
```

### 4.3 Local Safety Fallback
- Independent of cloud: leak → close valve within 100ms
- Pressure > max → relief valve / pump stop
- Flow < min with pump on → pump stop
- Stored in NVS, survives reboot

## 5. ML Pipeline Specification

### 5.1 Model Registry
```
models/
├── baseline/
│   ├── filter_stress_v1/       # Deterministic formula
│   ├── filter_health_v1/       # Deterministic formula
│   └── rul_v1/                 # Weibull survival baseline
├── statistical/
│   ├── anomaly_iforest_v1/     # Isolation Forest (sklearn)
│   └── rul_regression_v1/      # Gradient Boosting (XGBoost/LightGBM)
└── production/                 # Symlinks to active versions
```

### 5.2 Feature Engineering
```python
# Filter Stress Features
features = {
    "cumulative_volume_l": float,
    "cumulative_hours": float,
    "avg_pressure_kpa": float,
    "pressure_variance": float,
    "avg_feed_tds": float,
    "tds_variance": float,
    "cleaning_cycles": int,
    "days_since_install": int,
    "avg_temperature_c": float,
    "recovery_ratio_trend": float
}

# Anomaly Features (sliding window)
window_features = {
    "mean": float,
    "std": float,
    "min": float,
    "max": float,
    "slope": float,
    "z_score": float,
    "iqr_outlier_count": int
}
```

### 5.3 Training Pipeline
```
data/processed/device_{id}/
├── train.parquet      # Time-aware split (no future leakage)
├── val.parquet
└── test.parquet

scripts/
├── prepare_dataset.py
├── train_baseline.py
├── train_statistical.py
├── evaluate.py
└── register_model.py
```

### 5.4 Evaluation Metrics
| Model | Metrics | Threshold |
|-------|---------|-----------|
| RUL | MAE, RMSE, MAPE | MAE < 14 days |
| Failure Risk | Precision, Recall, F1, AUC | Recall > 0.85 |
| Anomaly | Precision, Recall, F1 | Precision > 0.80 |

## 6. Infrastructure

### 6.1 Docker Compose (Development)
```yaml
services:
  postgres:
    image: timescale/timescaledb:latest-pg16
    environment:
      POSTGRES_DB: aquanexis
      POSTGRES_USER: aquanexis
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    depends_on: [postgres]
    volumes: [./backend:/app, models:/app/models]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: .env
    depends_on: [backend]
    volumes: [./frontend:/app, /app/node_modules]

  simulator:
    build: ./simulator
    env_file: .env
    depends_on: [backend]

volumes:
  postgres_data:
  models:
```

### 6.2 CI/CD Pipeline
```yaml
# .github/workflows/ci.yml
jobs:
  backend:
    - lint (ruff, mypy)
    - test (pytest, coverage > 80%)
    - build (docker)
    - migration check (alembic check)
  
  frontend:
    - lint (eslint, prettier)
    - typecheck (tsc)
    - test (vitest, coverage > 70%)
    - build (vite)
    - e2e (playwright)

  integration:
    - docker compose up
    - health checks
    - api contract tests
```

## 7. Security Requirements

| Layer | Controls |
|-------|----------|
| **Device Auth** | JWT per device, short expiry, rotation, revocation list |
| **API Auth** | API keys for admin, JWT for devices, rate limiting |
| **Transport** | TLS 1.3 enforced, HSTS, certificate pinning for devices |
| **Secrets** | Environment variables only, never in code, rotate quarterly |
| **Database** | Parameterized queries, least-privilege roles, encryption at rest |
| **Audit** | All mutations logged with actor, timestamp, before/after |

## 8. Observability

### 8.1 Metrics (Prometheus)
- `http_requests_total` by endpoint, status
- `http_request_duration_seconds` histogram
- `telemetry_ingested_total` by device, quality
- `alert_created_total` by type, severity
- `safety_action_triggered_total` by type
- `model_prediction_duration_seconds`
- `db_query_duration_seconds`

### 8.2 Logging
- Structured JSON logs (request_id, device_id, user_id)
- Levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Correlation IDs across request boundaries

### 8.3 Tracing
- OpenTelemetry instrumentation
- Trace: device ingestion → validation → persistence → derivation → alert

## 9. Deployment Checklist

- [ ] Database migrations applied
- [ ] Model artifacts in `MODEL_ARTIFACT_DIR`
- [ ] Environment variables configured (no defaults in prod)
- [ ] TLS certificates provisioned
- [ ] Device JWT secret rotated
- [ ] Backup/restore tested
- [ ] Load test passed (10k devices)
- [ ] Safety actions tested in staging
- [ ] Rollback plan documented