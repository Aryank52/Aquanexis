# AquaNexis — Task Checklist

## Current Sprint: Phase G — Maintenance & Lifecycle (IN PROGRESS)

### Slice A — Runtime Stability ✅
### Slice B — Telemetry Foundation ✅
### Phase C — Live Dashboard + Alert Lifecycle ✅
### Phase D — Water Intelligence + Filter Intelligence ✅
### Phase E — Filter Intelligence Enhancement + Model Validation ✅
### Phase F — Reliability & Safety ✅

## Phase F — Reliability & Safety ✅

### Backend (FastAPI)
- [x] **F1** Leak detection with automatic valve closure (`app/services/leak_protection.py`, `app/services/safety_service.py`)
- [x] **F2** Pressure diagnostics with membrane fouling detection (`app/services/pressure_protection.py`, `app/services/hydraulic_service.py`)
- [x] **F3** Pump protection (dry-run, overcurrent) (`app/services/energy_protection.py`)
- [x] **F3** Sensor failure detection and graceful degradation (`app/services/flow_protection.py`, `app/services/energy_protection.py`)
- [x] **F4** System Reliability Score (`app/services/failure_risk_service.py`)
- [x] **F5** Safety Service: validation, action execution, logging, notification (`app/services/safety_service.py`)
- [x] **F6** Safety config per device (thresholds, actions, cooldowns) (`app/domain/safety.py`, `app/schemas/safety.py`)
- [x] **F7** Firmware command protocol (validated payload, signed) (`app/domain/safety.py` - `FirmwareCommand`, `FirmwareResponse`, `SafetyActionCommand`)
- [x] **F8** Safety endpoints: `GET /safety/config`, `POST /safety/test` (admin) (`app/api/v1/endpoints/safety.py`)
- [x] **F9** Diagnostics endpoints: `/diagnostics` (aggregated), `/diagnostics/history` (`app/api/v1/endpoints/diagnostics.py`)
- [x] **F10** Unit tests: diagnostic calculations, safety validation logic (13 Phase F tests passing)

### Migrations
- [x] 0006_safety_tables.py - Safety events and safety actions tables with indexes

### Domain Models (`app/domain/safety.py`)
- [x] SafetyActionType, SafetyEventType, SafetyActionStatus, SafetyEventType
- [x] SafetyConfig, SafetyValidationContext, SafetyValidationResult
- [x] LeakDiagnostics, PressureDiagnostics, FlowDiagnostics, PumpDiagnostics, TankDiagnostics, SystemDiagnostics
- [x] SafetyAction, SafetyEvent, SafetyActionCommand, SafetyActionResponse, SafetyConfig, SafetyActionCommand, SafetyActionResponse, SafetyAuditEvent
- [x] Firmware command protocol (FirmwareCommand, FirmwareResponse)
- [x] Safety audit events (SafetyAuditEvent)

### Services (`app/services/`)
- [x] `app/services/leak_protection.py` - Leak detection and protection
- [x] `app/services/pressure_protection.py` - Pressure monitoring and protection
- [x] `app/services/flow_protection.py` - Flow monitoring and protection
- [x] `app/services/energy_protection.py` - Pump current/power monitoring and protection
- [x] `app/services/safety_service.py` - Main safety orchestration service

### API Endpoints (`app/api/v1/endpoints/`)
- [x] `safety.py` - GET /safety/config, PUT /safety/config/{device_id}, POST /safety/test, POST /safety/action, POST /safety/action/test, GET /safety/events/{device_id}, GET /safety/audit/{device_id}

### Schemas (`app/schemas/safety.py`)
- [x] SafetyConfigResponse, SafetyConfigUpdate
- [x] SafetyTestRequest, SafetyTestResponse
- [x] SafetyActionCommand, SafetyActionResponse

### Database Models (`app/models/safety.py`)
- [x] SafetyEventModel - Safety event audit trail with indexes
- [x] SafetyActionModel - Safety action command log with indexes
- [x] SafetyActionType, SafetyEventType, SafetyActionStatus, SafetyEventType enums with native_enum=False

