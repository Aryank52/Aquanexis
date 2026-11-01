# AquaNexis — Application Flow Document

## 1. User Journeys

### 1.1 Primary Journey: Daily Dashboard Check
```
User opens app
    │
    ▼
┌─────────────────────────────────────┐
│ Landing Page (if not authenticated) │
│ - Product title + value prop        │
│ - System visualization              │
│ - "Open Live System" (primary)      │
│ - "Filter Intelligence" (secondary) │
└─────────────┬───────────────────────┘
              │ Click "Open Live System"
              ▼
┌─────────────────────────────────────┐
│ Dashboard (authenticated)           │
│ - AquaScore gauge (prominent)       │
│ - Filter Health card (FSI/FHI/RUL)  │
│ - System State badge                │
│ - Active Alert banner (if any)      │
│ - Sensor grid (9 cards)             │
│ - Key trend sparkline               │
│ - Data freshness indicator          │
└─────────────┬───────────────────────┘
              │
              ├── Click "Water Quality" → Water Quality Page
              ├── Click "Filter Health" → Filter Health Page
              ├── Click "Diagnostics" → Diagnostics Page
              ├── Click "Alerts" → Alerts Page
              ├── Click "Maintenance" → Maintenance Page
              └── Click "Device Health" → Device Health Page
```

### 1.2 Anomaly → Alert → Maintenance Journey
```
Device detects anomaly (e.g., TDS rising)
    │
    ▼
Backend validates + computes AquaScore drop
    │
    ▼
Alert created: "water_quality_degraded" WARNING
    │
    ▼
WebSocket pushes to Dashboard
    │
    ▼
Active Alert Banner appears (pulse animation)
    │
    ▼
User clicks banner → Alerts Page
    │
    ▼
Alert Detail shows:
  - Trigger: TDS 180 → 320 ppm (threshold 250)
  - Trend: +45% over 2h
  - Explanation: "Permeate TDS rising, rejection rate dropped to 82%"
  - Action: "Acknowledge" button
    │
    ▼
User acknowledges → Alert state: ACKNOWLEDGED
    │
    ▼
User navigates to Filter Health Page
    │
    ▼
FSI elevated (78), FHI declining (45), RUL 12 days
    │
    ▼
Explanation panel: "Top factors: feed TDS +35%, pressure +12%, runtime +200h"
    │
    ▼
User clicks "Replace Filter" → Maintenance Wizard
    │
    ▼
Step 1: Confirm replacement
Step 2: Scan/enter new filter serial
Step 3: System runs verification (flush + quality check)
Step 4: Verification passes → FHI resets to 95, RUL recalculated
Step 5: Alert auto-resolves (water_quality_degraded)
    │
    ▼
Maintenance event recorded with pre/post metrics
    │
    ▼
Dashboard updates: AquaScore 94, Filter Health 95, RUL 180 days
```

### 1.3 Safety Event Journey (Leak Detection)
```
Leak sensor triggers + flow delta confirms
    │
    ▼
Safety Service validates (multi-sensor correlation)
    │
    ▼
Action: Close inlet valve (configured)
    │
    ▼
Firmware executes (local fallback also triggers)
    │
    ▼
SafetyEvent logged + CRITICAL alert created
    │
    ▼
WebSocket pushes to all connected clients
    │
    ▼
Dashboard: Red "LEAK DETECTED" banner, System State = CRITICAL
    │
    ▼
Notification sent (email/webhook)
    │
    ▼
User acknowledges → Alert: ACKNOWLEDGED
    │
    ▼
User investigates → Fixes leak → Presses "Reset Safety" (admin)
    │
    ▼
Valve reopens → System State = NORMAL → Alert RESOLVED
```

