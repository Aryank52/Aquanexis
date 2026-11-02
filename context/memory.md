# AquaNexis Project Memory

## Durable Project Facts

### 2026-10-31 — Project Initialization
- Repository created from scratch
- Specification defined in master prompt
- Tech stack decision: FastAPI + PostgreSQL + React + ESP32
- No existing code, migrations, or data

### Architecture Decisions
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-10-31 | FastAPI for backend | Modern, async, OpenAPI native, type-safe |
| 2026-10-31 | PostgreSQL for persistence | ACID, JSONB for flexible telemetry, TimescaleDB-ready |
| 2026-10-31 | React + TanStack Query | Server state management, caching, deduping |
| 2026-10-31 | Alembic for migrations | Version-controlled schema evolution |
| 2026-10-31 | Deterministic ML first | No dataset yet; statistical baselines are auditable |
| 2026-10-31 | Safety as separate subsystem | Isolation from business logic; auditability |
| 2026-11-01 | Phase E: Filter Intelligence Enhancement | Centralized config, baselines, model registry, explainability |
| 2026-11-02 | Phase F: Reliability & Safety | Leak, pressure, flow, pump protection with validated actions |
| 2026-11-02 | Phase G: Maintenance & Lifecycle | Alert state machine, auto-resolution, maintenance workflows |

### Implementation Status
- **Slice A (Runtime Stability)**: ✅ COMPLETE
- **Slice B (Telemetry Foundation)**: ✅ COMPLETE
- **Phase C (Live Dashboard + Alert Lifecycle)**: ✅ COMPLETE
- **Phase D (Water Intelligence + Filter Intelligence)**: ✅ COMPLETE
- **Phase E (Filter Intelligence Enhancement + Model Validation)**: ✅ COMPLETE
- **Phase F (Reliability & Safety)**: ✅ COMPLETE
- **Phase G (Maintenance & Lifecycle)**: 🔄 IN PROGRESS (G1 complete)
- **Phase H (Hardware / ESP32)**: ⏳ PENDING
- **Phase I (Security / CI / Hardening)**: ⏳ PENDING
- **Phase J (Final Verification)**: ⏳ PENDING

### Known Constraints
1. No physical hardware yet — simulator required for development
2. No historical dataset — ML baselines must be deterministic/statistical
3. Single developer — vertical slices must be independently testable
4. Production deployment target: containerized (Docker Compose / k8s)

### Open Questions
- [ ] Notification provider selection (email/SMS/push)
- [ ] Device provisioning flow (claiming, JWT issuance)
- [ ] TimescaleDB vs vanilla PostgreSQL for time-series
- [ ] WebSocket vs Server-Sent Events for real-time UI
- [ ] Chart library selection (Recharts vs Chart.js vs uPlot)

### Completed Work
- Slice A: Runtime stability (config, health endpoints, logging, auth, Docker, CI)
- Slice B: Telemetry foundation (device registry, ingestion, validation, simulator, migrations 0001-0004)
- Phase C: Live Dashboard + Alert Lifecycle (alerts table, state machine, WebSocket, alert evaluation in ingestion)
- Phase D: Water Intelligence + Filter Intelligence (AquaScore, purification performance, hydraulic intelligence, FSI, FHI, RUL, failure risk, explanations, API endpoints, 36 unit tests passing)
- Phase E: Filter Intelligence Enhancement + Model Validation (FSI versioning, baselines, ΔP first-class, FHI with maintenance bands, RUL with model registry/stability/confidence, counterfactuals, maintenance bands, dataset provenance, experiment mode)
- **Phase F: Reliability & Safety** (Leak detection with automatic valve closure, pressure diagnostics with membrane fouling, pump protection dry-run/overcurrent, sensor failure detection, safety orchestration, firmware command protocol, safety endpoints, 36 unit tests + 13 safety = 49 total)
- **Phase G1: Alert State Machine Enforcement** (AlertStateMachine service with audit logging, auto-clear logic, bulk transitions, valid-transitions endpoint, 28 unit tests)

