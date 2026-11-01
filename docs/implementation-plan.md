# AquaNexis — Implementation Plan

## Overview
Vertical slices delivered in order. Each slice = working, tested, demonstrable increment.

---

## Slice A — Runtime Stability (Week 1-2)
**Goal**: Backend runs, health checks pass, database connects, logs structured, tests green.

### Backend Tasks
- [ ] **A1** Initialize FastAPI project with `pyproject.toml`, `ruff`, `mypy`, `pytest`
- [ ] **A2** Configuration management (pydantic-settings, `.env.example`, validation)
- [ ] **A3** Database layer: async SQLAlchemy + asyncpg, session management, `init_db()`
- [ ] **A4** Structured logging (structlog, JSON output, request_id correlation)
- [ ] **A5** Health endpoints: `GET /health` (liveness), `GET /ready` (readiness with DB check)
- [ ] **A6** Alembic setup + initial migration (devices, sensor_readings tables)
- [ ] **A7** Device JWT authentication (issue, verify, middleware)
- [ ] **A8** Basic test suite: config, health, auth, database
- [ ] **A9** Dockerfile + docker-compose.yml for local dev
- [ ] **A10** CI pipeline: lint, typecheck, test, build

### Frontend Tasks
- [ ] **A11** Initialize React + TypeScript + Vite project
- [ ] **A12** Tailwind CSS + design tokens from uiux-brief
- [ ] **A13** TanStack Query setup + API client (axios/fetch wrapper)
- [ ] **A14** Routing (React Router), layout shell (header, sidebar)
- [ ] **A15** Primitive UI components (Button, Card, Badge, Input, Select)
- [ ] **A16** Theme provider (light/dark, CSS variables)
- [ ] **A17** ESLint + Prettier + TypeScript strict mode
- [ ] **A18** Vitest + React Testing Library setup
- [ ] **A19** Dockerfile + docker-compose integration
- [ ] **A20** CI pipeline: lint, typecheck, test, build

### Infrastructure
- [ ] **A21** GitHub Actions workflows (backend, frontend, integration)
- [ ] **A22** `.env.example` with all required variables documented
- [ ] **A23** Pre-commit hooks (ruff, prettier, mypy)

### Acceptance Criteria
- `docker compose up` starts backend + frontend + postgres
- `GET /health` → 200 `{status: "healthy"}`
- `GET /ready` → 200 `{ready: true, checks: {...}}`
- Backend tests pass (`pytest -v`)
- Frontend builds (`npm run build`) and tests pass (`npm test`)
- No secrets in repo
- Structured JSON logs visible in container output

---

## Slice B — Telemetry Foundation (Week 2-3)
**Goal**: Device identity, sensor ingestion, validation, persistence, simulator.

### Backend Tasks
- [ ] **B1** Device domain model + repository (CRUD, status updates)
- [ ] **B2** Sensor reading domain model + repository (TimescaleDB optimized)
- [ ] **B3** Quality validation service (range, rate, cross-sensor, stuck)
- [ ] **B4** Telemetry ingestion endpoint `POST /api/v1/telemetry`
- [ ] **B5** Background derivation task (AquaScore, trends, anomalies, FSI, FHI, RUL, diagnostics)
- [ ] **B6** Derived data repositories (water_quality_scores, filter_health, diagnostics, performance)
- [ ] **B7** Device provisioning endpoint `POST /api/v1/devices` (admin)
- [ ] **B8** Device config endpoints `GET/PUT /api/v1/devices/{id}`
- [ ] **B9** Telemetry history endpoint with downsampling
- [ ] **B10** Simulator service (generates realistic sensor data for N devices)
- [ ] **B11** Unit tests: validation, derivation, repositories
- [ ] **B12** Integration tests: ingestion → persistence → derivation → query

### Frontend Tasks
- [ ] **B13** Device selector in header (connects to `/devices`)
- [ ] **B14** Connection status indicator (WebSocket + polling fallback)
- [ ] **B15** TanStack Query hooks for telemetry, latest reading
- [ ] **B16** SensorValueCard component (value, unit, quality badge, freshness)
- [ ] **B17** Basic dashboard layout with sensor grid (9 cards)

