# AquaNexis — Architecture Document

## 1. Architectural Style

**Modular Monolith** — Single deployable backend with clear internal boundaries, designed for future service extraction if scale demands.

### Principles
- **Domain-Driven Design**: Bounded contexts for Devices, Telemetry, Water Quality, Filter Health, Diagnostics, Alerts, Maintenance, Safety
- **Dependency Rule**: Inner layers (domain, analytics, ML, safety) have no dependencies on outer layers (API, infrastructure)
- **Immutability**: Raw telemetry never modified; corrections are new events
- **Provenance**: Every derived value and prediction traces to source data + config + model version

## 2. Context Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            AQUANEXIS BACKEND                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Devices    │  │  Telemetry   │  │ Water Quality│  │ Filter Health│    │
│  │  Context     │  │  Context     │  │  Context     │  │  Context     │    │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘    │
│         │                 │                 │                 │            │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴───────┐    │
│  │                    SHARED KERNEL (schemas, value objects)           │    │
│  └────────────────────────────────────────────────────────────────────┘    │
│         │                 │                 │                 │            │
│  ┌──────┴───────┐  ┌─────┴─────┐   ┌───────┴───────┐  ┌────┴────────┐   │
│  │ Diagnostics  │  │  Alerts   │   │ Maintenance   │  │   Safety    │   │
│  │  Context     │  │  Context  │   │  Context      │  │  Context    │   │
│  └──────────────┘  └───────────┘   └───────────────┘  └─────────────┘   │
│         │                 │                 │                 │            │
│  ┌──────┴─────────────────┴─────────────────┴─────────────────┴───────┐    │
│  │                      ANALYTICS / ML LAYER                            │    │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌────────────────┐  │    │
│  │  │ AquaScore │  │  Trends   │  │ Anomalies │  │ Filter Models  │  │    │
│  │  │  Engine   │  │  Engine   │  │  Engine   │  │ (FSI/FHI/RUL)  │  │    │
│  │  └───────────┘  └───────────┘  └───────────┘  └────────────────┘  │    │
│  └────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3. Layer Architecture

### 3.1 Domain Layer (Pure Python, No Framework Deps)
```
domain/
├── devices.py           # Device, SensorConfig, Calibration, DeviceStatus
├── readings.py          # SensorReading, QualityFlags, QualityState
├── water_quality.py     # AquaScore, ParameterScore, Trend, Anomaly
├── filter_health.py     # FSI, FHI, RUL, ModelMetadata, Explanation
├── diagnostics.py       # PressureDiagnostics, FlowDiagnostics, LeakDiagnostics, 
                         # TankDiagnostics, PumpDiagnostics
├── alerts.py            # Alert, AlertType, Severity, AlertState, DedupeKey
└── maintenance.py       # MaintenanceEvent, EventType, VerificationResult
```

**Rules**: No imports from `api/`, `services/`, `repositories/`, `infrastructure/`. Only stdlib + shared kernel.

### 3.2 Analytics/ML Layer (Pure Python, No Framework Deps)
```
analytics/
├── aquascore.py         # compute_aquascore(reading, config) -> AquaScore
├── trends.py            # compute_trends(readings, windows) -> TrendSet
├── anomalies.py         # detect_anomalies(window) -> AnomalyResult
└── performance.py       # compute_performance(feed, permeate) -> Performance

ml/
├── features.py          # extract_features(readings, config) -> FeatureVector
├── filter_stress.py     # compute_fsi(features, config) -> FSI
├── filter_health.py     # compute_fhi(fsi, features, config) -> FHI
├── rul.py               # predict_rul(features, model) -> RULPrediction
├── anomaly_model.py     # IsolationForest wrapper
└── registry.py          # ModelRegistry (load, version, metadata)
```

**Rules**: Stateless pure functions. Models loaded via registry. No DB access.

### 3.3 Services Layer (Orchestration, Transactions)
```
services/
├── device_service.py          # Device CRUD, provisioning, config
├── telemetry_service.py       # Ingest → validate → persist → derive → detect → alert
├── water_quality_service.py   # Query scores, trends, anomalies
├── filter_health_service.py   # Query FSI/FHI/RUL, trigger retraining
├── diagnostics_service.py     # Query diagnostics, compute real-time
├── alert_service.py           # State machine, deduplication, notifications
├── maintenance_service.py     # Workflows, verification, history
└── safety_service.py          # Validate → execute → log protective actions
```