### 1.4 Calibration Journey
```
User notices pH reading drift
    │
    ▼
Navigates to Device Health → Sensor Health Grid
    │
    ▼
pH sensor shows "Calibration Due" badge
    │
    ▼
Clicks "Calibrate pH" → Calibration Wizard
    │
    ▼
Step 1: Place sensor in pH 7.0 buffer → Enter reference 7.0
Step 2: Place sensor in pH 4.0 buffer → Enter reference 4.0
Step 3: System computes offset/slope → Shows predicted vs actual
Step 4: Confirm → Calibration recorded + sensor_config updated
    │
    ▼
Post-calibration verification: Read known buffer → Confirm accuracy
    │
    ▼
Maintenance event: CALIBRATION recorded with pre/post metrics
    │
    ▼
Sensor Health Grid updates: "Calibrated 2 min ago", quality GOOD
```

## 2. Data Flows

### 2.1 Telemetry Ingestion Flow
```
ESP32 Device
    │
    ├── Reads all sensors (100ms - 1s intervals)
    ├── Applies local calibration (offset/slope)
    ├── Builds JSON payload with timestamp (NTP synced)
    ├── Signs with Device JWT
    └── POST /api/v1/telemetry (HTTPS/TLS)
                │
                ▼
FastAPI Backend
    │
    ├── Extract device_id from JWT
    ├── Validate payload (Pydantic)
    ├── Check device exists + status
    ├── Run quality validation:
    │   ├── Range checks (per sensor config)
    │   ├── Rate-of-change (vs last reading)
    │   ├── Cross-sensor consistency (TDS≈EC×0.64)
    │   └── Stuck sensor detection (variance < threshold)
    ├── Assign quality flags per sensor
    ├── Compute overall_quality (GOOD/SUSPECT/BAD)
    ├── Persist raw reading (sensor_readings hypertable)
    │
    ├── Async (background task):
    │   ├── Compute AquaScore + parameter scores
    │   ├── Compute trends (1h, 24h, 7d)
    │   ├── Run anomaly detection
    │   ├── Compute purification performance
    │   ├── Compute FSI, FHI, RUL prediction
    │   ├── Compute diagnostics (pressure, flow, leak, tank, pump)
    │   ├── Check alert thresholds
    │   ├── Trigger safety validation if critical
    │   └── Persist all derived tables
    │
    ├── Broadcast latest via WebSocket
    └── Return response with quality + derived values
```

### 2.2 Alert Generation Flow
```
Derived computation completes
    │
    ▼
Check each alert rule:
    ├── AquaScore < 70 → water_quality_degraded (WARNING)
    ├── AquaScore < 50 → water_quality_critical (CRITICAL)
    ├── FSI > 70 → filter_stress_high (WARNING)
    ├── FSI > 85 → filter_stress_critical (CRITICAL)
    ├── FHI < 40 → filter_health_degraded (WARNING)
    ├── FHI < 20 → filter_health_critical (CRITICAL)
    ├── RUL < 30 days → maintenance_due (INFO)
    ├── RUL < 7 days → maintenance_urgent (WARNING)
    ├── Leak probability > 0.8 → leak_detected (CRITICAL)
    ├── Pressure > 600 kPa → pressure_anomaly (CRITICAL)
    ├── Pump current > 2.5A → pump_energy_anomaly (WARNING)
    ├── Sensor quality BAD → sensor_fault (WARNING)
    └── Calibration overdue → calibration_due (INFO)
    │
    ▼
For each triggered rule:
    ├── Generate dedupe_key = f"{device_id}:{alert_type}:{source}"
    ├── Query existing alert with same dedupe_key + state IN (ACTIVE, ACKNOWLEDGED)
    ├── If exists: UPDATE trigger_value, timestamp, explanation
    ├── If not: INSERT new alert (state=ACTIVE)
    ├── Broadcast alert:created or alert:updated via WebSocket
    ├── If severity CRITICAL: queue notification (email/webhook)
    └── If safety-related: trigger Safety Service validation
```

