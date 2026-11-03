# AquaNexis — Round 2 Whole-Repository System Audit

**Audit Date**: 4 November 2026  
**Target**: AtomQUEST 2026 — Round 2 Prototype Readiness (Track 2: Water Purifier)  
**Institution**: UPES Dehradun (Solo Prototype)  
**Product Scope**: Software-Only Predictive Water Intelligence System

---

## 1. Repository Architecture Map

```text
Repository (e:\PROJECTS\Aquanexis)
├── frontend/                   # React 18 + TypeScript + Vite + Tailwind + TanStack Query
│   ├── src/api/                # Axios client, REST endpoint wrappers, WebSocket manager
│   ├── src/app/                # App shell, router, Layout
│   ├── src/components/         # UI primitives, gauges, sparklines, ProvenanceBadge, AlertEvidenceDrawer
│   ├── src/hooks/              # React Query hooks (dashboard, water quality, filter health, alerts, etc.)
│   ├── src/pages/              # 12 route pages + auth pages
│   ├── src/state/ & context/   # Auth state & theme context
│   └── src/types/              # TypeScript API contracts (api.ts)
├── backend/                    # FastAPI + Pydantic v2 + SQLAlchemy 2.0 (Async)
│   ├── app/api/v1/             # REST routers (telemetry, dashboard, water_quality, filter_health, alerts, etc.)
│   ├── app/domain/             # Domain models & QualityValidator
│   ├── app/services/           # Analytics (FSI, FHI, RUL, FailureRisk, AquaScore, Hydraulic, Safety, Alerts, Maintenance)
│   ├── app/infrastructure/     # Config, Database, Security (JWT/API key), Logging, WebSocket manager
│   ├── app/models/ & schemas/  # SQLAlchemy ORM models & Pydantic schemas
│   ├── alembic/                # Migrations 0001–0008 (0002 requires TimescaleDB extension)
│   ├── simulator.py            # 8-profile synthetic telemetry generator & HTTP client
│   └── tests/unit/             # 133 unit tests
├── docs/                       # PRD, TRD, Architecture, Schema, Local Setup, Troubleshooting
├── .github/workflows/          # CI pipelines (backend, frontend, integration, docker)
├── firmware/esp32/             # ARCHIVED C/ESP-IDF reference drivers (OUT OF SCOPE)
└── Root Submission Artifacts   # PROGRESS_REPORT.md, VIDEO_SCRIPT.md, SUBMISSION_CHECKLIST.md, Report PDF
```

---

## 2. Subsystem Status Classification

