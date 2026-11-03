# AquaNexis — Post-Round 2 Production & Release Checklist

**Track**: Track 2 — Water Purifier | **System**: Predictive Water Intelligence System  
**Institution**: UPES Dehradun  
**Date**: November 2026  

---

## 1. Pre-Flight Verification Checklist

| Category | Verification Item | Status | Verification Evidence / Command |
| :--- | :--- | :---: | :--- |
| **Demo Protection** | Backend starts cleanly on `:8000` | ✅ PASS | `uvicorn app.main:app --port 8000` → `/health` 200 OK |
| **Demo Protection** | Frontend starts cleanly on `:3000` | ✅ PASS | `npm run dev` → `http://localhost:3000` accessible |
| **Demo Protection** | `DEMO_MODE=true` operational | ✅ PASS | Scenario switcher drives NORMAL / FILTER_STRESS / LEAK / SENSOR_FAULT |
| **Code Quality** | Backend Ruff linting & formatting | ✅ PASS | `ruff check app` (0 errors), `ruff format --check app` (0 errors) |
| **Code Quality** | Frontend ESLint & Prettier | ✅ PASS | `npm run lint` (0 errors, 0 warnings), `npm run format:check` |
| **Type Safety** | Frontend TypeScript Typecheck | ✅ PASS | `npm run typecheck` (`tsc --noEmit` exits code 0) |
| **Testing** | Backend Unit Test Suite | ✅ PASS | `pytest tests/unit -v` (154 passed, 11 skipped) |
| **Testing** | Frontend Vitest Component Suite | ✅ PASS | `npm test -- --run` (14 passed) |
| **Testing** | Integration & TimescaleDB Pipeline | ✅ PASS | Configured in `.github/workflows/integration-e2e.yml` |
| **Telemetry** | Unified Canonical Wire Contract | ✅ PASS | `backend/app/domain/canonical_telemetry.py` (MEASURED vs SIMULATED) |
| **Device Security** | Replay & Sequence Validation | ✅ PASS | Monotonic sequence enforcement, clock-skew ±300s window |
| **Device Security** | Device Authentication & Scoping | ✅ PASS | Device token claims validated, mismatched IDs rejected with 403 |
| **Prognostics** | Versioned RUL Dataset Generator | ✅ PASS | `controlled-membrane-deg-v1.0` (600 samples, 15 physical features) |
| **Prognostics** | Multivariate RUL Model Artifact | ✅ PASS | `backend/app/models/rul_model.pkl` (Candidate Test MAE: 4.85 days) |
| **Prognostics** | Calibrated Uncertainty Interval | ✅ PASS | $\pm 1.96 \times \text{MAE} = \pm 9.5\text{ days}$ (95% coverage) |
| **Safety Logic** | Actuator Verification & Fallback | ✅ PASS | Actuator commands logged, safe default state enforced |
| **CI/CD** | Workflow Consolidation | ✅ PASS | Exactly 4 clean workflows: `backend-ci`, `frontend-ci`, `integration-e2e`, `docker` |
| **Documentation** | Honest Engineering Disclosures | ✅ PASS | Clear separation of physical vs simulated telemetry |

---

## 2. Release Gate Decision

- [x] **GO FOR PRODUCTION RELEASE STAGING**: All tests passing, demo intact, zero fabricated hardware claims, explicit provenance badges active.

