# AquaNexis — Task Checklist

## Current Sprint: Phase C — Live Dashboard + Alert Lifecycle (COMPLETE)

### Slice A — Runtime Stability ✅
### Slice B — Telemetry Foundation ✅

## Phase C — Live Dashboard + Alert Lifecycle ✅

### Backend (FastAPI)
- [x] **C1** Database - Alerts table with migration (0005_alerts_table.py)
- [x] **C2** Alert states - DETECTED, OPEN, ACKNOWLEDGED, SNOOZED, RESOLVED, AUTO_CLEARED with transitions (`app/domain/alerts.py`)
- [x] **C3** Alert severity - INFO, WARNING, CRITICAL with examples
- [x] **C4** Alert API - GET /api/v1/alerts, GET /api/v1/alerts/{id}, POST /acknowledge, POST /snooze, POST /resolve with filters
- [x] **C5** WebSocket - /ws/devices/{device_id} with events: telemetry.updated, alert.created, alert.updated, device.status_changed, sensor.health_changed
- [x] **C6** Alert evaluation integrated into telemetry ingestion (leak, pressure, flow, pump, water quality, tank level)
- [x] **C7** Simulator profiles already implemented (8 profiles)

### Migrations
- [x] 0005_alerts_table.py - Alerts table with indexes

### Domain Models
- [x] `app/domain/alerts.py` - Alert, AlertSeverity, AlertStatus, ALERT_TRANSITIONS, ALERT_CODES
- [x] `app/models/alert.py` - Alert ORM model with status, severity, evidence, timestamps

### API Endpoints
- [x] GET /api/v1/alerts (with filters: device, severity, status, date range)
- [x] GET /api/v1/alerts/{id}
- [x] POST /api/v1/alerts/{id}/acknowledge
- [x] POST /api/v1/alerts/{id}/snooze
- [x] POST /api/v1/alerts/{id}/resolve
- [x] GET /api/v1/alerts/summary/counts

### WebSocket
- [x] `/ws/devices/{device_id}` endpoint
- [x] ConnectionManager for broadcasting
- [x] Events: telemetry.updated, alert.created, alert.updated, device.status_changed, sensor.health_changed
- [x] Integrated with telemetry ingestion and alert evaluation

### Schemas
- [x] AlertResponse, AlertListQuery, AlertAcknowledgeRequest, AlertSnoozeRequest, AlertResolveRequest, AlertTransitionResponse

### Tests
- [x] Unit tests: Config (14 passed), Security (9 passed) - Total 23 passed

---

## Next Phase: Phase D — Water Intelligence + Filter Intelligence

### Phase D Requirements
- [ ] **D1** AquaScore algorithm
- [ ] **D2** Purification performance (TDS rejection, Recovery)
- [ ] **D3** Hydraulic intelligence (ΔP, flow deviation, fill-time, reject/permeate ratio)
- [ ] **D4** Filter Stress Index (deterministic first-layer)
- [ ] **D5** Filter Health Index (0-100)
- [ ] **D6** RUL pipeline (Random Forest / XGBoost)
- [ ] **D7** Failure-risk classification
- [ ] **D8** Explainability
- [ ] **D9** Data strategy (synthetic vs measured)
- [ ] **D10** ML model registry
- [ ] **D11** Acceptance criteria

---

## Notes
- Update this file when tasks are completed or added
- Check off items as done
- Move items between sections as priorities shift
- Reference implementation-plan.md for detailed acceptance criteria