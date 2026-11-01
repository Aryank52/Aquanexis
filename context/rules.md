# AquaNexis Development Rules

## Core Principles
1. **Modularity First** — Sensors, ML models, communication protocol, backend, and UI evolve independently
2. **Data Integrity** — Raw telemetry immutable after ingestion; derived values reproducible
3. **Safety as Subsystem** — Separate safety layer; frontend never performs hardware actions
4. **Explainable Intelligence** — Every prediction references model, version, inputs, confidence, explanation
5. **Engineering Grade UI** — Serious product UI with clear hierarchy, restrained colors, accessible states

## Architecture Boundaries
### Backend (FastAPI)
```
api/
 domain/
 services/
 repositories/
 models/
 schemas/
 analytics/
 ml/
 safety/
 infrastructure/
 tests/
```

### Frontend (React)
```
app/
 pages/
 components/
 features/
 api/
 hooks/
 state/
 charts/
 types/
 utils/
```

## Data Rules
- Every reading: device_id, timestamp, measured_values, quality_state, quality_flags
- Derived values must be reproducible from source data + configuration
- Predictions must reference: model_name, model_version, prediction_timestamp, inputs, confidence_interval, explanation

## ML Rules
- Start with deterministic/statistical anomaly rules
- Time-aware validation for sequential data
- Record MAE/RMSE for RUL; precision/recall/F1 for classification
- Never mix future observations into training features
- Store model version and dataset version
- No deep learning without accumulated dataset justification

## Sensor Rules (Level-1 Required)
- TDS/EC, pH, Turbidity, Temperature, Flow, Pressure, Tank Level, Leak, Pump Current/Energy
- Optional: Permeate flow, Reject flow, UV state, Vibration
- No lab-grade chemical sensors for feature inflation

## Safety Rules
- Leak/critical pressure/flow → validate → critical event → configured protective action → log → notify
- Frontend never directly performs hardware safety actions
- No exposed mains switching through hobby electronics
- Invalid sensor data → safe transparent state, not guessing

## Alert State Machine
```
NORMAL → INFO/WARNING/CRITICAL → ACKNOWLEDGED → RESOLVED
```
Required: stable type, severity, trigger_source, dedupe_key, created_time, ack_state, resolution_state, audit_metadata
No duplicate alert storms from sustained conditions

## Frontend Requirements
- Primary dashboard: AquaScore, Filter Health, RUL, System State, latest alert, sensor values, freshness, key trend
- Dedicated screens: Water Quality, Purification Performance, Filter Health, Diagnostics, Alerts, Maintenance, Device/Sensor Health
- TanStack Query for server state; lazy-load heavy pages; downsample charts; fast first load

## Testing Requirements
- Backend: validation, service logic, persistence, alert state machine
- ML: feature calculation, deterministic rules, model loading, evaluation smoke tests
- Frontend: key components, error/loading states, alert/maintenance workflows
- E2E: Playwright for Dashboard → anomaly → alert → filter health → maintenance

## Environment Variables (Never Commit Secrets)
- DATABASE_URL, APP_ENV, ALLOWED_ORIGINS, API_KEYS, DEVICE_AUTH_SECRETS, NOTIFICATION_PROVIDERS, MODEL_ARTIFACT_LOCATION

## Migration Policy
- Alembic for schema changes
- Never edit production schema manually without migrations in source control

## Documentation Policy
On architecture changes: update architecture.md, schema/API docs, memory.md if durable fact changed, add decision note

## Completion Protocol
1. Run relevant tests
2. Frontend build if frontend changed
3. Backend import/health checks if backend changed
4. Migration checks if schema changed
5. Verify no secrets introduced
6. Verify no network waterfalls
7. Inspect final diff
8. Update task checklist
9. Report: files changed, behavior added/changed, tests run, results, limitations, next task