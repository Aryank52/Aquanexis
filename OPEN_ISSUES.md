# AquaNexis Open Issues

## Critical Issues (Blocking)

### HARDWARE-001: Physical ESP32 Hardware Not Available
**Status**: OPEN
**Priority**: CRITICAL
**Phase**: H1-Physical
**Description**: No physical ESP32-S3 hardware or sensors available for testing. All firmware development has been done against the Python simulator only.
**Impact**: Cannot validate sensor readings, safety actions, or communication with real hardware.
**Resolution**: Procure ESP32-S3 development board and all required sensors.

### HARDWARE-002: Sensor Calibration Procedures Unverified
**Status**: OPEN
**Priority**: CRITICAL
**Phase**: H1-Physical
**Description**: All calibration procedures documented but not physically tested. Actual sensor behavior may differ from simulator.
**Impact**: Production devices may report incorrect values without proper calibration.
**Resolution**: Execute all calibration procedures with physical hardware.

### HARDWARE-003: Safety Action Validation with Relays
**Status**: OPEN
**Priority**: CRITICAL
**Phase**: H1-Physical
**Description**: Safety actions (valve close, pump stop, relief valve) only tested in simulator. Need validation with actual relay board.
**Impact**: Safety system may not function correctly in real emergency.
**Resolution**: Test all 4 safety actions with relay board and verify timing.

---

## High Priority Issues

### FIRMWARE-001: ESP-IDF Build Environment Not Verified
**Status**: OPEN (BLOCKED - Manual install required)
**Priority**: HIGH
**Phase**: H1
**Description**: Firmware CMakeLists.txt created but not built with ESP-IDF. Potential compilation issues with ESP-IDF v5.x.
**Resolution**: Set up ESP-IDF v5.x environment and build firmware.
**Blocker**: ESP-IDF v5.x not installed. Manual install required: Download `esp-idf-tools-setup.exe` from https://github.com/espressif/esp-idf-tools/releases/latest, install with ESP-IDF v5.2, target ESP32-S3.

### FIRMWARE-002: OTA Update Mechanism Not Implemented
**Status**: OPEN
**Priority**: HIGH
**Phase**: H1
**Description**: OTA check task exists but actual firmware update logic not implemented.
**Resolution**: Implement OTA firmware download, validation, and rollback.

### FIRMWARE-003: Offline Telemetry Buffering Not Implemented
**Status**: OPEN
**Priority**: HIGH
**Phase**: H1
**Description**: Telemetry batching exists but no persistent storage for offline operation.
**Resolution**: Implement SPIFFS/NVS buffering with sequence numbers for replay protection.

### FIRMWARE-004: Time Synchronization (NTP) Not Implemented
**Status**: OPEN
**Priority**: HIGH
**Phase**: H1
**Description**: Device relies on backend timestamps but no local NTP sync for accurate local timestamps.
**Resolution**: Add NTP client with periodic sync and fallback to backend time.

### SECURITY-001: Device Provisioning Flow Not Implemented
**Status**: OPEN
**Priority**: HIGH
**Phase**: H2
**Description**: No device claiming/registration flow for end users. Devices must be pre-registered via admin API.
**Resolution**: Implement QR code / BLE provisioning flow with user app.

### SECURITY-002: Certificate Pinning Not Implemented
**Status**: OPEN
**Priority**: HIGH
**Phase**: H1
**Description**: HTTPS client uses system CA store without certificate pinning for backend API.
**Resolution**: Add certificate pinning or custom CA bundle for production.

---

## Medium Priority Issues

### FIRMWARE-005: Sensor Self-Test Coverage Incomplete
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: H1
**Description**: Self-test methods exist but only check basic communication. No validation of sensor accuracy ranges.
**Resolution**: Add range checks and known-value verification to self-tests.

### FIRMWARE-006: No Watchdog for Sensor Tasks
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: H1
**Description**: Sensor reading task has no dedicated watchdog. If task hangs, no automatic recovery.
**Resolution**: Add task watchdog with automatic restart.

### FIRMWARE-007: Power Management Not Implemented
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: H3
**Description**: No deep sleep or power management for battery/solar deployments.
**Resolution**: Add light sleep between readings, configurable intervals.

### FIRMWARE-008: Configuration via BLE/Serial Not Implemented
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: H2
**Description**: WiFi credentials and device config must be set via NVS or compile-time. No runtime config.
**Resolution**: Add BLE GATT service for WiFi provisioning and config.

### FRONTEND-001: Real-time WebSocket Reconnection Logic
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G5.2
**Description**: WebSocket reconnection uses simple retry. No exponential backoff or connection state UI.
**Resolution**: Implement proper reconnection with backoff and connection status indicator.

### FRONTEND-002: Offline Mode Not Handled
**Status**: OPEN
**Priority**: MEDIUM
**Phase**: G5.2
**Description**: Frontend shows errors when backend unreachable. No cached data display or offline indicator.
**Resolution**: Add offline detection, cached data display, and sync indicator.

---

## Low Priority Issues

### DOCS-001: API Documentation Not Generated
**Status**: OPEN
**Priority**: LOW
**Phase**: J
**Description**: No OpenAPI/Swagger UI for backend API documentation.
**Resolution**: Add FastAPI auto-generated docs with `/docs` endpoint.

### DOCS-002: Firmware Doxygen Comments Incomplete
**Status**: OPEN
**Priority**: LOW
**Phase**: H1
**Description**: Some sensor driver functions lack detailed Doxygen comments.
**Resolution**: Add comprehensive Doxygen comments for all public APIs.

### TEST-001: No Integration Tests for Firmware
**Status**: OPEN
**Priority**: LOW
**Phase**: H4
**Description**: No hardware-in-loop tests or firmware integration tests in CI.
**Resolution**: Add ESP-IDF unity tests and hardware-in-loop test framework.

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

---

## Issue Statistics

| Priority | Open | Resolved | Total |
|----------|------|----------|-------|
| CRITICAL | 3 | 0 | 3 |
| HIGH | 6 | 0 | 6 |
| MEDIUM | 6 | 0 | 6 |
| LOW | 4 | 0 | 4 |
| **Total** | **19** | **12** | **31** |

---

## Action Items for Next Sprint

1. **Procure hardware** for H1-Physical bring-up
2. **Set up ESP-IDF build environment** and compile firmware
3. **Implement NTP time sync** in firmware
4. **Add persistent telemetry buffering** (SPIFFS)
5. **Implement certificate pinning** for HTTPS
6. **Create device provisioning flow** (BLE/QR)
7. **Add hardware watchdog** for sensor tasks
8. **Implement OTA firmware update** with rollback