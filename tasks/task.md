# AquaNexis — Task Checklist

**Last Updated**: 2026-11-04

## Current Sprint: Round 2 Final Readiness & System Repair — ✅ COMPLETE

### Completed Phases
- [x] **Slice A** — Runtime Stability ✅
- [x] **Slice B** — Telemetry Foundation ✅
- [x] **Phase C** — Live Dashboard + Alert Lifecycle ✅
- [x] **Phase D** — Water Intelligence + Filter Intelligence ✅
- [x] **Phase E** — Filter Intelligence Enhancement + Model Validation ✅
- [x] **Phase F** — Reliability & Safety (Software Alert & Audit Architecture) ✅
- [x] **Phase G1–G4** — Alert State Machine, Auto-Resolution, Notifications, Maintenance Lifecycle ✅
- [x] **Phase G5** — Frontend Stabilization & API Integration ✅
- [x] **Phase G6** — Scope Reset (Software-Only Prototype; `firmware/esp32/` Archived) ✅
- [x] **Phase G7** — End-to-End Validation (`NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`) ✅
- [x] **Phase G8** — Platform Reliability & Isolated `DEMO_MODE` Runtime ✅

---

## Round 2 Final Engineering Pass Checklist (2026-11-04)

- [x] **Whole-Repository Audit**: Created `ROUND2_SYSTEM_AUDIT.md` covering frontend, backend, simulator, analytics, DB layer, WebSocket, auth, alerts, maintenance, CI, and security.
- [x] **Isolated `DEMO_MODE` Engine**: Implemented `backend/app/infrastructure/demo_mode.py` and `backend/app/api/v1/endpoints/demo_api.py` so FastAPI runs end-to-end without being blocked by local TimescaleDB binary availability.
- [x] **Core Analytics Fixes**:
  - [x] Normalized FSI weights in `backend/app/domain/filter_intelligence.py` to sum to `1.00`.
  - [x] Excluded missing sensors (`differential_pressure`, `flow_deviation`) from `total_weight` in `backend/app/services/filter_stress_service.py`.
  - [x] Fixed `QualityValidator._validate_rate` bug in `backend/app/domain/quality.py`.
  - [x] Exposed `MODEL_MISSING` status explicitly for deterministic RUL fallback and withheld RUL predictions on `SENSOR_FAULT` (`Quality: BAD`, `Confidence: LOW`).
- [x] **Security Fixes**:
  - [x] Added authentication dependencies to `/api/v1/alerts/bulk-transition` and `/api/v1/notifications/worker/stats`.
  - [x] Updated `verify_api_key` in `backend/app/infrastructure/security.py` to support Bearer JWT tokens and `X-API-Key`.
- [x] **Simulator & Reproducible Demo**:
  - [x] Verified `NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`, `HIGH_TURBIDITY`, `LOW_FLOW`, `HIGH_PRESSURE_DROP`, `DEVICE_OFFLINE`.
  - [x] Created `DEMO_RUN.md` with the 12-step reproducible demonstration sequence.
- [x] **Verification**:
  - [x] Frontend `npm run typecheck` (PASS), `npm test -- --run` (14/14 PASS), `npm run build` (PASS).
  - [x] Backend unit tests: 133/133 PASS.
  - [x] Live E2E scenario & WebSocket verification (`NORMAL` → `FILTER_STRESS` → `LEAK` → `SENSOR_FAULT`): PASS.
- [x] **Submission Artifacts**:
  - [x] Updated `VIDEO_SCRIPT.md`, `PROGRESS_REPORT.md`, `SUBMISSION_CHECKLIST.md`, and regenerated `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf` (2 pages, <10 MB).
