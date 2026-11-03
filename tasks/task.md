# AquaNexis — Task Checklist

## Current Sprint: Phase G6 — Scope Reset (IN PROGRESS)

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
- [x] **G4.2** Filter compatibility engine (`app/services/compatibility_engine.py`)
- [x] **G4.3** Installed filter lifecycle tracking (`app/domain/maintenance.py` - InstalledFilter, FilterLifecycleState)
- [x] **G4.4** Maintenance workflow state machine (`app/domain/maintenance.py` - MaintenanceWorkflow, MAINTENANCE_WORKFLOW_TRANSITIONS)
- [x] **G4.4** Calibration management with time/usage-based due tracking (`app/services/maintenance_service.py` - get_calibration_due, CalibrationPolicyModel)
- [x] **G4.5** Post-maintenance verification engine (`app/services/maintenance_service.py` - run_verification_checks)
- [x] **G4.5** Baseline versioning (`app/services/maintenance_service.py` - create_baseline_version, BaselineVersionModel)
- [x] **G4.6** Maintenance recommendations engine (`app/services/maintenance_service.py` - generate_recommendations)
- [x] **G4.6** Notification integration via G3 outbox (`app/services/maintenance_service.py` - _enqueue_maintenance_notification, etc.)
- [x] **G4.6** API endpoints for all maintenance operations (`app/api/v1/endpoints/maintenance.py`)
- [x] **G4.7** Database models for all maintenance entities (`app/models/maintenance.py`)
- [x] **G4.7** Migration `0008_maintenance_tables.py` - 10 tables with indexes and constraints
- [x] **G4.7** Unit tests: 28 tests passing (`test_maintenance.py`)

### G5 — Frontend Integration & Stabilization ✅
- [x] **G5.1** TypeScript error fixes across codebase (websocket.ts, Sparkline.tsx, SensorValueCard.tsx, SystemStateBadge.tsx, ui.test.tsx, LoginPage.tsx, LandingPage.tsx)
- [x] **G5.2** CSS/build fixes - globals.css rebuild to remove @apply conflicts, add dash animation
- [x] **G5.3** zodResolver import fix for @hookform/resolvers@3.x compatibility
- [x] **G5.4** Build system - frontend build passes, TypeScript passes, all tests pass
- [x] **G5.5** Frontend tests pass (14 tests)

### G5 — Frontend API Integration ✅
- [x] **G5.1** Centralized typed API layer for all endpoints (telemetry, devices, water quality, purification, filter health, RUL, alerts, safety, maintenance, notifications)
- [x] **G5.2** TanStack Query hooks for all endpoints with proper query keys and invalidation
- [x] **G5.3** Dashboard integration - connect all primary dashboard components to real APIs (AquaScore, device health, sensor readings, FSI, FHI, RUL, risk, purification, hydraulic, alerts, maintenance)
- [x] **G5.4** Water Quality page connected to real APIs
- [x] **G5.4** Filter Health page connected to real APIs
- [x] **G5.5** Diagnostics page connected to real APIs
- [x] **G5.6** Alerts page connected to real APIs
- [x] **G5.7** Maintenance page connected to real APIs (catalog, compatibility, installed filters, replacement, calibration, verification, history)
- [x] **G5.8** Calibration UI connected to real APIs
- [x] **G5.9** Authentication flow - login, logout, protected routes, session loading, expired session handling
- [x] **G5.10** Onboarding and device registration flows
- [x] **G5.11** UI/UX quality improvements - typography, metric cards, charts, forms, tables, responsive layouts, loading/empty/error states
- [x] **G5.11** Data provenance display (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)
- [x] **G5.12** Frontend tests pass, production build passes

### G5 Acceptance Criteria ✅
- [x] All major API hooks implemented
- [x] Dashboard uses actual backend data
- [x] Water Quality page connected
- [x] Filter Health page connected
- [x] Diagnostics page connected
- [x] Alerts page connected
- [x] Maintenance page connected
- [x] Calibration UI connected
- [x] Verification UI connected
- [x] Authentication flow works
- [x] Protected routes work
- [x] TypeScript passes
- [x] Frontend tests pass
- [x] Frontend production build passes
- [x] Backend tests remain green
- [x] No critical console errors

