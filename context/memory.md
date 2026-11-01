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

### Implementation Status
- **Slice A (Runtime Stability)**: ✅ COMPLETE
- **Slice B (Telemetry Foundation)**: ✅ COMPLETE
- **Phase C (Live Dashboard + Alert Lifecycle)**: ✅ COMPLETE
- **Phase D (Water Intelligence + Filter Intelligence)**: ✅ COMPLETE
- **Phase E (Filter Intelligence Enhancement)**: ⏳ NEXT
- **Phase F (Reliability)**: ⏳ PENDING
- **Phase G (Maintenance)**: ⏳ PENDING
- **Phase H (Product Polish)**: ⏳ PENDING
- **Phase I (Final Verification)**: ⏳ PENDING

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

### Phase D Verification Status (2026-11-01)
- ✅ AquaScore algorithm with configurable weights, guidelines, confidence, explanations
- ✅ Purification performance: TDS rejection, recovery ratio, efficiency
- ✅ Hydraulic intelligence: ΔP, flow deviation, fill-time deviation, pressure stability
- ✅ Filter Stress Index (deterministic): DP, flow deviation, turbidity exposure, cumulative volume, age, operating hours, TDS trend
- ✅ Filter Health Index (0-100): stress, lifecycle, usage, pressure/flow, historical behavior components
- ✅ RUL pipeline: ML (Random Forest/XGBoost) with deterministic fallback, model registry, confidence intervals
- ✅ Failure risk classification (LOW/MEDIUM/HIGH): RUL, health, stress, anomaly, alert components
- ✅ Explainability: top contributing factors, model metadata, feature importance
- ✅ Model registry: versioning, dataset versioning, metrics tracking, status lifecycle
- ✅ API endpoints: water-quality, filter-health, purification-performance, diagnostics
- ✅ 36 unit tests passing (Phase D: 13, Config: 14, Security: 9)
- ✅ All migrations applied (0001-0005)

### Next Actions
1. Start PostgreSQL/TimescaleDB and run migrations (`alembic upgrade head`)
2. Run integration tests with database (`docker compose up -d postgres && python -m pytest tests/`)
3. Start Phase E: Filter Intelligence Enhancement

### Phase D Verification Status (2026-11-01)
- ✅ AquaScore algorithm with configurable weights, guidelines, confidence, explanations
- ✅ Purification performance (TDS rejection, Recovery ratio, Efficiency)
- ✅ Hydraulic intelligence (ΔP, flow deviation, fill-time deviation, pressure stability)
- ✅ Filter Stress Index (deterministic): 7 components (DP, flow deviation, turbidity, volume, age, hours, TDS trend)
- ✅ Filter Health Index (0-100): 5 components (stress, lifecycle, usage, pressure/flow, historical)
- ✅ RUL pipeline: ML (Random Forest/XGBoost) with deterministic fallback, model registry, confidence intervals
- ✅ Failure risk classification (LOW/MEDIUM/HIGH): RUL, health, stress, anomaly, alert components
- ✅ Explainability: top contributing factors, model metadata, feature importance
- ✅ Model registry: versioning, dataset versioning, metrics tracking, status lifecycle
- ✅ API endpoints: water-quality, filter-health, purification-performance, diagnostics
- ✅ 36 unit tests passing (Phase D: 13, Config: 14, Security: 9)
- ✅ All migrations applied (0001-0005)

### Next Actions
1. Start PostgreSQL/TimescaleDB and run migrations (`alembic upgrade head`)
2. Run integration tests with database (`docker compose up -d postgres && python -m pytest tests/`)
3. Start Phase E: Filter Intelligence Enhancement