# AquaNexis Open Issues

## Critical Issues (Blocking)

---

## High Priority Issues

### G6-001: Scope Reset Documentation Incomplete
**Status**: OPEN
**Priority**: CRITICAL
**Phase**: G6
**Description**: Need to complete scope reset documentation, update all project tracking files, and communicate the new software-only direction.
**Resolution**: Complete all documentation updates and ensure all tracking files reflect software-only scope.

### G6-002: Firmware Directory Marked as Archived/Reference
**Status**: OPEN
**Priority**: HIGH
**Phase**: G6
**Description**: The `firmware/esp32/` directory needs to be clearly marked as archived/reference material with README explaining it's out of scope.
**Resolution**: Add README to firmware/esp32/ directory explaining archived status.

### G6-003: Hardware-Related Open Issues Need Reclassification
**Status**: OPEN
**Priority**: HIGH
**Phase**: G6
**Description**: Multiple open issues (HARDWARE-001, HARDWARE-002, HARDWARE-003, FIRMWARE-001 through FIRMWARE-008, SECURITY-001, SECURITY-002) are hardware-related and need to be closed or reclassified as OUT OF SCOPE.
**Resolution**: Close hardware-related issues with "OUT OF SCOPE" status, create new software-only issues if needed.

---

## High Priority Issues (Software-Only)

### SOFTWARE-001: End-to-End Application Validation with Simulator
**Status**: OPEN
**Priority**: HIGH
**Phase**: G7
**Description**: Complete end-to-end validation of the entire application using the Python simulator as the data source.
**Resolution**: Run full E2E test suite covering all user workflows with simulated telemetry data.

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

### SOFTWARE-005: WebSocket Reconnection Logic
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G7
**Description**: WebSocket reconnection uses simple retry. No exponential backoff or connection state UI.
**Resolution**: Implement proper reconnection with exponential backoff and connection status indicator.

### SOFTWARE-002: Offline Mode Not Handled
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G7
**Description**: Frontend shows errors when backend unreachable. No cached data display or offline indicator.
**Resolution**: Add offline detection, cached data display, and sync indicator.

### SOFTWARE-003: Data Provenance Display
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G6
**Description**: Ensure all data points clearly show provenance (MEASURED/SIMULATED/CALCULATED/MODEL_PREDICTED) in UI.
**Resolution**: Add provenance badges/indicators to all data display components.

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