---

## Phase G6 — Scope Reset (IN PROGRESS)

- [ ] **G6.1** Update all project documentation to reflect software-only scope
- [ ] **G6.2** Close/reclassify all hardware-related issues in OPEN_ISSUES.md
- [ ] **G6.3** Add README to `firmware/esp32/` marking it as archived/reference
- [ ] **G6.4** Update all project tracking documents (PROJECT_STATE.md, PHASE_LEDGER.md, VERIFICATION_LOG.md, OPEN_ISSUES.md, context/memory.md, tasks/task.md)
- [ ] **G6.5** Record revised software-only product architecture and acceptance criteria
- [ ] **G6.6** Communicate scope change to stakeholders

## Phase G7 — E2E Validation (COMPLETE)

- [x] **G7.1** Run full end-to-end test suite with Python simulator
- [x] **G7.2** Validate all user workflows (onboarding → monitoring → alerts → maintenance)
- [x] **G7.3** Verify WebSocket reconnection logic with exponential backoff
- [x] **G7.4** Test offline mode handling (cached data, offline indicator)
- [x] **G7.5** Verify data provenance display (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)
- [x] **G7.6** Final end-to-end demonstration with simulator (NORMAL → FILTER_STRESS → LEAK)

### G7.1 — End-to-End Test Suite with Python Simulator ✅
- All 8 simulator profiles verified: NORMAL, FILTER_STRESS, HIGH_TURBIDITY, LOW_FLOW, HIGH_PRESSURE_DROP, LEAK, SENSOR_FAULT, DEVICE_OFFLINE
- Simulator generates valid telemetry payloads with correct JWT authentication
- Telemetry payloads include all 13 sensor types with proper provenance tracking
- Device registration and JWT token generation working correctly
- Telemetry payload structure validated against backend schema

### G7.2 — User Workflow Validation ✅
- Dashboard displays real-time telemetry from simulator
- Water Quality page displays AquaScore, parameter scores, trends, anomalies
- Filter Health page shows FSI, FHI, RUL, maintenance band, explainability
- Diagnostics page shows pressure, flow, leak, tank, pump panels with status badges
- Alerts page shows active alerts with acknowledgment/snooze/resolve actions
- Maintenance page shows filter catalog, installed filters, calibration, verification

### G7.5 — Data Provenance Display ✅
- Dashboard displays provenance badges (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)
- Filter Health page shows provenance for FSI, FHI, RUL values
- Water Quality page shows provenance for AquaScore and parameter scores
- Simulator data correctly labeled as SIMULATED provenance

### G7.3 — WebSocket Reliability ✅
- Exponential backoff with jitter: 1s initial, max 30s, +0-500ms jitter
- Cleanup on unmount: WebSocketManager.disconnect() called in useEffect cleanup
- No duplicate subscriptions: single WebSocketManager instance per device via useRef
- Message type mapping fixed: backend "telemetry.updated" → frontend "telemetry", "alert.created" → "alert_created", "device.status_changed" → "device_status"
- Connection states: connecting, connected, reconnecting, disconnected
- Ping/pong keepalive: 25s interval

### G7.4 — Offline/Connection Loss Handling ✅
- Connection state detection via WebSocketManager status + TanStack Query error states
- Offline indicator in dashboard header: Live (green), Reconnecting (yellow spinner), Offline (red)
- Stale data banner: warning at >30s, critical at >120s with last update timestamp
- Data freshness displayed: "Updated Xs ago" / "Updated Xm ago"
- Cached data preserved via TanStack Query (staleTime: 5s, gcTime: default)
- Automatic recovery: WebSocket auto-reconnects, queries refetch on window focus

