# AquaNexis Brain — Core Architectural Knowledge

## Product Loop
**Sense → Validate → Understand → Detect → Predict → Alert → Protect → Assist**

## System Components
1. **Multi-parameter Water Sensing** — Beyond TDS: pH, turbidity, temp, flow, pressure, tank level, leak, pump energy
2. **Purification Performance Measurement** — Rejection rate, recovery ratio, permeate quality
3. **Purifier Health Diagnostics** — Pump health, membrane fouling, valve state
4. **Filter Stress & Health Estimation** — Stress Index, Health Index, RUL prediction
5. **Explainable Alerts** — Type, severity, source, dedupe, audit trail
6. **Leak/Pressure/Flow/Energy Diagnostics** — Real-time anomaly detection
7. **Historical Data & Auditability** — Immutable raw telemetry, reproducible derivations
8. **Maintenance & Calibration Workflows** — Guided replacement, verification, calibration

## Conceptual Architecture
```
ESP32 / Sensors
      ↓ Wi-Fi / HTTPS
FastAPI Backend
      ↓ PostgreSQL
Analytics / ML Layer
      ↓
Decision + Alert Engine
      ↓
React UI (TanStack Query)
```

## Key Domain Models
- **Device** — Identity, firmware, calibration, sensor config
- **SensorReading** — Immutable raw telemetry with quality flags
- **WaterQualityIndex** — AquaScore (0-100), component scores
- **FilterHealth** — Stress Index, Health Index, RUL (days), model metadata
- **PurificationPerformance** — Rejection rate, recovery, efficiency
- **SystemDiagnostics** — Pressure, flow, leak, pump energy, tank state
- **Alert** — State machine: NORMAL → INFO/WARN/CRIT → ACK → RESOLVED
- **MaintenanceEvent** — Filter replacement, calibration, verification

## ML Model Strategy
| Model | Type | Inputs | Output |
|-------|------|--------|--------|
| Anomaly Detection | Statistical/Isolation Forest | Multi-sensor window | Anomaly score, flags |
| Filter Stress Index | Regression (deterministic first) | Usage, quality, pressure, time | 0-100 stress |
| Filter Health Index | Regression | Stress, age, cleaning cycles | 0-100 health |
| RUL Prediction | Survival/Regression | Health, stress trajectory, usage pattern | Days + confidence band |
| Leak Detection | Threshold + Rate-of-change | Flow delta, pressure delta, leak sensor | Leak probability |

## Safety Subsystem (Isolated)
- **Leak Protection** — Valve shutoff on validated leak
- **Pressure Protection** — Relief on overpressure
- **Flow Protection** — Pump stop on dry-run/over-flow
- **Energy Protection** — Pump current limit
- All actions: validated → logged → notified → auditable

## Alert Taxonomy
| Type | Severity | Source | Auto-resolve? |
|------|----------|--------|---------------|
| Water Quality Degraded | WARNING | AquaScore < threshold | Yes |
| Filter Stress High | WARNING | FSI > 80 | No |
| Filter Health Critical | CRITICAL | FHI < 20 | No |
| Leak Detected | CRITICAL | Leak sensor + flow delta | No |
| Pressure Anomaly | WARNING/CRITICAL | Pressure sensor | Conditional |
| Pump Energy Anomaly | WARNING | Current sensor | Conditional |
| Sensor Fault | WARNING | Quality flags | Conditional |
| Calibration Due | INFO | Time/usage threshold | No |
| Maintenance Due | INFO | RUL < threshold | No |

## Data Flow Invariants
1. Raw sensor readings **never modified** after ingestion
2. Corrections = new administrative events, not overwrites
3. All derived values = pure functions of raw data + config
4. Model predictions = immutable records with full provenance
5. Alert transitions = explicit state machine with audit trail

## Configuration Schema
```yaml
device:
  id: string
  sensors: { tds, ph, turbidity, temp, flow, pressure, tank, leak, pump_current }
  calibration: { sensor: { offset, slope, last_calibrated } }
  safety: { leak_action: "shutoff", pressure_max: 600, flow_min: 0.1, pump_current_max: 2.5 }
thresholds:
  aquascore_warn: 70
  aquascore_crit: 50
  fsi_warn: 70
  fsi_crit: 85
  fhi_warn: 40
  fhi_crit: 20
  rul_warn_days: 30
  rul_crit_days: 7
ml:
  anomaly_window_minutes: 15
  rul_model: "baseline_v1"
  retrain_schedule: "weekly"
```

## Integration Contracts
- **Device → Backend**: HTTPS POST /api/v1/telemetry (JSON, device JWT)
- **Backend → UI**: REST + WebSocket for real-time
- **ML → Backend**: Internal gRPC or direct function calls
- **Alerts → Notifications**: Webhook/email/push via provider abstraction