### Acceptance Criteria
- Simulator runs, sends telemetry every 10s
- `POST /telemetry` accepts valid payload, returns quality + derived
- Invalid payload → 422 with details
- Quality flags correctly assigned (range, rate, cross-sensor)
- Raw readings in `sensor_readings` hypertable
- Derived tables populated within 5s of ingestion
- Dashboard shows live sensor grid with quality badges
- History endpoint returns downsampled data (max 1000 points)

---

## Slice C — Live Dashboard (Week 3-4)
**Goal**: Complete dashboard with AquaScore, Filter Health, System State, Alerts, Trends.

### Backend Tasks
- [ ] **C1** Dashboard aggregation endpoint `GET /api/v1/devices/{id}/dashboard`
- [ ] **C2** WebSocket manager for real-time updates
- [ ] **C3** WebSocket endpoint `/ws/realtime/{device_id}`
- [ ] **C4** Real-time broadcast: telemetry, alerts, safety actions, device status
- [ ] **C5** Alert repository + service (CRUD, state machine, deduplication)
- [ ] **C6** Alert endpoints: `GET /alerts`, `POST /alerts/{id}/acknowledge`, `POST /alerts/{id}/resolve`
- [ ] **C6** Alert evaluation integrated into derivation pipeline

### Frontend Tasks
- [ ] **C7** AquaScoreGauge component (animated, color bands)
- [ ] **C8** FilterHealthCard (FSI, FHI, RUL sparklines)
- [ ] **C9** SystemStateBadge (healthy/degraded/critical + pulse)
- [ ] **C10** ActiveAlertBanner (slide down, pulse if critical, acknowledge action)
- [ ] **C11** KeyTrendChart (uPlot sparkline, 24h AquaScore trend)
- [ ] **C12** WebSocket hook + connection management (reconnect, backoff)
- [ ] **C13** Dashboard page composition (all components integrated)
- [ ] **C14** Loading skeletons, error states, empty states
- [ ] **C15** Responsive layout (sidebar collapse, mobile drawer)
- [ ] **C16** Accessibility: live region for alerts, focus management

### Acceptance Criteria
- Dashboard loads < 2s (simulated data)
- WebSocket connects, receives live updates
- AquaScore gauge animates on value change
- Alert banner appears for critical/warning alerts
- Acknowledge button works, updates alert state
- Sensor grid updates via WebSocket (no refetch needed)
- Freshness indicator accurate (green < 10s, amber 10-60s, red > 60s)
- Mobile layout usable (drawer sidebar, stacked cards)

---

## Slice D — Water Intelligence (Week 4-5)
**Goal**: AquaScore detail, trend analysis, anomaly detection, purification performance.

### Backend Tasks
- [ ] **D1** AquaScore algorithm (weighted parameter scores vs WHO/EPA guidelines)
- [ ] **D2** Trend computation (1h, 24h, 7d, 30d windows, direction + magnitude)
- [ ] **D3** Anomaly detection: z-score, IQR, rate-of-change (Isolation Forest when data sufficient)
- [ ] **D4** Purification performance: rejection rate, recovery ratio, efficiency
- [ ] **D5** Water Quality endpoints: `/water-quality`, `/trends`, `/anomalies`, `/performance`
- [ ] **D6** Model registry for anomaly models (versioning, metadata)

### Frontend Tasks
- [ ] **D7** WaterQualityPage (parameter score cards, trend chart, anomaly timeline)
- [ ] **D8** ParameterScoreCard component
- [ ] **D9** TrendChart component (uPlot, multi-series, window selector, downsampling)
- [ ] **D10** AnomalyTimeline component
- [ ] **D11** PurificationPerformancePage (rejection gauge, recovery chart, efficiency trend)
- [ ] **D12** Export CSV functionality

### Acceptance Criteria
- AquaScore computes correctly from parameter scores
- Trends show direction/magnitude for 4 windows
- Anomalies detected and flagged with type
- Purification performance calculated from feed/permeate
- Water Quality page loads < 3s with 30d data
- Trend chart handles 10k+ points via downsampling
- Export downloads CSV with timestamp, values, scores

---

## Slice E — Filter Intelligence (Week 5-6)
**Goal**: FSI, FHI, RUL baseline, model metadata, explainable output.