**Rules**: Single transaction per request where possible. Call domain + analytics + repositories. No direct HTTP/DB logic.

### 3.4 Repositories Layer (Data Access)
```
repositories/
├── device_repo.py         # Device CRUD, status updates
├── reading_repo.py        # Raw reading insert, query (TimescaleDB optimized)
├── score_repo.py          # Water quality score insert, query
├── filter_repo.py         # Filter health insert, query
├── diagnostic_repo.py     # Diagnostics insert, query
├── alert_repo.py          # Alert CRUD + state transitions + dedupe
└── maintenance_repo.py    # Maintenance events CRUD
```

**Rules**: SQLAlchemy async. No business logic. Return domain objects or DTOs.

### 3.5 API Layer (HTTP/WebSocket)
```
api/v1/endpoints/
├── telemetry.py           # POST /telemetry
├── devices.py             # Device CRUD, config
├── water_quality.py       # GET /water-quality, /trends, /anomalies
├── filter_health.py       # GET /filter-health, /rul
├── diagnostics.py         # GET /diagnostics
├── alerts.py              # GET /alerts, POST /acknowledge, /resolve
├── maintenance.py         # POST /filter-replacement, /calibration
├── health.py              # GET /health, /ready
└── websocket.py           # WS /realtime
```

**Rules**: Thin — validation (Pydantic), auth, call service, return response. No business logic.

### 3.6 Infrastructure Layer (External Concerns)
```
infrastructure/
├── database.py            # AsyncEngine, sessionmaker, init_db
├── config.py              # Settings (pydantic-settings), validation
├── logging.py             # Structured logging setup
├── security.py            # JWT, API keys, device auth
├── websocket.py           # Connection manager, broadcasting
├── notifications.py       # Email, webhook providers
└── migrations/            # Alembic environment
```

## 4. Data Architecture

### 4.1 Immutable Raw Layer
- `sensor_readings` hypertable — append-only, never updated
- Quality flags stored per-reading for auditability
- Partitioned by time (1-day chunks), indexed by device_id

### 4.2 Derived Layer (Materialized Views / Computed Tables)
- `water_quality_scores` — computed on ingest, stored for query performance
- `filter_health` — computed on ingest + scheduled recalculation
- `purification_performance` — computed on ingest
- `system_diagnostics` — computed on ingest + windowed analysis

### 4.3 Operational Layer
- `devices` — mutable configuration, status
- `alerts` — state machine with deduplication constraint
- `maintenance_events` — append-only audit log
- `model_artifacts` — registry with promotion workflow

### 4.4 Data Flow Guarantees
| Operation | Consistency | Latency Target |
|-----------|-------------|----------------|
| Telemetry ingest | Eventual (derived async) | < 100ms ack |
| Alert creation | Strong (dedupe constraint) | < 50ms |
| Safety action | Strong (validated, logged) | < 500ms |
| Dashboard query | Read committed | < 200ms |
| Historical export | Snapshot isolation | < 5s |

## 5. Safety Architecture

### 5.1 Isolation Principle
```
┌─────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                       │
│  (Services, Analytics, API) — NO DIRECT HARDWARE CONTROL    │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
            ┌───────────────┐   ┌───────────────┐
            │  Safety       │   │  Firmware     │
            │  Service      │   │  (Local)      │
            │  (Validate,   │   │  (Immediate   │
            │   Log, Notify)│   │   Fallback)   │
            └───────┬───────┘   └───────┬───────┘
                    │                   │
                    ▼                   ▼
            ┌───────────────────────────────────┐
            │       HARDWARE INTERFACE          │
            │  (Valve, Pump, Relief — Abstract) │
            └───────────────────────────────────┘
```

### 5.2 Safety Action Flow
```
Sensor Anomaly Detected
         │
         ▼
┌────────────────────────┐
│  Safety Service        │
│  1. Re-validate (multi-sensor correlation)    │
│  2. Check cooldown / rate limits               │
│  3. Determine action (configured per device)   │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Execute Action        │ ──▶ Firmware command (validated payload)
│  - Close inlet valve   │
│  - Stop pump           │
│  - Open relief         │
└───────────┬────────────┘
            │
            ▼
┌────────────────────────┐
│  Log & Notify          │
│  - SafetyEvent record  │
│  - Critical Alert      │
│  - Notification        │
└────────────────────────┘
```

