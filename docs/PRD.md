# AquaNexis — Product Requirements Document

## 1. Product Overview

**AquaNexis** is a predictive water intelligence system that transforms raw multi-parameter sensor data into actionable water quality insights, purification performance metrics, filter health predictions, and safety-critical diagnostics.

### Vision
Every water purification system should know its own health, predict its own failures, and protect its users — autonomously and transparently.

### Core Value Proposition
- **Beyond TDS**: 9+ water parameters for true quality understanding
- **Predictive Filter Intelligence**: Stress Index, Health Index, RUL with explanations
- **Purification Performance**: Real-time rejection rate, recovery ratio, efficiency
- **Safety-First Diagnostics**: Leak, pressure, flow, energy monitoring with validated protective actions
- **Explainable Alerts**: Every notification traces to source data and reasoning
- **Auditability**: Immutable history for compliance and trust

## 2. User Personas

| Persona | Needs | Key Interactions |
|---------|-------|------------------|
| **Homeowner** | Safe water, low maintenance surprise, filter cost optimization | Dashboard, alerts, filter replacement guidance |
| **Facility Manager** | Multi-device fleet, compliance logs, predictive maintenance | Fleet view, historical reports, maintenance scheduling |
| **Service Technician** | Diagnostic data, calibration workflows, verification | Device health, sensor diagnostics, post-maintenance verification |
| **Water Quality Engineer** | Trend analysis, anomaly investigation, model tuning | Raw data export, trend charts, model performance metrics |

## 3. Functional Requirements

### 3.1 Sense — Telemetry Ingestion
- **FR-S1**: Accept sensor readings from authenticated devices via HTTPS
- **FR-S2**: Validate payload structure, ranges, timestamps
- **FR-S3**: Assign quality state (GOOD, SUSPECT, BAD) per sensor per reading
- **FR-S4**: Persist raw readings immutably with device_id, timestamp, values, quality_flags
- **FR-S5**: Support simulator for development without hardware

### 3.2 Validate — Data Quality
- **FR-V1**: Range validation per sensor type (configurable per device)
- **FR-V2**: Rate-of-change validation (spike detection)
- **FR-V3**: Cross-sensor consistency checks (e.g., TDS vs EC correlation)
- **FR-V4**: Sensor fault detection (stuck values, noise patterns)
- **FR-V5**: Data freshness tracking (last_seen per device/sensor)

### 3.3 Understand — Water Quality Intelligence
- **FR-U1**: Compute **AquaScore** (0-100) from weighted parameter scores
- **FR-U2**: Parameter scoring: TDS, pH, turbidity, temperature vs WHO/EPA guidelines
- **FR-U3**: Trend analysis: 1h, 24h, 7d, 30d windows with direction/magnitude
- **FR-U4**: Anomaly detection: statistical (z-score, IQR) + isolation forest (when data sufficient)
- **FR-U5**: Purification performance: rejection rate = 1 - (permeate_TDS / feed_TDS)

### 3.4 Detect — Filter & System Diagnostics
- **FR-D1**: **Filter Stress Index (FSI)** 0-100: cumulative stress from usage, pressure, quality, time
- **FR-D2**: **Filter Health Index (FHI)** 0-100: derived from FSI, age, cleaning cycles, recovery trend
- **FR-D3**: Pressure diagnostics: membrane fouling indicator, pump curve deviation
- **FR-D4**: Leak detection: sensor + flow/pressure correlation, rate-of-change
- **FR-D5**: Tank state: level, fill/empty rates, stagnation detection
- **FR-D6**: Pump energy: current/power trending, efficiency degradation

### 3.5 Predict — Remaining Useful Life
- **FR-P1**: RUL prediction (days) with confidence band
- **FR-P2**: Model provenance: name, version, training dataset version, prediction timestamp
- **FR-P3**: Input features logged for reproducibility
- **FR-P4**: Explanation payload: top contributing factors (SHAP-style or coefficient-based)
- **FR-P5**: Baseline: deterministic survival model → statistical regression → ML (when data justifies)

### 3.6 Alert — Explainable Notification
- **FR-A1**: Alert state machine: NORMAL → INFO/WARNING/CRITICAL → ACKNOWLEDGED → RESOLVED
- **FR-A2**: Deduplication: same dedupe_key = update existing, not create new
- **FR-A3**: Alert payload: type, severity, source, trigger_value, threshold, explanation, timestamp
- **FR-A4**: Notification channels: in-app, email, webhook (extensible)
- **FR-A5**: Alert history with full audit trail

### 3.7 Protect — Safety Actions
- **FR-PR1**: Leak → validate (sensor + flow delta) → close inlet valve → log → notify
- **FR-PR2**: Overpressure → validate → open relief / stop pump → log → notify
- **FR-PR3**: Dry-run (flow < min with pump on) → stop pump → log → notify
- **FR-PR4**: Pump overcurrent → stop pump → log → notify
- **FR-PR5**: All safety actions: isolated, validated, logged, auditable, frontend never triggers directly

### 3.8 Assist — Maintenance Workflows
- **FR-M1**: Filter replacement workflow: guided steps, verification, reset health
- **FR-M2**: Calibration workflow: guided sensor calibration, reference values, verification
- **FR-M3**: Post-maintenance verification: automated quality check, performance baseline reset
- **FR-M4**: Maintenance history: what, when, who, pre/post metrics

## 4. Non-Functional Requirements

| Category | Requirement |
|----------|-------------|
| **Performance** | Dashboard load < 2s; telemetry ingestion < 100ms p99; WebSocket latency < 50ms |
| **Reliability** | 99.9% ingestion uptime; graceful degradation (read-only mode if ML down) |
| **Security** | Device JWT auth; TLS 1.3; secrets in env vars; no PII in telemetry |
| **Scalability** | 10k devices, 1 reading/min each = 14.4M readings/day; horizontal API scaling |
| **Maintainability** | Modular boundaries; >80% test coverage on domain logic; OpenAPI docs |
| **Accessibility** | WCAG 2.1 AA; keyboard navigation; screen reader support; color-blind safe palette |

## 5. Success Metrics

| Metric | Target |
|--------|--------|
| AquaScore accuracy vs lab | ±5 points |
| RUL MAE (baseline) | < 14 days |
| Filter failure prediction recall | > 85% |
| Alert precision (non-spurious) | > 90% |
| Safety action correctness | 100% (validated) |
| Dashboard first paint | < 1.5s |
| API p99 latency | < 200ms |

## 6. Out of Scope (v1)
- Lab-grade chemical sensors (heavy metals, specific ions)
- Multi-tenant SaaS (single-tenant deployment only)
- Mobile native apps (responsive web only)
- Blockchain/audit ledger (standard DB audit sufficient)
- Voice assistants, AR/VR interfaces
- Deep learning models (until dataset justifies)