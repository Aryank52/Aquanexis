# AquaNexis Phase Ledger

## Phase Summary

| Phase | Name | Status | Start Date | End Date | Tests |
|-------|------|--------|------------|----------|-------|
| A | Runtime Stability | ✅ COMPLETE | 2026-10-31 | 2026-10-31 | 14 |
| B | Telemetry Foundation | ✅ COMPLETE | 2026-10-31 | 2026-10-31 | 36 |
| C | Live Dashboard + Alert Lifecycle | ✅ COMPLETE | 2026-11-01 | 2026-11-01 | 49 |
| D | Water Intelligence + Filter Intelligence | ✅ COMPLETE | 2026-11-01 | 2026-11-01 | 36 |
| E | Filter Intelligence Enhancement + Model Validation | ✅ COMPLETE | 2026-11-01 | 2026-11-01 | 36 |
| F | Reliability & Safety | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 36 |
| G1 | Alert State Machine Enforcement | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 28 |
| G2 | Auto-resolution for Self-Clearing Alerts | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 19 |
| G3 | Notification Providers + Queue | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 22 |
| G4 | Maintenance & Filter Lifecycle | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 28 |
| G5.1 | Frontend Stabilization | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 14 |
| G5.2 | Frontend API Integration | ✅ COMPLETE | 2026-11-02 | 2026-11-02 | 14 |
| **G6** | **Scope Reset (Software-Only)** | ✅ **COMPLETE** | **2026-11-03** | **2026-11-03** | **N/A** |
| **G7** | **E2E Validation (`NORMAL` / `FILTER_STRESS` / `LEAK` / `SENSOR_FAULT`)** | ✅ **COMPLETE** | **2026-11-03** | **2026-11-04** | **147** |
| **G8** | **Platform Reliability & Round 2 `DEMO_MODE` Readiness** | ✅ **COMPLETE** | **2026-11-03** | **2026-11-04** | **147** |
| **H (Hardware/ESP32)** | **OUT OF SCOPE** | 📦 **ARCHIVED** | — | — | — |

---

## Round 2 Final Engineering Pass (2026-11-04)

1. **Whole-Repository System Audit (`ROUND2_SYSTEM_AUDIT.md`)**:
   - Audited backend, frontend, simulator, domain analytics, database migrations, WebSocket, security, and CI workflows.
   - Fixed domain bugs in `app/domain/quality.py` (`NameError` in `_validate_rate`), `app/domain/safety.py` (dataclass field ordering and duplicate definitions), `app/domain/filter_intelligence.py` (normalized FSI weights to `1.00`), and `app/services/filter_stress_service.py` (missing sensors excluded from `total_weight` rather than scored as zero; actual kPa differential stored).
   - Fixed security gaps by enforcing authentication on `/api/v1/alerts/bulk-transition` and `/api/v1/notifications/worker/stats`, and supporting Bearer JWT in `verify_api_key`.
2. **Isolated `DEMO_MODE` Runtime (`app/infrastructure/demo_mode.py` & `app/api/v1/endpoints/demo_api.py`)**:
   - Implemented full in-memory simulator-backed engine so Round 2 demonstration runs reliably without requiring local TimescaleDB installation, while keeping PostgreSQL/TimescaleDB code and migrations intact.
   - Connected live scenario switching (`NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`) via both header UI (`Layout.tsx`) and `backend/simulator.py`.
3. **Frontend & Explainability Repairs**:
   - Fixed `LoginPage.tsx` `useAuth` import, added `sessionStorage` auth persistence, added `MODEL_MISSING` disclosure badges and `Quality: GOOD/SUSPECT/BAD` indicators on `DashboardPage.tsx` and `FilterHealthPage.tsx`, and enabled `OPEN` alert acknowledgment and evidence inspection in `AlertsPage.tsx` and `AlertEvidenceDrawer.tsx`.
4. **Verification Summary**:
   - Backend unit tests: **133 passed** (`0` failures in non-DB unit test suites).
   - Frontend checks: `npm run typecheck` **PASS**, `npm test -- --run` **14/14 PASS**, `npm run build` **PASS**.
   - Live E2E verification across `NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`, alert acknowledgment, maintenance recommendations, and WebSocket `/ws/realtime/{device_id}`: **PASS**.
