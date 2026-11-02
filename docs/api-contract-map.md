# AquaNexis API Contract Map

## Current State Analysis (as of Phase G5)

### Backend Endpoints (Actual)

| Endpoint | Method | Path | Auth | Request Schema | Response Schema | Frontend Consumer | Status |
|----------|--------|------|------|----------------|-----------------|-------------------|--------|
| Health | GET | `/health` | None | - | `HealthCheckResponse` | healthApi.check() | ✅ |
| Health | GET | `/ready` | None | - | `HealthCheckResponse` | healthApi.ready() | ✅ |
| Auth Login | POST | `/auth/login` | None | `LoginRequest` | `LoginResponse` | authApi.login() | ✅ |
| Auth Logout | POST | `/auth/logout` | Bearer | - | - | authApi.logout() | ✅ |
| Auth Refresh | POST | `/auth/refresh` | None | `{refresh_token}` | `{access_token, expires_in}` | authApi.refreshToken() | ✅ |
| Device List | GET | `/devices` | API Key | - | `Device[]` | deviceApi.list() | ✅ |
| Device Get | GET | `/devices/{id}` | API Key | - | `Device` | deviceApi.get() | ✅ |
| Device Create | POST | `/devices` | API Key | `DeviceCreate` | `DeviceResponse` | N/A | ✅ |
| Device Update | PATCH | `/devices/{id}` | API Key | `DeviceUpdate` | `DeviceResponse` | N/A | ✅ |
| Telemetry Latest | GET | `/devices/{id}/telemetry/latest` | Device JWT | - | `TelemetryReading` | telemetryApi.latest() | ✅ |
| Telemetry History | GET | `/devices/{id}/telemetry/history` | Device JWT | Query params | `TelemetryHistoryResponse` | telemetryApi.history() | ✅ |
| Telemetry Ingest | POST | `/telemetry` | Device JWT | `TelemetryPayload` | `TelemetryIngestResponse` | N/A (device) | ✅ |
| Telemetry Batch | POST | `/telemetry/batch` | Device JWT | `BatchTelemetryPayload` | `BatchTelemetryResult` | N/A (device) | ✅ |
| Dashboard | GET | `/devices/{id}/dashboard` | **MISSING** | - | **MISSING** | dashboardApi.get() | ❌ **MISSING** |
| Water Quality | GET | `/water-quality` | Device JWT | - | `WaterQuality` | waterQualityApi.get() | ✅ |
| WQ Trends | GET | `/water-quality/trends` | Device JWT | Query | - | waterQualityApi.trends() | ✅ |
| WQ Anomalies | GET | `/water-quality/anomalies` | Device JWT | Query | - | waterQualityApi.anomalies() | ✅ |
| Filter Health | GET | `/filter-health` | Device JWT | - | `FilterHealth` | filterHealthApi.get() | ✅ |
| Filter Risk | GET | `/filter-health/risk` | Device JWT | - | `FailureRisk` | filterHealthApi.risk() | ✅ |
| Filter Baseline | GET | `/filter-health/baseline` | Device JWT | - | `BaselineMetrics` | filterHealthApi.baseline() | ✅ |
| RUL Stability | GET | `/filter-health/rul-stability` | Device JWT | - | `RULStabilityReport` | filterHealthApi.rulStability() | ✅ |
| Maintenance Band | GET | `/filter-health/maintenance-band` | Device JWT | - | - | filterHealthApi.maintenanceBand() | ✅ |
| Counterfactual | GET | `/filter-health/counterfactual` | Device JWT | - | `CounterfactualAnalysis` | filterHealthApi.counterfactual() | ✅ |
| Purification | GET | `/purification-performance` | Device JWT | - | `PurificationPerformance` | purificationApi.get() | ✅ |
| Purification History | GET | `/purification-performance/history` | Device JWT | Query | - | purificationApi.history() | ✅ |
| Diagnostics | GET | `/diagnostics` | Device JWT | - | `DiagnosticsData` | diagnosticsApi.get() | ✅ |
| Alerts List | GET | `/alerts` | Device JWT | Query | `PaginatedResponse<Alert>` | alertsApi.list() | ✅ |
| Alert Detail | GET | `/alerts/{id}` | Device JWT | - | `Alert` | alertsApi.get() | ✅ |
| Alert Acknowledge | POST | `/alerts/{id}/acknowledge` | Device JWT | `AlertAcknowledgeRequest` | `Alert` | alertsApi.acknowledge() | ✅ |
| Alert Resolve | POST | `/alerts/{id}/resolve` | Device JWT | `AlertResolveRequest` | `Alert` | alertsApi.resolve() | ✅ |
| Alert Snooze | POST | `/alerts/{id}/snooze` | Device JWT | `AlertSnoozeRequest` | `Alert` | alertsApi.snooze() | ✅ |
| Maintenance History | GET | `/maintenance/history` | Device JWT | - | `MaintenanceEvent[]` | maintenanceApi.history() | ✅ |
| Filter Replacement | POST | `/maintenance/filter-replacement` | Device JWT | - | `MaintenanceEvent` | maintenanceApi.filterReplacement() | ✅ |
| Calibration | POST | `/maintenance/calibration` | Device JWT | - | `MaintenanceEvent` | maintenanceApi.calibration() | ✅ |
| Safety Config | GET | `/safety/config` | Device JWT | - | - | N/A | ✅ |
| Safety Test | POST | `/safety/test` | Device JWT | - | - | N/A | ✅ |
| Safety Action | POST | `/safety/action` | Device JWT | - | - | N/A | ✅ |
| Safety Events | GET | `/safety/events` | Device JWT | - | - | N/A | ✅ |
| Safety Audit | GET | `/safety/audit` | Device JWT | - | - | N/A | ✅ |
| Notifications Config | GET | `/notifications/providers` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/filters` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/filters/install` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/filters/replace` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/filters/compatibility/check` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/events` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/events` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/workflows/{id}/transition` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/baseline/{device_id}` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/recommendations` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/calibration` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/calibration/due` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/verification/start` | Device JWT | - | - | N/A | ✅ |
| Maintenance | POST | `/maintenance/verification/{id}/complete` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/verification/{id}` | Device JWT | - | - | N/A | ✅ |
| Maintenance | GET | `/maintenance/recommendations` | Device JWT | - | - | N/A | ✅ |
| Safety Config | GET | `/safety/config` | Device JWT | - | - | N/A | ✅ |
| Safety Test | POST | `/safety/test` | Device JWT | - | - | N/A | ✅ |
| Safety Action | POST | `/safety/action` | Device JWT | - | - | N/A | ✅ |
| Safety Events | GET | `/safety/events` | Device JWT | - | - | N/A | ✅ |
| Safety Audit | GET | `/safety/audit` | Device JWT | - | - | N/A | ✅ |

### Missing Endpoints (Critical Gaps)

| Endpoint | Required By | Priority |
|----------|-------------|----------|
| `/devices/{id}/dashboard` | DashboardPage, useDashboard hook | **CRITICAL** |
| `/devices/{id}/telemetry/latest` (device-scoped) | Device-scoped telemetry | HIGH |
| `/water-quality/trends` pagination | WaterQualityPage | MEDIUM |
| `/water-quality/anomalies` pagination | WaterQualityPage | MEDIUM |
| `/filter-health/counterfactual` | Already exists | ✅ |
| `/diagnostics` history | DiagnosticsPage | MEDIUM |
| `/alerts` WebSocket events | AlertsPage, DashboardPage | ✅ (exists) |
| `/notifications` list | NotificationsPage | ✅ (exists) |
| `/notifications/test` | NotificationsPage | ✅ (exists) |

### Frontend Hooks Integration Status

| Hook | Endpoint | Status | Notes |
|------|----------|--------|-------|
| `useDashboard` | `/devices/{id}/dashboard` | ❌ **MISSING** | Uses hardcoded DEVICE_ID |
| `useDashboard` | WebSocket | ✅ | Works via WebSocket |
| `useTelemetry` | `/telemetry/latest` | ✅ | Works |
| `useTelemetry` | `/telemetry/history` | ✅ | Works |
| `useWaterQuality` | `/water-quality` | ✅ | Works |
| `useFilterHealth` | `/filter-health` | ✅ | Works |
| `useFilterHealth.risk` | `/filter-health/risk` | ✅ | Works |
| `useFilterHealth.baseline` | `/filter-health/baseline` | ✅ | Works |
| `useFilterHealth.rulStability` | `/filter-health/rul-stability` | ✅ | Works |
| `useFilterHealth.maintenanceBand` | `/filter-health/maintenance-band` | ✅ | Works |
| `useFilterHealth.counterfactual` | `/filter-health/counterfactual` | ✅ | Works |
| `usePurification` | `/purification-performance` | ✅ | Works |
| `useDiagnostics` | `/diagnostics` | ✅ | Works |
| `useDevice` | `/devices/{id}` | ✅ | Works |
| `useDeviceList` | `/devices` | ✅ | Works |
| `useAlerts` | `/alerts` | ✅ | Works |
| `useAlert` | `/alerts/{id}` | ✅ | Works |
| `useAcknowledgeAlert` | POST `/alerts/{id}/acknowledge` | ✅ | Works |
| `useResolveAlert` | POST `/alerts/{id}/resolve` | ✅ | Works |
| `useSnoozeAlert` | POST `/alerts/{id}/snooze` | ✅ | Works |
| `useAlert` | `/alerts/{id}` | ✅ | Works |
| `useMaintenanceHistory` | `/maintenance/history` | ✅ | Works |
| `useFilterReplacement` | POST `/maintenance/filter-replacement` | ✅ | Works |
| `useCalibration` | POST `/maintenance/calibration` | ✅ | Works |
| `useWebSocket` | WebSocket | ✅ | Works |
| `useDevice` | `/devices/{id}` | ✅ | Works |
| `useDeviceList` | `/devices` | ✅ | Works |
| `useDashboard` | **MISSING** | ❌ | **CRITICAL** |
| `usePurification` | ✅ | Works |
| `useDiagnostics` | ✅ | Works |
| `useAlerts` | ✅ | Works |
| `useFilterHealth` | ✅ | Works |
| `useWaterQuality` | ✅ | Works |
| `useTelemetry` | ✅ | Works |
| `useDevice` | ✅ | Works |

### Critical Missing Endpoint: `/devices/{id}/dashboard`

The frontend `DashboardPage` and `useDashboard` hook expect a composite endpoint that returns `DashboardData` (composite of device, latest_telemetry, water_quality, filter_health, diagnostics, purification, active_alert, data_freshness_seconds).

This is the **most critical missing endpoint** blocking dashboard integration.

### Data Provenance Fields Needed

The backend needs to add provenance fields to all responses:
- `source: 'MEASURED' | 'SIMULATED' | 'CALCULATED' | 'MODEL_PREDICTED'`
- `model_version` (for predicted values)
- `calculation_version` (for calculated values)
- `simulated: boolean` flag for simulator data

### WebSocket Events

Current events:
- `telemetry` - new telemetry data
- `alert_created` - new alert
- `alert_updated` - alert state changed
- `safety_action` - safety action executed
- `device_status` - device status changed
- `pong` - heartbeat

Frontend uses `useWebSocket` hook which handles reconnection, ping/pong, and message routing.