### Backend Tasks
- [ ] **E1** Filter Stress Index (deterministic formula: volume, pressure, quality, time, cleanings)
- [ ] **E2** Filter Health Index (derived from FSI, age, cleaning cycles, recovery trend)
- [ ] **E3** RUL baseline model (Weibull survival → deterministic, then statistical regression)
- [ ] **E4** Feature extraction pipeline (sliding windows, cumulative stats)
- [ ] **E5** Explanation generation (coefficient-based for baseline, SHAP-ready)
- [ ] **E6** Model artifact registry (load, version, metadata, promotion)
- [ ] **E7** Filter Health endpoints: `/filter-health`, `/rul`, `/explanation`
- [ ] **E8** Scheduled job: recalculate FSI/FHI/RUL every 6 hours
- [ ] **E9** Unit tests: FSI formula, FHI derivation, RUL prediction, explanation

### Frontend Tasks
- [ ] **E10** FilterHealthPage (FSI/FHI gauges, RUL chart with confidence band)
- [ ] **E11** RULChart component (uPlot, line + confidence ribbon)
- [ ] **E12** ExplanationPanel (horizontal bar chart of feature contributions)
- [ ] **E13** ModelMetadataCard (name, version, dataset, metrics, status)
- [ ] **E14** "Replace Filter" CTA (disabled unless FHI < 40 or RUL < 30)
- [ ] **E15** Filter health history view

### Acceptance Criteria
- FSI/FHI compute deterministically from features
- RUL returns days + confidence band + model metadata
- Explanation shows top 5 factors with direction
- Model version persisted with every prediction
- Filter Health page loads < 2s
- RUL chart shows history with confidence ribbon
- Replace Filter button navigates to maintenance wizard

---

## Slice F — Reliability (Week 6-7)
**Goal**: Pressure diagnostics, leak state, tank state, pump/energy, validated safety interface.

### Backend Tasks
- [ ] **F1** Pressure diagnostics: fouling indicator, pump curve deviation
- [ ] **F2** Leak diagnostics: probability, flow/pressure correlation
- [ ] **F3** Tank diagnostics: fill/empty rates, stagnation detection
- [ ] **F4** Pump diagnostics: efficiency trend, current/power, runtime
- [ ] **F5** Safety Service: validation, action execution, logging, notification
- [ ] **F6** Safety config per device (thresholds, actions, cooldowns)
- [ ] **F7** Firmware command protocol (validated payload, signed)
- [ ] **F8** Safety endpoints: `GET /safety/config`, `POST /safety/test` (admin)
- [ ] **F9** Diagnostics endpoints: `/diagnostics` (aggregated), `/diagnostics/history`
- [ ] **F10** Unit tests: diagnostic calculations, safety validation logic

### Frontend Tasks
- [ ] **F11** DiagnosticsPage (5 panels: pressure, flow, leak, tank, pump)
- [ ] **F12** DiagnosticsPanel component (current, trend, status, mini-chart)
- [ ] **F13** Safety action toast/notification (distinct from alerts)
- [ ] **F14** Safety config view (read-only for operators, editable for admin)

### Acceptance Criteria
- Diagnostics compute correctly from sensor windows
- Leak probability correlates sensor + flow delta
- Pressure fouling indicator tracks membrane degradation
- Pump efficiency trend calculated over 7d
- Safety validation prevents false triggers (multi-sensor correlation)
- Safety action logged with full context
- Diagnostics page shows all 5 panels with live data
- Safety test endpoint triggers validation (no hardware action in sim)

---

## Slice G — Maintenance (Week 7-8)
**Goal**: Alerts workflow, filter replacement, calibration, post-maintenance verification.

### Backend Tasks
- [ ] **G1** Alert state machine enforcement (API + service)
- [ ] **G2** Auto-resolution for self-clearing alerts (water quality, pressure)
- [ ] **G3** Notification providers (console, email, webhook) + queue
- [ ] **G4** Maintenance service: filter replacement, calibration, verification workflows
- [ ] **G5** Maintenance endpoints: `/filter-replacement`, `/calibration`, `/verification`, `/history`
- [ ] **G6** Post-maintenance verification: automated quality check, baseline reset
- [ ] **G7** Calibration due tracking (time + usage based)
- [ ] **G8** Unit tests: alert transitions, maintenance workflows, verification logic

### Frontend Tasks
- [ ] **G9** AlertsPage (list with filters, detail drawer, timeline)
- [ ] **G10** AlertDetail component (state machine visualization, actions)
- [ ] **G11** MaintenancePage (quick actions, history table)
- [ ] **G12** FilterReplacementWizard (4 steps: confirm, serial, verify, complete)
- [ ] **G13** CalibrationWizard (sensor selection, reference inputs, verification)
- [ ] **G14** VerificationStep component (automated check, manual confirm)
- [ ] **G15** MaintenanceHistory table (sortable, filterable, expandable details)