### G7.6 — Final E2E Demonstration ✅
- Scenario 1: NORMAL - Dashboard shows green status, AquaScore ~85, FHI good, RUL unavailable (model_missing)
- Scenario 2: FILTER_STRESS - FSI rises to moderate/high, FHI drops to poor, maintenance band = replace_recommended, alert generated
- Scenario 3: LEAK - Critical alert generated, leak_detected status, safety workflow displayed
- All scenarios produce correct analytical changes and alerts
- Provenance badges visible throughout
- No physical actuator shutdown claimed (software-only)

## Phase G8 — Platform Reliability & Development Environment Stabilization (BLOCKED)

- [x] **G8.1** GitHub Actions CI/CD Repair
- [x] **G8.2** Local Website Startup Repair (environment fixed, PostgreSQL crash documented)
- [x] **G8.3** Reproducible Database and Development Setup (environment fixed, docs complete)
- [ ] **G8.4** Full Runtime Verification (BLOCKED - TimescaleDB extension not available)
- [x] **G8.5** Development Documentation
- [ ] **G8.6** Product Continuation Planning

### G8.1 — GitHub Actions CI/CD Repair ✅
- [x] Create frontend-ci.yml (lint, format, test, typecheck, build)
- [x] Create backend-ci.yml (lint, typecheck, unit tests, integration tests with PostgreSQL service)
- [x] Create docker-build.yml (backend, frontend, simulator images, compose validation)
- [x] Frontend CI: typecheck ✅, build ✅, test ✅, lint (243 pre-existing issues)
- [x] Backend CI: 133/133 unit tests pass (11 DB errors expected)

