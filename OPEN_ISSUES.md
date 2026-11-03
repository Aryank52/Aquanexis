# AquaNexis Open Issues

**Last Updated**: 2026-11-04

---

## Critical Issues (Blocking Round 2 Demo)

*None — All Round 2 software demonstration blockers resolved via isolated `DEMO_MODE` runtime and domain/analytics fixes.*

---

## Resolved Issues in Round 2 Final Engineering Pass (2026-11-04)

### ✅ RESOLVED: G8-003 Local Runtime Blocked by Missing TimescaleDB Extension
- **Resolution**: Implemented isolated `DEMO_MODE=true` (`backend/app/infrastructure/demo_mode.py` and `backend/app/api/v1/endpoints/demo_api.py`) backed by the real `SimulatorState` and domain/analytics services (`QualityValidator`, `WaterQualityService`, `FilterStressService`, `FilterHealthService`, `RULService`, `FailureRiskService`, `HydraulicService`, `PurificationService`, `CompatibilityEngine`), while preserving the PostgreSQL/TimescaleDB architecture intact.

### ✅ RESOLVED: SOFTWARE-002 Analytics & Domain Integrity Audit
- **Resolution**:
  - Normalized `FSIConfigVersion` weights in `backend/app/domain/filter_intelligence.py` to sum to `1.00`.
  - Fixed `FilterStressService` (`backend/app/services/filter_stress_service.py`) so missing `differential_pressure` or `flow_deviation` sensors are excluded from `total_weight` rather than scored as a false `0.0`.
  - Fixed `QualityValidator._validate_rate` (`backend/app/domain/quality.py`) `NameError: name 'payload' is not defined`.
  - Fixed `backend/app/domain/safety.py` dataclass field ordering and duplicate class definitions across `safety_service.py`, `leak_protection.py`, `pressure_protection.py`, `flow_protection.py`, and `energy_protection.py`.
  - Explicitly surfaced `MODEL_MISSING` status for RUL estimation and prevented `SENSOR_FAULT` (`Quality: BAD`) from producing confident predictions.

### ✅ RESOLVED: SEC-001 Unauthenticated Endpoints & API Key / Bearer Token Alignment
- **Resolution**: Added authentication dependencies to `/api/v1/alerts/bulk-transition` and `/api/v1/notifications/worker/stats`, and updated `verify_api_key` in `backend/app/infrastructure/security.py` to accept valid Bearer JWTs from logged-in frontend sessions as well as `X-API-Key`.

---

## Open Non-Blocking / Post-Round-2 Items

### 1. INFRA-001: Local Windows TimescaleDB Binary Extension
- **Priority**: MEDIUM (Post-Round-2 / Docker Deployment)
- **Status**: DOCUMENTED WORKAROUND (`DEMO_MODE=true` active for local Windows without Docker)
- **Details**: Migration `0002_create_hypertables.py` requires the `timescaledb` extension, which is not bundled with winget PostgreSQL 16 on Windows. Use `docker compose up` (`timescale/timescaledb:latest-pg16`) or `DEMO_MODE=true`.

### 2. ML-001: Trained RUL Machine Learning Artifact (`.pkl`)
- **Priority**: MEDIUM (Round 3 Roadmap)
- **Status**: DISCLOSED (`MODEL_MISSING`)
- **Details**: RUL currently uses the deterministic engineering fallback (`v1.0`) and explicitly displays `MODEL_MISSING` in the UI and API. Training a Random Forest / XGBoost model on labeled filter run-to-failure telemetry is scheduled for Round 3.

### 3. LINT-001: Pre-existing Frontend ESLint Technical Debt
- **Priority**: LOW
- **Status**: OPEN (Non-blocking; TypeScript `tsc --noEmit`, unit tests, and production `vite build` pass with 0 errors)
- **Details**: Pre-existing `@typescript-eslint/no-unused-vars` and `@typescript-eslint/no-explicit-any` warnings across secondary UI components.

### 4. HW-001: Physical Purifier / ESP32 Hardware Integration
- **Priority**: OUT OF SCOPE (Archived)
- **Status**: ARCHIVED in `firmware/esp32/`