| Subsystem | Current Status | Classification | Key Findings |
| :--- | :--- | :--- | :--- |
| **PostgreSQL / TimescaleDB** | 🔴 Blocked | Infrastructure Blocker | Local PostgreSQL 16 lacks the `timescaledb` extension required by migration `0002_timescale_hypertables.py`, and Windows Defender triggers `0xC0000142` DLL init crashes on the local PG data dir. Additionally, `init_db()` in `main.py` fails hard on startup if DB is unavailable. |
| **Backend Startup & Routing** | 🔴 Broken at Runtime | Repair Required | `backend/app/api/v1/router.py` adds prefixes (`/telemetry`, `/alerts`, `/devices`, etc.) to sub-routers that already declare the same `prefix` internally, doubling all paths (`/api/v1/devices/devices/...`). |
| **Dashboard Endpoint (`dashboard.py`)** | 🔴 Broken at Runtime | Repair Required | `get_dashboard` is duplicated 3 times; references `data_freshness_seconds` before assignment (`UnboundLocalError`); references `AquaScoreResponse` without importing it (`NameError`); accesses ORM attributes on Pydantic objects (`AttributeError`). |
| **Derivation Pipeline** | 🔴 Stubbed | Repair Required | `derive_and_persist()` in `telemetry.py` and `derivation_service.py` is a no-op stub that logs messages without computing or storing AquaScore, FSI, FHI, RUL, Diagnostics, or Purification Performance. |
| **Core Analytics (FSI, FHI, RUL, Risk, AquaScore)** | 🟡 Mostly Working (Pure Python) | Minor Fixes Required | Pure Python services (`FilterStressService`, `FilterHealthService`, `RULService`, `FailureRiskService`, `WaterQualityService`, `HydraulicService`, `PurificationService`) work without a DB and pass 133 unit tests. However: (1) `FilterStressService` weights sum to `1.05` and include missing sensor weights in `total_weight` (scoring missing sensors as `0.0`); (2) `FilterStressService` assigns the 0–100 score instead of actual kPa to `pressure_differential_kpa`; (3) `QualityValidator._validate_rate` references an undefined `payload` variable when `previous_reading` is present; (4) `RULService` has no trained `.pkl` artifact and properly returns `MODEL_MISSING` deterministic fallback. |
| **Safety Services** | 🔴 Broken at Runtime | Repair Required | `leak_protection.py`, `pressure_protection.py`, `flow_protection.py`, and `energy_protection.py` each have a duplicate class definition at the bottom of the file that instantiates itself recursively (`RecursionError`). |
| **Authentication (Frontend ↔ Backend)** | 🔴 Mismatched | Repair Required | `LoginPage.tsx` imports `useAuth` from `@/context/AuthContext` while `App.tsx` mounts `AuthProvider` from `@/state/auth.tsx` (crashing `/login`). Frontend calls `/api/v1/auth/login`, `/auth/logout`, `/auth/refresh`, which do not exist on the backend. Session state is lost on browser refresh. |
| **Frontend ↔ Backend API Contracts** | 🔴 Mismatched | Repair Required | Frontend `endpoints.ts` requests `/api/v1/devices/{id}/water-quality`, `/devices/{id}/filter-health`, `/devices/{id}/diagnostics`, `/devices/{id}/alerts`, `/devices/{id}/telemetry/latest`, etc., and expects uppercase enums (`GOOD`, `CRITICAL`, `SIMULATED`) and nested structures (`readings`, `pressure`, `flow`, `leak`), whereas backend endpoints use different paths and lowercase/flat schemas. |
| **WebSocket Real-Time Updates** | 🟡 Partially Working | Path & Payload Alignment Needed | Frontend connects to `/ws/realtime/{deviceId}` while backend listens on `/ws/devices/{device_id}`. Reconnection backoff and cleanup on unmount are properly implemented in `frontend/src/api/websocket.ts`. |
| **Simulator (`backend/simulator.py`)** | 🟢 Working (Generator) | Ready for `DEMO_MODE` | All 8 profiles (`NORMAL`, `FILTER_STRESS`, `HIGH_TURBIDITY`, `LOW_FLOW`, `HIGH_PRESSURE_DROP`, `LEAK`, `SENSOR_FAULT`, `DEVICE_OFFLINE`) generate synthetic 13-sensor telemetry. In `LEAK` and `SENSOR_FAULT` profiles, fault injection probability was set to 1–2% per reading (too low for deterministic short demos) and should trigger deterministically during scenario runs. |
| **Frontend Build & Unit Tests** | 🟢 Working | Verified | `npm run typecheck`, `npm run build`, and `npm test -- --run` (14/14 tests) pass. ESLint has pre-existing lint warnings/errors documented as non-blocking technical debt. |
| **ESP32 Firmware (`firmware/esp32/`)** | 📦 Archived | Out of Scope | Reference C code only; no physical ESP32, sensors, relays, or purifier hardware exists. |

---

## 3. What Is Mock/Simulated vs Production-Like vs Unsafe to Claim

### Production-Like Software Components
- **Domain & Analytics Engine**: Multi-parameter `WaterQualityService` (AquaScore 0–100, trend slopes, z-score anomaly detection), `FilterStressService` (7-factor stress model), `FilterHealthService` (5-factor health index + maintenance bands), `RULService` (explicit `MODEL_MISSING` deterministic fallback with confidence intervals and counterfactual analysis), `FailureRiskService`, `HydraulicService`, `PurificationService`, and `AlertStateMachine` (enforced state transitions, audit history, self-clearing vs manual-only alert codes).
- **Frontend Architecture**: React 18 + TypeScript strict mode, TanStack Query cache management, WebSocket reconnection with exponential backoff + jitter, stale-data detection banners, and explicit `ProvenanceBadge` (`MEASURED`, `SIMULATED`, `CALCULATED`, `MODEL_PREDICTED`).

### Simulated / Demo-Backed Components
- **All Sensor Telemetry**: 100% synthetic telemetry generated by `backend/simulator.py` across 13 virtual sensor channels (`SIMULATED` provenance).
- **Runtime Persistence (`DEMO_MODE`)**: Because local PostgreSQL lacks the `timescaledb` extension, Round 2 demonstration uses an explicit, isolated `DEMO_MODE` repository/state layer in FastAPI backed by the simulator and real domain/analytics services.
- **Safety Actions**: Logged software protection events and commands (`close_inlet_valve`, `stop_pump`); no physical actuators exist.

### Unsafe to Claim (Must Never Be Claimed)
- Physical water purifier hardware, ESP32 deployment, or physical sensor measurements.
- Physical relay/valve/pump shutdown.
- Trained ML model accuracy (e.g., RUL MAE ≤ 7 days) — no `.pkl` model is trained on real filter run-to-failure data; RUL uses the deterministic engineering fallback (`status: MODEL_MISSING`).
- Live TimescaleDB hypertable verification in the local Windows environment.
- Regulatory water potability certification.