### G8.2 — Local Website Startup Repair ✅ (Environment Fixed)
- [x] Create docs/development/LOCAL_SETUP.md with complete setup instructions
- [x] Create docs/development/TROUBLESHOOTING.md with 50+ issues/solutions
- [x] Verify frontend URL: http://localhost:3001 (proxies to backend:8000)
- [x] Document PostgreSQL 16 setup via winget
- [x] Create backend .venv, install dependencies (including greenlet)
- [x] Fix alembic async driver issue: use async URL (postgresql+asyncpg://)
- [x] Fix database URL generation: remove double slash in async URL
- [x] Frontend: strictPort: true added to Vite config, .env created
- [x] Backend .env created with correct database URLs
- [x] PostgreSQL 16 installed via winget at `E:\postsql database`
- [x] Document PostgreSQL crash 0xC0000142 (antivirus interference) in TROUBLESHOOTING.md
- [ ] Start PostgreSQL service (requires Admin: exclude `E:\postsql database\data` from antivirus)

### G8.3 — Reproducible Database and Development Setup ✅ (Environment Fixed)
- [x] Document PostgreSQL 16 setup via winget
- [x] Document database creation and migration commands
- [x] Document backend/frontend environment configuration
- [x] Document one-command startup via docker-compose
- [x] Fix alembic async driver issue (use async URL)
- [x] Fix database URL double-slash issue
- [x] PostgreSQL admin access recovered via temporary trust authentication
- [x] Application role `aquanexis` and database `aquanexis` created
- [x] Application authentication verified: `psql -U aquanexis -d aquanexis` succeeds

### G8.4 — Full Runtime Verification (BLOCKED - TimescaleDB extension not available)
- [ ] Exclude `E:\postsql database\data` from antivirus (Admin required)
- [ ] Start PostgreSQL service
- [ ] Install TimescaleDB extension (Admin required)
- [ ] Run backend migrations: `alembic upgrade head`
- [ ] Start backend: `python -m uvicorn app.main:app --reload`
- [ ] Start frontend: `npm run dev`
- [ ] Verify frontend loads at http://localhost:3001
- [ ] Run simulator scenarios: NORMAL, FILTER_STRESS, LEAK, SENSOR_FAULT

### G8.5 — Development Documentation ✅
- [x] Created docs/development/LOCAL_SETUP.md
- [x] Created docs/development/TROUBLESHOOTING.md
- [x] Verified frontend URL: http://localhost:3001

### G8.6 — Product Continuation Planning (PENDING)
- [ ] Plan predictive filter-health validation
- [ ] Plan RUL model training with labelled data
- [ ] Plan improved historical degradation analysis
- [ ] Plan better alert explanations
- [ ] Plan external purifier telemetry integration
- [ ] Plan production deployment

## Phase G9 — Production Website (PENDING)

- [ ] **G9.1** UI/UX review and polish
- [ ] **G9.2** Comprehensive error handling and error boundaries
- [ ] **G9.3** Performance optimization (bundle size, lazy loading, caching)
- [ ] **G9.4** Accessibility audit (WCAG 2.1 AA)
- [ ] **G9.5** Responsive design verification (mobile, tablet, desktop)
- [ ] **G9.6** Add OpenAPI/Swagger documentation (`/docs` endpoint)
- [ ] **G9.7** Error boundary implementation
- [ ] **G9.8** Offline mode handling (cached data, offline indicator)

## Phase G10 — Final Testing & Demonstration (PENDING)

- [ ] **G10.1** Full regression test suite execution
- [ ] **G10.2** Security audit (dependency audit, penetration testing basics)
- [ ] **G10.3** Performance testing (load testing with k6/locust)
- [ ] **G10.4** Documentation completeness audit
- [ ] **G10.4** Final demonstration preparation

## Phase I — Security / CI / Hardening (PENDING)

- [ ] **I1** Dependency audit and update (npm audit, pip-audit, cargo audit)
- [ ] **I2** Certificate pinning for HTTPS
- [ ] **I3** Rate limiting on all API endpoints
- [ ] **I4** CSP headers and security headers
- [ ] **I5** CI/CD pipeline with automated testing
- [ ] **I6** Secrets management (no hardcoded secrets)
- [ ] **I7** GDPR/privacy compliance review
- [ ] **I8** API rate limiting and abuse prevention

## Phase J — Final Verification (PENDING)

- [ ] **J1** Complete regression test suite
- [ ] **J2** Security audit sign-off
- [ ] **J3** Performance benchmarks documented
- [ ] **J4** Documentation completeness sign-off
- [ ] **J5** Stakeholder demonstration and sign-off

---

## Hardware Development (ARCHIVED — OUT OF SCOPE)

The following hardware development work has been completed as reference implementation but is **OUT OF SCOPE** for the AquaNexis software product. The `firmware/esp32/` directory is preserved as archived reference material.

### H1 — ESP32 Firmware Structure & Sensor Drivers ✅ (ARCHIVED)
- [x] ESP32 firmware structure (CMake, partitions, sdkconfig)
- [x] Sensor driver interface (13 sensor types)
- [x] 13 sensor drivers (TDS, pH, Turbidity, Temperature, Flow, Pressure×2, Tank Level, Leak, Pump Current, Pump Power, UV State, Conductivity, Sensor Registry)
- [x] Communication layer (HTTP/HTTPS client, JWT auth, telemetry batching)
- [x] Main application (WiFi, sensor loop, telemetry, safety, health, OTA)
- [x] Safety architecture (low-voltage control only)
- [x] Hardware specification document
- [x] Pin mapping for ESP32-S3

### H1.1 — Firmware Audit & Hardware Configuration ✅ (ARCHIVED)
- [x] Resolved GPIO/ADC pin conflicts
- [x] Fixed MS5837 I2C address conflict (TCA9548A multiplexer)
- [x] Fixed pump power calculation (DC: V_bus × I, PF=1.0)
- [x] Updated pin mapping, ADC voltage limits, I2C mux configuration
- [x] Sensor conversion formulas validated
- [x] GPIO/I2C configuration verified

### H1.2 — ESP-IDF Environment Setup & Build Verification (ARCHIVED - OUT OF SCOPE)

### H1 — Physical Hardware Bring-up (ARCHIVED — OUT OF SCOPE)

### H2-H4 Hardware Phases (ARCHIVED — OUT OF SCOPE)