### 5.3 Safety Config (Per Device)
```json
{
  "leak": { "action": "close_inlet_valve", "validate_with": ["flow_delta", "pressure_drop"], "cooldown_sec": 300 },
  "overpressure": { "action": "open_relief_valve", "threshold_kpa": 600, "cooldown_sec": 60 },
  "dry_run": { "action": "stop_pump", "min_flow_lpm": 0.1, "cooldown_sec": 120 },
  "overcurrent": { "action": "stop_pump", "max_current_a": 2.5, "cooldown_sec": 180 }
}
```

## 6. Alert Architecture

### 6.1 State Machine
```
                    ┌──────────────┐
                    │    NORMAL    │
                    └──────┬───────┘
                           │ threshold breached
                           ▼
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         ┌─────────┐ ┌──────────┐ ┌───────────┐
         │  INFO   │ │ WARNING  │ │ CRITICAL  │
         └────┬────┘ └────┬─────┘ └─────┬─────┘
              │           │             │
              │ acknowledge (user or auto)        │
              ▼           ▼             ▼
         ┌──────────────────────────────────────┐
         │           ACKNOWLEDGED               │
         └────────────────────┬─────────────────┘
                              │ condition cleared + user confirm
                              ▼
                       ┌──────────────┐
                       │   RESOLVED   │
                       └──────────────┘
```

### 6.2 Deduplication
- `dedupe_key = f"{device_id}:{alert_type}:{source}"`
- Unique constraint on `(device_id, dedupe_key, state)` where state ∈ {ACTIVE, ACKNOWLEDGED}
- New occurrence → update existing alert (trigger_value, timestamp), not insert

### 6.3 Alert Types (Extensible Registry)
```python
ALERT_REGISTRY = {
    "water_quality_degraded": {"severity": "WARNING", "auto_resolve": True},
    "filter_stress_high": {"severity": "WARNING", "auto_resolve": False},
    "filter_health_critical": {"severity": "CRITICAL", "auto_resolve": False},
    "leak_detected": {"severity": "CRITICAL", "auto_resolve": False},
    "pressure_anomaly": {"severity": "WARNING", "auto_resolve": True},
    "pump_energy_anomaly": {"severity": "WARNING", "auto_resolve": True},
    "sensor_fault": {"severity": "WARNING", "auto_resolve": True},
    "calibration_due": {"severity": "INFO", "auto_resolve": False},
    "maintenance_due": {"severity": "INFO", "auto_resolve": False},
}
```

## 7. Frontend Architecture

### 7.1 Component Hierarchy
```
App
├── Providers (QueryClient, WebSocket, Auth, Theme)
├── Router
│   ├── Landing (public)
│   ├── Dashboard (auth)
│   │   ├── Header (device selector, connection status)
│   │   ├── AquaScoreGauge
│   │   ├── FilterHealthCard
│   │   ├── SystemStateBadge
│   │   ├── ActiveAlertBanner
│   │   ├── SensorGrid (SensorValueCard x N)
│   │   └── KeyTrendChart
│   ├── WaterQuality
│   │   ├── ParameterScoreCards
│   │   ├── TrendCharts (1h, 24h, 7d)
│   │   └── AnomalyTimeline
│   ├── PurificationPerformance
│   │   ├── RejectionRateGauge
│   │   ├── RecoveryRatioChart
│   │   └── EfficiencyTrend
│   ├── FilterHealth
│   │   ├── FSIGauge / FHI Gauge
│   │   ├── RULChart with confidence band
│   │   ├── ExplanationPanel
│   │   └── ModelMetadataCard
│   ├── Diagnostics
│   │   ├── PressurePanel
│   │   ├── FlowPanel
│   │   ├── LeakPanel
│   │   ├── TankPanel
│   │   └── PumpEnergyPanel
│   ├── Alerts
│   │   ├── AlertList (filterable)
│   │   ├── AlertDetail (state machine viz)
│   │   └── AlertTimeline
│   ├── Maintenance
│   │   ├── FilterReplacementWizard
│   │   ├── CalibrationWizard
│   │   └── MaintenanceHistory
│   ├── DeviceHealth
│   │   ├── SensorHealthGrid
│   │   ├── FirmwareStatus
│   │   └── CalibrationStatus
│   └── Readiness
│       ├── ReadinessChecklist
│       └── SystemHealthOverview
```