---

## 4. Security Audit Findings Identified

1. **Config Env-Prefix Mismatch (`backend/app/infrastructure/config.py`)**: Nested `Pydantic Settings` classes (`AuthSettings`, `DatabaseSettings`, `MLSettings`, `NotificationSettings`) used mismatched prefixes (`AUTH_`, `NOTIFY_`) without `env_file=".env"`, causing `.env` secrets (`DEVICE_JWT_SECRET`) to be ignored in favor of default test strings.
2. **Unauthenticated Endpoints**: `/alerts/bulk-transition` and `/notifications/worker/stats` lacked authentication dependencies; `/ws/devices/{device_id}` did not validate tokens when provided.
3. **Hardcoded Dev Fallback**: Development API key fallback must only be active when `APP_ENV=development` or `DEMO_MODE=true`, never in `production`.
4. **Frontend XSS / Secret Exposure**: No `dangerouslySetInnerHTML` or `eval` found; `.env` is ignored by `.gitignore`; CORS is restricted to `localhost:3000` and `localhost:5173`.

---

## 5. Action Plan for Round 2 Readiness

1. **Analytics & Domain Repairs**:
   - Fix `FilterStressService` weight normalization (sum = `1.00`, exclude missing sensors from denominator instead of scoring missing data as confident `0.0`, fix `pressure_differential_kpa` kPa value, check both `inlet_pressure` and `pressure`).
   - Fix `QualityValidator._validate_rate` undefined `payload` variable and ensure `SENSOR_FAULT` readings produce `SUSPECT`/`BAD` quality flags and degrade prediction confidence.
   - Remove recursive duplicate class definitions in `leak_protection.py`, `pressure_protection.py`, `flow_protection.py`, `energy_protection.py`, and `safety_service.py`.
2. **Backend `DEMO_MODE` & Contract Alignment**:
   - Add explicit `DEMO_MODE=true` support in `config.py` and `main.py` so FastAPI starts cleanly without PostgreSQL/TimescaleDB while preserving the PostgreSQL/TimescaleDB code path intact.
   - Fix double prefixes in `backend/app/api/v1/router.py`.
   - Provide a complete, simulator-backed `DEMO_MODE` state engine that runs real `QualityValidator`, `WaterQualityService`, `FilterStressService`, `FilterHealthService`, `RULService`, `FailureRiskService`, `HydraulicService`, `PurificationService`, `AlertStateMachine`, and `SafetyService` on every simulator tick or ingested reading, broadcasting live updates over WebSocket (`/ws/realtime/{device_id}` and `/ws/devices/{device_id}`).
   - Add `/api/v1/auth/login`, `/api/v1/auth/logout`, `/api/v1/auth/refresh`, `/api/v1/auth/me` and simulator scenario control endpoints (`/api/v1/demo/scenario`) so the frontend and `simulator.py` work seamlessly.
   - Align all `/api/v1/devices/{device_id}/*`, `/api/v1/alerts/*`, `/api/v1/maintenance/*`, `/api/v1/notifications/*`, `/api/v1/health`, and `/api/v1/ready` response shapes with the frontend TypeScript contracts.
3. **Frontend Fixes**:
   - Unify `AuthContext` (`LoginPage.tsx` → `@/state/auth`) and persist demo/operator session in `sessionStorage` so page refreshes do not kick the user out during the demo.
   - Fix minor UI bugs (`FilterHealthPage` risk score percentage & evidence rendering, `AlertEvidenceDrawer` object rendering, `FilterCatalogPage` modal state) and add an interactive Demo Scenario Switcher bar (`NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`) in the layout header when running in `DEMO_MODE` (in addition to supporting CLI `python backend/simulator.py --profile <profile>`).
4. **Verification & Documentation**:
   - Verify all 4 scenarios (`NORMAL`, `FILTER_STRESS`, `LEAK`, `SENSOR_FAULT`) end-to-end against the live backend and browser.
   - Run frontend (`typecheck`, `test`, `build`) and backend (`pytest`) test suites.
   - Update `DEMO_RUN.md`, `docs/development/LOCAL_SETUP.md`, `PROGRESS_REPORT.md`, `SUBMISSION_CHECKLIST.md`, `VIDEO_SCRIPT.md`, and regenerate `atomQUEST2026_AquaNexis_UPESDehradun_Track2_Report.pdf` (1–2 pages, no `[Participant Name]` placeholder issues).

