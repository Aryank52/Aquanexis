# AquaNexis Open Issues

## Critical Issues (Blocking)

---

## High Priority Issues

### ✅ RESOLVED: G6 Scope Reset
**Resolved**: 2026-11-03
**Phase**: G6
**Details**: 
- Updated all project documentation to reflect software-only scope
- Closed/reclassified all hardware-related issues as OUT OF SCOPE
- Archived firmware/esp32/ directory with clear README
- Updated all project tracking files (PROJECT_STATE.md, PHASE_LEDGER.md, VERIFICATION_LOG.md, OPEN_ISSUES.md, context/memory.md, tasks/task.md)
- Recorded revised software-only product architecture and acceptance criteria
- Firmware directory marked as archived/reference with clear README

---

## High Priority Issues (Software-Only)

### ✅ RESOLVED: SOFTWARE-001 End-to-End Application Validation with Simulator
**Resolved**: 2026-11-03
**Phase**: G7
**Details**: 
- All 8 simulator profiles validated (NORMAL, FILTER_STRESS, HIGH_TURBIDITY, LOW_FLOW, HIGH_PRESSURE_DROP, LEAK, SENSOR_FAULT, DEVICE_OFFLINE)
- Simulator generates valid telemetry with JWT authentication
- Telemetry payloads include all 13 sensor types with provenance tracking
- Device registration and JWT token generation working
- Telemetry payloads validated against backend schema
- All user workflows validated (dashboard, water quality, filter health, diagnostics, alerts, maintenance)
- Data provenance display verified (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED)

### SOFTWARE-002: Analytics Calculations Validation
**Status**: OPEN
**Priority**: HIGH
**Phase**: G8
**Description**: Validate all analytics calculations (AquaScore, FSI, FHI, RUL, purification performance, hydraulic intelligence) against known test cases.
**Resolution**: Create test suite with known inputs and expected outputs for all analytics modules.

### SOFTWARE-003: Production Website Polish
**Status**: OPEN
**Priority**: HIGH
**Phase**: G9
**Description**: Polish UI, add comprehensive error handling, optimize performance, ensure responsive design.
**Resolution**: UI/UX review, error boundary implementation, performance optimization, accessibility audit.

### SOFTWARE-004: Full Regression Testing & Security Audit
**Status**: OPEN
**Priority**: HIGH
**Phase**: G10
**Description**: Complete regression test suite, security audit, penetration testing, dependency audit.
**Resolution**: Run full test suite, run security scanning tools, update dependencies, document findings.

---

## Medium Priority Issues

### ✅ RESOLVED: SOFTWARE-005 WebSocket Reconnection Logic
**Resolved**: 2026-11-03
**Phase**: G7
**Details**:
- WebSocket reconnection uses exponential backoff with jitter (1s initial, max 30s)
- Connection state UI shows: Connected (Live), Reconnecting, Offline
- Cleanup on unmount and logout implemented
- No duplicate subscriptions - single WebSocketManager per device
- Message type mapping fixed: backend "telemetry.updated" → frontend "telemetry", "alert.created" → "alert_created"

### ✅ RESOLVED: SOFTWARE-006 Offline Mode Not Handled
**Resolved**: 2026-11-03
**Phase**: G7
**Details**:
- Offline detection: WebSocket status tracked (connected/reconnecting/disconnected)
- API unreachable detection via TanStack Query error states
- Stale data banner shows when data >30s old, critical warning >2min
- Last update timestamp displayed in dashboard header
- Cached data preserved via TanStack Query cache (staleTime: 5s)
- Automatic recovery when connectivity restored

### ✅ RESOLVED: SOFTWARE-003 Data Provenance Display
**Resolved**: 2026-11-03
**Phase**: G6/G7
**Details**:
- Provenance badges added to Dashboard: SIMULATED (telemetry), CALCULATED (AquaScore), MODEL_PREDICTED (Filter Health/RUL)
- ProvenanceBadge component created with 4 types: MEASURED, SIMULATED, CALCULATED, MODEL_PREDICTED
- Backend schemas updated: SensorReadingResponse, AquaScoreResponse, FilterHealthResponse include provenance field
- Simulator data correctly labeled as SIMULATED provenance
- Analytics correctly labeled: AquaScore=CALCULATED, Filter Health=MODEL_PREDICTED (deterministic fallback)

### SOFTWARE-004: API Documentation Not Generated
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G9
**Description**: No OpenAPI/Swagger UI for backend API documentation.
**Resolution**: Add FastAPI auto-generated docs with `/docs` endpoint.

### SOFTWARE-005: Real-time WebSocket Updates for All Pages
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G7
**Description**: Ensure all pages that display real-time data properly subscribe to WebSocket updates.
**Resolution**: Audit all pages for WebSocket subscription consistency.

---

## Low Priority Issues

### DOCS-001: Firmware Doxygen Comments Incomplete
**Status**: OPEN
**Priority**: LOW
**Phase**: G6 (Archived)
**Description**: Some sensor driver functions lack detailed Doxygen comments.
**Resolution**: Add comprehensive Doxygen comments for all public APIs in archived firmware.

### DOCS-002: API Documentation Not Generated
**Status**: OPEN
**Priority**: LOW
**Phase**: G9
**Description**: No OpenAPI/Swagger UI for backend API documentation.
**Resolution**: Add FastAPI auto-generated docs with `/docs` endpoint.