### 7.2 Data Fetching Strategy
| Data Type | Strategy | Stale Time | Cache Time |
|-----------|----------|------------|------------|
| Latest telemetry | WebSocket + Query fallback | 0s | 30s |
| AquaScore / Filter Health | Query (5s refetch) | 5s | 60s |
| Historical trends | Query (on demand) | 60s | 5min |
| Alerts | WebSocket + Query | 0s | 30s |
| Maintenance history | Query (on demand) | 5min | 30min |
| Device config | Query (on mount) | 10min | 1hr |

### 7.3 Real-Time Architecture
```
WebSocket Connection (per device)
    │
    ├─▶ telemetry:latest → Update SensorGrid, AquaScore, FilterHealth
    ├─▶ alert:created → Update AlertBanner, AlertList, play notification
    ├─▶ alert:updated → Update AlertList, AlertDetail
    ├─▶ safety:action → Show safety toast, update SystemState
    └─▶ device:status → Update Header connection badge
```

## 8. ML Architecture

### 8.1 Model Lifecycle
```
Development                    Staging                    Production
     │                            │                          │
     ▼                            ▼                          ▼
┌─────────┐                ┌─────────────┐            ┌─────────────┐
│ Train   │ ─────────────▶ │ Validate    │ ────────▶  │ Promote     │
│ (local) │   Artifact     │ (metrics,   │   Symlink  │ (atomic     │
└─────────┘   + metadata   │  shadow)    │            │  switch)    │
                      └─────────────┘            └─────────────┘
                              │                          │
                              ▼                          ▼
                       ┌─────────────┐            ┌─────────────┐
                       │  Model      │            │  Inference  │
                       │  Registry   │            │  (cached    │
                       │  (PostgreSQL)            │   in proc)  │
                       └─────────────┘            └─────────────┘
```

### 8.2 Inference Contract
```python
# Every prediction returns:
@dataclass
class Prediction:
    value: float                    # RUL days, FSI, FHI, anomaly score
    confidence_lower: Optional[float]
    confidence_upper: Optional[float]
    model_name: str
    model_version: str
    dataset_version: str
    prediction_timestamp: datetime
    input_features: Dict[str, float]
    explanation: Optional[Dict]     # Feature contributions
```

## 9. Evolution Strategy

### 9.1 Service Extraction Triggers
| Context | Trigger | Target |
|---------|---------|--------|
| ML Pipeline | Training > 30min, GPU needed | Separate ML service (gRPC) |
| Telemetry Ingestion | > 50k req/s | Dedicated ingestion service (Kafka) |
| Notifications | Multiple providers, retry logic | Notification service |
| Safety | Regulatory certification needed | Isolated safety service |

### 9.2 Database Evolution
- **Phase 1**: Single PostgreSQL + TimescaleDB
- **Phase 2**: Read replicas for analytics queries
- **Phase 3**: ClickHouse / Apache Druid for OLAP if needed
- **Never**: Shard by device_id prematurely

## 10. Decision Log

| Date | Decision | Context |
|------|----------|---------|
| 2026-10-31 | Modular monolith over microservices | Team size, operational simplicity, clear boundaries enable future extraction |
| 2026-10-31 | TimescaleDB for time-series | Native hypertable, compression, continuous aggregates, PostgreSQL compatibility |
| 2026-10-31 | Deterministic ML first | No historical data; statistical baselines are auditable and explainable |
| 2026-10-31 | TanStack Query over Redux/Zustand | Server state ≠ client state; built-in caching, deduping, invalidation |
| 2026-10-31 | uPlot for charts | 100k+ points at 60fps; downsampling; no virtual DOM overhead |
| 2026-10-31 | Safety as separate subsystem | Regulatory clarity; firmware fallback; auditability; frontend isolation |