### Phase E Verification Status (2026-11-01)
- ✅ FSI centralized/versioned config (FSIConfigVersion, 7 components)
- ✅ Baselines working (flow, pressure, ΔP, turbidity, TDS/EC, daily volume)
- ✅ ΔP as first-class feature with baseline tracking
- ✅ FSI deterministic with 7 components, evidence, contributors
- ✅ FHI with 5 components + maintenance bands (NORMAL/MONITOR/PLAN/REPLACE)
- ✅ RUL pipeline: ML (RF/XGBoost) + deterministic fallback, model registry, CI, stability checks
- ✅ Failure risk: LOW/MEDIUM/HIGH with evidence + maintenance bands
- ✅ Explainability: contributors, factors, evidence, counterfactuals
- ✅ Model registry: versioning, dataset versioning, promotion workflow
- ✅ Dataset management: SYNTHETIC/CONTROLLED/REAL with provenance
- ✅ Prediction confidence: HIGH/MEDIUM/LOW, no fake precision
- ✅ Prediction stability: RUL jitter control, stability reports
- ✅ Alert integration: persistence, cooldown, dedup, severity
- ✅ Frontend API endpoints for all new features
- ✅ 36 unit tests passing (13 Phase D, 14 config, 9 security)
- ✅ All 5 migrations applied (0001-0005)

### Phase F Verification Status (2026-11-02)
- ✅ Leak detection with multi-sensor correlation (flow_delta, pressure_drop)
- ✅ Pressure diagnostics: overpressure, low pressure, membrane fouling indicator, pump curve deviation
- ✅ Flow diagnostics: dry-run, unstable flow, recovery ratio tracking
- ✅ Pump protection: overcurrent, overpower, efficiency degradation detection
- ✅ Sensor fault states: missing, stuck, impossible value, rapid change
- ✅ Safety audit events with full context
- ✅ Protection command abstraction with signed firmware commands
- ✅ Idempotent safe command execution with cooldown tracking
- ✅ Timeout/fail-safe defaults
- ✅ Role/resource authorization on all safety endpoints
- ✅ Rate limiting on safety endpoints
- ✅ 36 unit tests passing (14 config + 9 security + 13 Phase D/E/F)
- ✅ Migration 0006_safety_tables.py created

### Phase G1 Verification Status (2026-11-02)
- ✅ AlertStateMachine service enforces valid transitions (DETECTED→OPEN→ACKNOWLEDGED/SNOOZED/RESOLVED/AUTO_CLEARED)
- ✅ Terminal states (RESOLVED, AUTO_CLEARED) block further transitions
- ✅ Auto-clear logic for 24 self-clearing alert codes (water quality, pressure, flow, sensor, device, maintenance)
- ✅ Manual-only codes protected (leak_detected, filter_health_critical, maintenance_overdue)
- ✅ API endpoints: /acknowledge, /snooze, /resolve, /valid-transitions, /bulk-transition, /auto-clear-check
- ✅ Audit logging on all transitions
- ✅ 28 unit tests passing (transitions, auto-clear, bulk, validation map)
- ✅ Total unit tests: 64 (36 Phase D/E/F + 28 Phase G1)

### Phase G2 Verification Status (2026-11-02)
- ✅ Auto-clear integrated with telemetry evaluation engine (evaluate_alerts in telemetry.py)
- ✅ 7 alert categories auto-clear: water quality (2), pressure (4), flow (4), pump (4), tank (1), sensor (6), device (2), maintenance (1) = 24 codes
- ✅ 5 manual-only codes protected: leak_detected, leak_persistent, filter_health_critical, filter_rul_critical, maintenance_overdue
- ✅ Auto-clear triggers on condition resolution during telemetry ingestion
- ✅ WebSocket broadcast for auto-cleared alerts
- ✅ 19 unit tests passing (auto-clear codes verification, manual-only protection, auto-clear logic)
- ✅ Total unit tests: 102 (36 Phase D/E/F + 28 Phase G1 + 19 Phase G2 auto-clear + 19 G2 codes/logic)

### Next Actions
1. Start PostgreSQL/TimescaleDB and run migrations (`alembic upgrade head`)
2. Run integration tests with database (`docker compose up -d postgres && python -m pytest tests/`)
3. **Phase G3: Notification Providers (console, email, webhook) + Queue**
   - Notification provider abstraction
   - Console/logging provider
   - Email provider (SMTP)
   - Webhook provider
   - Notification queue with retry logic
4. **Phase G4-G8: Maintenance workflows, endpoints, verification, calibration tracking**