### Acceptance Criteria
- Alert state machine: ACTIVE → ACKNOWLEDGED → RESOLVED
- Deduplication prevents alert storms
- Auto-resolve works for water quality, pressure
- Notifications sent for CRITICAL alerts
- Filter replacement wizard completes in 4 steps
- Calibration wizard records offset/slope, updates device config
- Verification runs automated quality check, passes/fails
- Maintenance history shows pre/post metrics

---

## Slice H — Product Polish (Week 8-9)
**Goal**: UI refinement, motion, responsive, performance, accessibility, test coverage.

### Frontend Tasks
- [ ] **H1** Landing page (hero, SVG system viz, CTAs)
- [ ] **H2** ReadinessPage (engineering checklist)
- [ ] **H3** DeviceHealthPage (sensor grid, firmware, connectivity)
- [ ] **H4** Motion polish (all approved animations implemented)
- [ ] **H5** Responsive polish (all pages tested at 4 breakpoints)
- [ ] **H6** Performance: lazy-load feature pages, prefetch predictable nav
- [ ] **H7** Accessibility audit + fixes (WCAG AA)
- [ ] **H8** Dark mode toggle + persistence
- [ ] **H9** Error boundaries + global error UI
- [ ] **H10** Component test coverage > 70%
- [ ] **H11** E2E test: Dashboard → anomaly → alert → filter health → maintenance

### Backend Tasks
- [ ] **H12** API response caching headers (ETag, Cache-Control)
- [ ] **H13** Request rate limiting (per device, per IP)
- [ ] **H14** OpenAPI docs enhancement (examples, descriptions)
- [ ] **H15** Database query optimization (indexes, composite)
- [ ] **H16** Integration test coverage > 80% domain logic
- [ ] **H17** Load test: 1000 simulated devices, 1 reading/10s

### Acceptance Criteria
- Landing page renders correctly, CTAs navigate
- Readiness page shows 10 checks with status
- Device Health page shows all 9 sensors + firmware
- All approved animations smooth (60fps)
- All pages usable at 375px width
- Feature pages lazy-loaded (network tab shows no waterfall)
- Lighthouse: Performance > 90, Accessibility > 95, Best Practices > 90
- Dark mode toggles and persists
- E2E test passes in CI
- Load test: p99 ingestion < 200ms, dashboard < 2s

---

## Cross-Cutting Concerns (Ongoing)

| Area | Continuous Tasks |
|------|------------------|
| **Documentation** | Update architecture.md, schema docs, memory.md on each slice |
| **Migrations** | Every schema change = Alembic migration, reviewed |
| **Secrets** | Never commit; rotate quarterly; scan in CI |
| **Observability** | Add metrics/logs/traces for new features |
| **Security** | Dependency scanning (Dependabot), SAST in CI |

---

## Milestone Dates (Target)

| Slice | Target Complete | Demo Focus |
|-------|-----------------|------------|
| A | Week 2 | `docker compose up` → health checks green |
| B | Week 3 | Simulator → live sensor grid |
| C | Week 4 | Dashboard with live WebSocket updates |
| D | Week 5 | Water Quality + Performance pages |
| E | Week 6 | Filter Health with RUL + explanation |
| F | Week 7 | Diagnostics + Safety test |
| G | Week 8 | Full maintenance workflow |
| H | Week 9 | Polished product, E2E passing |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| TimescaleDB complexity | Start with vanilla PG, enable hypertable in migration B2 |
| WebSocket scaling | Single-process first; Redis pub/sub for multi-worker later |
| ML without data | Deterministic baselines only until Week 6; statistical when 30d data |
| Firmware integration | Simulator mimics device API; firmware developed in parallel |
| Scope creep | Hard stop at slice boundaries; new items → backlog |
| Performance | Downsampling, pagination, caching built into each slice |

---

## Definition of Done (Per Slice)
1. All tasks checked
2. Backend tests pass (`pytest -v`)
3. Frontend tests pass (`npm test`)
4. Frontend builds (`npm run build`)
4. Docker compose starts full stack
5. Manual smoke test of slice features
6. Documentation updated
7. No secrets introduced
8. PR reviewed and merged