### 2.3 Safety Action Flow
```
Safety trigger (leak, overpressure, dry-run, overcurrent)
    │
    ▼
SafetyService.validate(trigger_type, device_id, current_readings)
    │
    ├── Re-read latest sensor values
    ├── Cross-validate with correlated sensors
    │   ├── Leak: leak_sensor AND (flow_delta > threshold OR pressure_drop > threshold)
    │   ├── Overpressure: pressure_sensor > threshold (confirm with 2nd reading)
    │   ├── Dry-run: flow < min AND pump_command == ON
    │   └── Overcurrent: pump_current > max (confirm with 2nd reading)
    ├── Check cooldown (prevent oscillation)
    └── Check device safety_config for action
    │
    ▼
If validated:
    ├── Build safety command payload
    ├── Send to firmware via MQTT/HTTP (validated, signed)
    ├── Firmware executes (local fallback also monitors)
    ├── Log SafetyEvent (action, trigger, validation_details)
    ├── Create CRITICAL alert (safety_action_executed)
    ├── Broadcast safety:action via WebSocket
    └── Queue notification
Else:
    ├── Log validation_failed (trigger, reason)
    └── Create WARNING alert (safety_validation_failed)
```

## 3. API Flow Details

### 3.1 Telemetry Ingestion (POST /api/v1/telemetry)
```
Request:
Headers: Authorization: Bearer <device_jwt>
Body: {device_id, timestamp, readings: {...}}

Processing:
1. JWT verify → device_id
2. Pydantic validate → SensorReadingInput
3. DeviceRepo.get(device_id) → Device (check status != ERROR)
4. QualityValidator.validate(readings, device.sensor_config, last_reading)
5. ReadingRepo.insert(raw_reading)
6. Return immediate response (accepted, reading_id, quality, derived)
7. BackgroundTask: derive_and_persist(device_id, reading)

Response (202 Accepted):
{
  "accepted": true,
  "reading_id": "uuid",
  "quality_assessment": {...},
  "derived": {...}
}
```

### 3.2 Dashboard Data Fetch (GET /api/v1/devices/{id}/dashboard)
```
Single optimized query returning:
- Latest sensor_reading (with quality)
- Latest water_quality_score
- Latest filter_health
- Latest system_diagnostics
- Active alert (highest severity)
- Device status + last_seen

Response:
{
  "device": {...},
  "latest_telemetry": {...},
  "water_quality": {...},
  "filter_health": {...},
  "diagnostics": {...},
  "active_alert": {...},
  "data_freshness_seconds": 3
}
```

### 3.3 Historical Data with Downsampling
```
GET /api/v1/devices/{id}/telemetry/history?
  start=2026-10-01&end=2026-10-31&
  sensors=tds,ph,flow&
  interval=1h&
  limit=1000

Processing:
1. Calculate optimal bucket = (end-start)/limit
2. TimescaleDB time_bucket_gapfill(bucket, timestamp)
3. Aggregate: AVG, MIN, MAX per bucket
4. Return downsampled points (max 1000)

Response:
{
  "device_id": "uuid",
  "interval": "1 hour",
  "series": {
    "tds": [{"t": "2026-10-01T00:00", "avg": 45.2, "min": 44.1, "max": 46.8}, ...],
    "ph": [...],
    "flow": [...]
  }
}
```

## 4. WebSocket Message Types

### 4.1 Client → Server
```json
{ "type": "subscribe", "device_id": "uuid" }
{ "type": "unsubscribe", "device_id": "uuid" }
{ "type": "ping" }
```

### 4.2 Server → Client
```json
{ "type": "telemetry", "device_id": "uuid", "data": {...} }
{ "type": "alert_created", "device_id": "uuid", "alert": {...} }
{ "type": "alert_updated", "device_id": "uuid", "alert": {...} }
{ "type": "safety_action", "device_id": "uuid", "action": "close_inlet_valve", "trigger": "leak" }
{ "type": "device_status", "device_id": "uuid", "status": "online", "last_seen": "..." }
{ "type": "pong" }
```

