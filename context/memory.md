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
- **Phase D (Water Intelligence + Filter Intelligence)**: ⏳ NEXT
- **Phase E (Filter Intelligence)**: ⏳ PENDING
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

### Next Actions
1. Start PostgreSQL/TimescaleDB and run migrations
2. Run integration tests with database
3. Start Phase D: Water Intelligence + Filter Intelligence

### Phase C Verification Status (2026-11-01)
- ✅ Telemetry ingestion endpoint (POST /api/v1/telemetry) - complete with quality validation, alert evaluation, WebSocket broadcast
- ✅ Batch ingestion endpoint (POST /api/v1/telemetry/batch) - complete with per-item status
- ✅ Alert evaluation integrated into telemetry ingestion (leak, pressure, flow, pump, TDS, tank level)
- ✅ Alert state machine (DETECTED → OPEN → ACKNOWLEDGED/SNOOZED → RESOLVED/AUTO_CLEARED)
- ✅ Alert API endpoints (list, get, acknowledge, snooze, resolve, summary)
- ✅ WebSocket endpoint (/ws/devices/{device_id}) with ConnectionManager
- ✅ WebSocket events: telemetry.updated, alert.created, alert.updated, device.status_changed, sensor.health_changed
- ✅ Alert codes aligned between telemetry evaluation and ALERT_CODES registry
- ✅ 23 unit tests passing (config + security)
- ⚠️ Integration tests require PostgreSQL/TimescaleDB