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

### G3 — Notification Providers (console, email, webhook) + Queue ✅
- [x] **G3.1** Notification provider abstraction (`app/services/notification_providers.py`)
- [x] **G3.2** Console/logging provider (`ConsoleNotificationProvider`)
- [x] **G3.3** Email provider (SMTP) (`EmailNotificationProvider`)
- [x] **G3.4** Webhook provider with SSRF protection (`WebhookNotificationProvider`)
- [x] **G3.5** Notification queue with retry logic (`app/services/notification_service.py`, `app/services/notification_worker.py`)
- [x] **G3.6** Notification templates per alert type (`app/models/notification.py` - `NotificationTemplate`, default templates in migration)
- [x] **G3.7** Unit tests (22 tests passing in `test_notification_providers.py`)
- [x] **G3.8** API endpoints (`app/api/v1/endpoints/notifications.py`) - list, stats, retry, cancel, provider config, templates, test
- [x] **G3.9** Migration `0007_notification_tables.py` - outbox, provider config, templates with default templates

### G4 — Maintenance Service: Filter Replacement, Calibration, Verification Workflows ✅
- [x] **G4.1** Filter replacement workflow (`app/services/maintenance_service.py` - install_filter, replace_filter)
- [x] **G4.2** Calibration workflow (`app/services/maintenance_service.py` - record_calibration, get_calibration_due)
- [x] **G4.3** Verification workflow (`app/services/maintenance_service.py` - start_verification, run_verification_checks)
- [x] **G4.4** Maintenance history tracking (`app/services/maintenance_service.py` - get_installed_filters, get_maintenance_events)
- [x] **G4.5** Filter catalog with 11 categories (`app/domain/maintenance.py` - FilterCategory enum)
- [x] **G4.6** Filter compatibility engine (`app/services/compatibility_engine.py`)
- [x] **G4.7** Installed filter lifecycle tracking (`app/domain/maintenance.py` - InstalledFilter, FilterLifecycleState)
- [x] **G4.8** Maintenance workflow state machine (`app/domain/maintenance.py` - MaintenanceWorkflow, MAINTENANCE_WORKFLOW_TRANSITIONS)
- [x] **G4.9** Calibration management with time/usage-based due tracking (`app/services/maintenance_service.py` - get_calibration_due, CalibrationPolicyModel)
- [x] **G4.10** Post-maintenance verification engine (`app/services/maintenance_service.py` - run_verification_checks)
- [x] **G4.11** Baseline versioning (`app/services/maintenance_service.py` - create_baseline_version, BaselineVersionModel)
- [x] **G4.12** Maintenance recommendations engine (`app/services/maintenance_service.py` - generate_recommendations)
- [x] **G4.13** Notification integration via G3 outbox (`app/services/maintenance_service.py` - _enqueue_maintenance_notification, etc.)
- [x] **G4.14** API endpoints for all maintenance operations (`app/api/v1/endpoints/maintenance.py`)
- [x] **G4.15** Database models for all maintenance entities (`app/models/maintenance.py`)
- [x] **G4.16** Migration `0008_maintenance_tables.py` - 10 tables with indexes and constraints
- [x] **G4.17** Unit tests: 28 tests passing (`test_maintenance.py`)

### G5 — Frontend Integration & Stabilization ✅
- [x] **G5.1** TypeScript error fixes across codebase (websocket.ts, Sparkline.tsx, SensorValueCard.tsx, SystemStateBadge.tsx, ui.test.tsx, LoginPage.tsx, LandingPage.tsx)
- [x] **G5.2** CSS/build fixes - globals.css rebuild to remove @apply conflicts, add dash animation
- [x] **G5.3** zodResolver import fix for @hookform/resolvers@3.x compatibility
- [x] **G5.4** Build system - frontend build passes, TypeScript passes, all tests pass
- [x] **G5.5** Frontend tests pass (14 tests)

### G5 — Frontend API Integration (IN PROGRESS)
- [x] **G5.1** Centralized typed API layer for all endpoints (telemetry, devices, water quality, purification, filter health, RUL, alerts, safety, maintenance, notifications)
- [x] **G5.2** TanStack Query hooks for all endpoints with proper query keys and invalidation
- [x] **G5.3** Dashboard integration - connect all primary dashboard components to real APIs (AquaScore, device health, sensor readings, FSI, FHI, RUL, risk, purification, hydraulic, alerts, maintenance)
- [x] **G5.4** Water Quality page connected to real APIs
- [x] **G5.4** Filter Health page connected to real APIs
- [x] **G5.5** Diagnostics page connected to real APIs
- [x] **G5.6** Alerts page connected to real APIs
- [x] **G5.7** Maintenance page connected to real APIs (catalog, compatibility, installed filters, replacement, calibration, verification, history)
- [ ] **G5.8** Calibration UI connected to real APIs
- [ ] **G5.9** Authentication flow - login, logout, protected routes, session loading, expired session handling
- [ ] **G5.10** Onboarding and device registration flows
- [ ] **G5.11** UI/UX quality improvements - typography, metric cards, charts, forms, tables, responsive layouts, loading/empty/error states
- [ ] **G5.11** Data provenance display (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)
- [ ] **G5.12** Frontend tests pass, production build passes

### G5.9 — G5 Acceptance Criteria (PENDING)
- [ ] All major API hooks implemented
- [ ] Dashboard uses actual backend data
- [ ] Water Quality page connected
- [ ] Filter Health page connected
- [ ] Diagnostics page connected
- [ ] Alerts page connected
- [ ] Maintenance page connected
- [ ] Calibration UI connected
- [ ] Verification UI connected
- [ ] Authentication flow works
- [ ] Protected routes work
- [ ] TypeScript passes
- [ ] Frontend tests pass
- [ ] Frontend production build passes
- [ ] Backend tests remain green
- [ ] No critical console errors

---

## Notes
- Update this file when tasks are completed or added
- Check off items as done
- Move items between sections as priorities shift
- Reference implementation-plan.md for detailed acceptance criteria
- Total unit tests now: 161 (36 Phase D/E/F + 28 Phase G1 + 19 Phase G2 auto-clear + 19 G2 auto-clear codes/logic + 22 Phase G3 notifications + 28 Phase G4 maintenance)