### Tests (All 36 unit tests passing)
- [x] `test_phase_d_services.py` - 13 tests for Phase D services (including new safety tests)
- [x] `test_config.py` - 14 tests
- [x] `test_security.py` - 9 tests
- Total: 36 tests passing

### Database Migrations
- [x] 0006_safety_tables.py - Safety events and safety actions tables with indexes

---

## Phase G — Maintenance & Lifecycle (IN PROGRESS)

### G1 — Alert State Machine Enforcement (API + Service) ✅
- [x] **G1.1** AlertStateMachine service (`app/services/alert_state_machine.py`)
- [x] **G1.2** State transition validation with audit logging
- [x] **G1.3** Auto-clear logic for self-clearing alert codes
- [x] **G1.4** API endpoints using state machine: `/acknowledge`, `/snooze`, `/resolve`
- [x] **G1.5** New endpoints: `/valid-transitions`, `/bulk-transition`, `/auto-clear-check`
- [x] **G1.6** Unit tests: 28 tests passing (`test_alert_state_machine.py`)

### G2 — Auto-resolution for Self-Clearing Alerts (water quality, pressure) ✅
- [x] **G2.1** Integrate auto-clear with evaluation engine (`app/api/v1/endpoints/telemetry.py` - evaluate_alerts function)
- [x] **G2.2** Auto-clear water quality alerts (water_quality_degraded, water_quality_critical)
- [x] **G2.3** Auto-clear pressure alerts (pressure_low, pressure_high, pressure_unstable, pressure_differential_high)
- [x] **G2.4** Auto-clear flow alerts (flow_low, flow_high, flow_interrupted, flow_unstable)
- [x] **G2.5** Auto-clear sensor alerts (sensor_missing, sensor_stuck, sensor_impossible_value, sensor_rapid_change, sensor_calibration_due, sensor_calibration_overdue)
- [x] **G2.6** Auto-clear device alerts (device_offline, device_reconnected)
- [x] **G2.7** Auto-clear maintenance alerts (maintenance_due)
- [x] **G2.8** Unit tests for auto-resolution logic (19 tests passing in `test_auto_clear_integration.py`)

### G3 — Notification Providers (console, email, webhook) + Queue — NEXT
- [ ] **G3.1** Notification provider abstraction
- [ ] **G3.2** Console/logging provider
- [ ] **G3.3** Email provider (SMTP)
- [ ] **G3.4** Webhook provider
- [ ] **G3.5** Notification queue with retry logic
- [ ] **G3.6** Notification templates per alert type
- [ ] **G3.7** Unit tests

### G4 — Maintenance Service: Filter Replacement, Calibration, Verification Workflows
- [ ] **G4.1** Filter replacement workflow
- [ ] **G4.2** Calibration workflow
- [ ] **G4.3** Verification workflow
- [ ] **G4.4** Maintenance history tracking

### G5 — Maintenance Endpoints: `/filter-replacement`, `/calibration`, `/verification`, `/history`
- [ ] **G5.1** POST /maintenance/filter-replacement
- [ ] **G5.2** POST /maintenance/calibration
- [ ] **G5.3** POST /maintenance/verification
- [ ] **G5.4** GET /maintenance/history

### G6 — Post-Maintenance Verification: Automated Quality Check, Baseline Reset
- [ ] **G6.1** Automated quality check after maintenance
- [ ] **G6.2** Baseline reset after filter replacement
- [ ] **G6.3** Verification result recording

### G7 — Calibration Due Tracking (time + usage based)
- [ ] **G7.1** Calibration schedule per sensor
- [ ] **G7.2** Usage-based calibration tracking
- [ ] **G7.3** Calibration overdue alerts

### G8 — Unit Tests: Alert Transitions, Maintenance Workflows, Verification Logic
- [ ] **G8.1** Tests for maintenance workflows
- [ ] **G8.2** Tests for verification logic
- [ ] **G8.3** Tests for calibration tracking

---

## Notes
- Update this file when tasks are completed or added
- Check off items as done
- Move items between sections as priorities shift
- Reference implementation-plan.md for detailed acceptance criteria
- Total unit tests now: 102 (36 Phase D/E/F + 28 Phase G1 + 19 Phase G2 auto-clear + 19 G2 auto-clear codes/logic)