## 5. State Transitions

### 5.1 Device Status
```
PROVISIONED → ONLINE (telemetry received)
    │
    ├── 5 min no telemetry → OFFLINE
    ├── Error reading → ERROR
    └── Maintenance mode → MAINTENANCE
```

### 5.2 Alert State Machine (Detailed)
```
NORMAL (no alert)
    │
    ├─ threshold breached ──▶ ACTIVE (INFO/WARNING/CRITICAL)
    │                              │
    │                              ├─ auto-resolve condition met ──▶ RESOLVED
    │                              │
    │                              ├─ user acknowledges ──▶ ACKNOWLEDGED
    │                              │       │
    │                              │       ├─ condition clears ──▶ RESOLVED
    │                              │       └─ user resolves ──▶ RESOLVED
    │                              │
    │                              └─ condition clears (auto-resolve) ──▶ RESOLVED
    │
    └─ (sustained) → deduplicated (existing ACTIVE updated)
```

### 5.3 Filter Health State
```
NEW FILTER (FHI=100, FSI=0, RUL=max)
    │
    ├── Usage accumulates → FSI increases, FHI decreases, RUL decreases
    ├── Cleaning cycle → FSI decreases slightly, FHI increases slightly
    ├── Replacement → FHI=100, FSI=0, RUL=max (reset)
    └── Degraded (FHI<20) → CRITICAL alert + maintenance_due
```

## 6. Error Handling Flows

### 6.1 Ingestion Errors
| Error | HTTP Code | Device Action | Backend Action |
|-------|-----------|---------------|----------------|
| Invalid JWT | 401 | Re-authenticate | Log, no persist |
| Device not found | 404 | Re-provision | Log |
| Payload validation fail | 422 | Fix payload | Log, no persist |
| Device in ERROR | 409 | Wait/alert | Reject, alert admin |
| DB unavailable | 503 | Retry with backoff | Circuit breaker |
| Rate limited | 429 | Backoff | Log, reject |

### 6.2 Dashboard Query Errors
| Error | UI Behavior |
|-------|-------------|
| Device offline | Show "Offline" badge, stale data with warning |
| No data yet | Empty state: "Waiting for first reading..." |
| Query timeout | Retry button, show cached if available |
| WebSocket disconnect | Auto-reconnect (exponential backoff), show "Reconnecting..." |

## 7. Background Job Flows

### 7.1 Scheduled Jobs
| Job | Schedule | Purpose |
|-----|----------|---------|
| Aggregate hourly stats | Every hour | Pre-compute 1h/24h trends |
| Recalculate FSI/FHI/RUL | Every 6 hours | Batch update with latest data |
| Retrain models | Weekly (Sunday 2AM) | If new data > 10% |
| Check calibration due | Daily 6AM | Create calibration_due alerts |
| Cleanup old raw data | Monthly | Retain 2 years raw, 5 years aggregated |
| Backup verification | Weekly | Test restore |

### 7.2 Event-Driven Jobs
| Trigger | Job |
|---------|-----|
| Filter replacement | Reset filter health, recalc baseline |
| Calibration | Update sensor_config, invalidate cached scores |
| Safety action | Audit log, notify admin, require manual reset |
| Model promoted | Invalidate inference cache, reload |

## 8. Offline/Edge Scenarios

### 8.1 Device Offline
- Firmware buffers readings (up to 24h in flash)
- On reconnect: batch upload with original timestamps
- Backend processes in timestamp order, derives correctly
- Alerts generated for missed thresholds during gap

### 8.2 Backend Degraded
- Read-only mode: serve cached dashboard data
- Ingestion queue: accept but don't derive (return 202, derive async)
- Safety: firmware local fallback operates independently
- Alerts: only critical safety alerts via firmware direct notification

### 8.3 Network Partition
- Device continues sensing, buffering
- Frontend shows "Connection degraded" with last known state
- WebSocket reconnection with state sync on resume