### TEST-001: No Integration Tests for Firmware
**Status**: OPEN
**Priority**: LOW
**Phase**: N/A (Archived)
**Description**: No hardware-in-loop tests or firmware integration tests in CI.
**Resolution**: Add ESP-IDF unity tests and hardware-in-loop test framework (archived).

### TEST-002: No Load Testing for Backend
**Status**: OPEN
**Priority**: LOW
**Phase**: I
**Description**: No load/stress testing for telemetry ingestion at scale.
**Resolution**: Add k6 or locust load tests to CI.

---

## Resolved Issues (Reference)

### ✅ RESOLVED: TypeScript Errors Across Frontend
**Resolved**: 2026-11-02
**Phase**: G5.1
**Details**: Fixed websocket.ts, Sparkline.tsx, SensorValueCard.tsx, SystemStateBadge.tsx, ui.test.tsx, LoginPage.tsx, LandingPage.tsx

### ✅ RESOLVED: CSS Build Failures
**Resolved**: 2026-11-02
**Phase**: G5.1
**Details**: Rebuilt globals.css to remove @apply conflicts, added dash animation

### ✅ RESOLVED: zodResolver Import Error
**Resolved**: 2026-11-02
**Phase**: G5.1
**Details**: Fixed dynamic import for @hookform/resolvers@3.x compatibility

### ✅ RESOLVED: Frontend Build Failures
**Resolved**: 2026-11-02
**Phase**: G5.1
**Details**: Build now passes with TypeScript strict mode

### ✅ RESOLVED: Backend Safety Endpoints
**Resolved**: 2026-11-02
**Phase**: F
**Details**: All safety endpoints implemented with authorization

### ✅ RESOLVED: Alert State Machine
**Resolved**: 2026-11-02
**Phase**: G1
**Details**: Valid transitions enforced, auto-clear logic implemented

### ✅ RESOLVED: Notification Providers
**Resolved**: 2026-11-02
**Phase**: G3
**Details**: Console, email, webhook with SSRF protection

### ✅ RESOLVED: Maintenance Workflows
**Resolved**: 2026-11-02
**Phase**: G4
**Details**: Filter replacement, calibration, verification, baseline versioning

### ✅ RESOLVED: Frontend API Integration
**Resolved**: 2026-11-02
**Phase**: G5.2
**Details**: All pages connected to real APIs, auth flow, provenance display

### ✅ RESOLVED: ESP32 Firmware Structure
**Resolved**: 2026-11-02
**Phase**: H1
**Details**: Complete firmware with 13 sensor drivers, comm layer, main app

### ✅ RESOLVED: Firmware Audit & Hardware Configuration (H1.1)
**Resolved**: 2026-11-02
**Phase**: H1.1
**Details**: 
- Resolved GPIO/ADC conflicts (GPIO4/5/6/7 conflicts resolved)
- Fixed MS5837 I2C address conflict (TCA9548A multiplexer channels 0/1)
- Fixed pump power calculation (DC: V_bus × I with PF=1.0)
- Updated pin mapping to eliminate GPIO/ADC conflicts
- Added TCA9548A multiplexer for dual MS5837 sensors
- Fixed ADC voltage limits with voltage divider notes
- Updated pump power calculation (DC: V_bus × I, PF=1.0)
- Updated hardware spec with correct pin mapping

### ✅ RESOLVED: Firmware Audit & Hardware Configuration (H1.1)
**Resolved**: 2026-11-03
**Phase**: H1.1
**Details**: 
- Resolved GPIO/ADC conflicts (GPIO4/5/6/7 conflicts resolved)
- Fixed MS5837 I2C address conflict (TCA9548A multiplexer channels 0/1)
- Fixed pump power calculation (DC: V_bus × I with PF=1.0)
- Updated pin mapping to eliminate GPIO/ADC conflicts
- Added TCA9548A multiplexer for dual MS5837 sensors
- Fixed ADC voltage limits with voltage divider notes
- Updated pump power calculation (DC: V_bus × I, PF=1.0)
- Updated hardware spec with correct pin mapping
- Sensor conversion formulas validated
- Sensor range validation added
- GPIO configuration consistency verified
- I2C configuration with TCA9548A multiplexer validated
- Telemetry payload serialization validated
- Network failure/retry behavior validated
- Measurement provenance tracking validated
- Safe failure behavior implemented

---

## Issue Statistics

| Priority | Open | Resolved | Total |
|----------|------|----------|-------|
| CRITICAL | 0 | 0 | 0 |
| HIGH | 4 | 0 | 4 |
| MEDIUM | 5 | 0 | 5 |
| LOW | 4 | 12 | 16 |
| **Total** | **13** | **12** | **25** |

---

## Action Items for Next Sprint

1. **Complete G6 Scope Reset** — Update all documentation, close hardware issues, archive firmware
2. **G7 E2E Validation** — Run full end-to-end tests with simulator
3. **G8 Analytics Validation** — Validate all analytics calculations with known test cases
4. **G9 Production Website** — Polish UI, error handling, performance
4. **G10 Final Testing** — Regression testing, security audit
5. **Phase I** — Security / CI / Hardening
6. **Phase J** — Final Verification