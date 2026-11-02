// ============================================================================
// AquaNexis API Types — Matches backend schemas
// ============================================================================

// --- Device ---
export type DeviceStatus = 'online' | 'degraded' | 'offline' | 'maintenance' | 'error';

export interface Device {
  id: string;
  serial_number: string;
  name: string;
  firmware_version: string;
  sensor_config: Record<string, unknown>;
  calibration: Record<string, unknown>;
  safety_config: Record<string, unknown>;
  status: DeviceStatus;
  last_seen: string | null;
  created_at: string;
  updated_at: string;
}

// --- Quality ---
export type QualityState = 'GOOD' | 'SUSPECT' | 'BAD';

export interface QualityFlags {
  range: 'OK' | 'SUSPECT' | 'BAD';
  rate: 'OK' | 'SUSPECT' | 'BAD';
  cross_sensor: 'OK' | 'SUSPECT' | 'BAD';
}

export interface QualityAssessment {
  overall: QualityState;
  flags: Record<string, QualityFlags>;
}

// --- Sensor Reading ---
export interface SensorReadings {
  tds: number | null;
  ec: number | null;
  ph: number | null;
  turbidity: number | null;
  temperature: number | null;
  flow: number | null;
  pressure: number | null;
  tank_level: number | null;
  leak_detected: boolean | null;
  pump_current: number | null;
  permeate_flow: number | null;
  reject_flow: number | null;
  uv_state: boolean | null;
  vibration: number | null;
}

export interface TelemetryReading {
  id: string;
  device_id: string;
  timestamp: string;
  received_at: string;
  readings: SensorReadings;
  quality: QualityAssessment;
}

export interface TelemetryHistoryPoint {
  t: string;
  avg: number;
  min: number;
  max: number;
}

export interface TelemetryHistoryResponse {
  device_id: string;
  interval: string;
  series: Record<string, TelemetryHistoryPoint[]>;
}

// --- Water Quality ---
export type TrendDirection = 'improving' | 'stable' | 'degrading';

export interface ParameterScore {
  parameter: string;
  score: number;
  value: number;
  unit: string;
}

export interface TrendInfo {
  direction: TrendDirection;
  magnitude: number;
}

export interface WaterQuality {
  device_id: string;
  timestamp: string;
  aquascore: number;
  parameter_scores: ParameterScore[];
  trends: Record<string, TrendInfo>;
  anomaly_score: number | null;
  anomaly_flags: Record<string, unknown>;
}

// --- Filter Health ---
export type MaintenanceBand = 'NORMAL' | 'MONITOR' | 'PLAN_MAINTENANCE' | 'REPLACE_RECOMMENDED';
export type PredictionConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FilterHealth {
  device_id: string;
  timestamp: string;
  fsi: number;
  fhi: number;
  rul_days: number | null;
  rul_confidence_lower: number | null;
  rul_confidence_upper: number | null;
  model_name: string;
  model_version: string;
  dataset_version: string | null;
  input_features: Record<string, number>;
  explanation: FilterExplanation | null;
  maintenance_band: MaintenanceBand;
  confidence_level: PredictionConfidence;
}

export interface FilterExplanation {
  top_contributors: ExplanationFactor[];
  model_info: {
    name: string;
    version: string;
    mae_days?: number;
  };
  counterfactual?: CounterfactualAnalysis;
}

export interface ExplanationFactor {
  feature: string;
  contribution: number;
  direction: 'increases' | 'decreases';
  label: string;
}

export interface CounterfactualAnalysis {
  scenarios: CounterfactualScenario[];
}

export interface CounterfactualScenario {
  description: string;
  rul_change_days: number;
  confidence: PredictionConfidence;
}

export interface RULStabilityReport {
  is_stable: boolean;
  jitter_days: number;
  trend_direction: TrendDirection;
  window_hours: number;
  predictions: Array<{ timestamp: string; rul_days: number }>;
}

export interface BaselineMetrics {
  device_id: string;
  flow_baseline: number | null;
  pressure_baseline: number | null;
  delta_p_baseline: number | null;
  turbidity_baseline: number | null;
  tds_baseline: number | null;
  daily_volume_baseline: number | null;
  last_updated: string | null;
}

export interface FailureRisk {
  device_id: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  risk_score: number;
  evidence: RiskEvidence[];
  maintenance_band: MaintenanceBand;
}

export interface RiskEvidence {
  factor: string;
  value: number;
  threshold: number;
  severity: 'low' | 'medium' | 'high';
  description: string;
}

// --- Purification Performance ---
export interface PurificationPerformance {
  device_id: string;
  timestamp: string;
  rejection_rate: number | null;
  recovery_ratio: number | null;
  permeate_quality: number | null;
  feed_quality: number | null;
  efficiency: number | null;
}

// --- Diagnostics ---
export interface DiagnosticsData {
  device_id: string;
  timestamp: string;
  pressure: PressureDiagnostics;
  flow: FlowDiagnostics;
  leak: LeakDiagnostics;
  tank: TankDiagnostics;
  pump: PumpDiagnostics;
}

export interface PressureDiagnostics {
  current_kpa: number;
  trend_1h: number;
  trend_24h: number;
  fouling_indicator: number;
  status: 'normal' | 'elevated' | 'critical';
}

export interface FlowDiagnostics {
  current_lpm: number;
  recovery_ratio: number;
  permeate_lpm: number;
  reject_lpm: number;
  trend_1h: number;
  status: 'normal' | 'low' | 'critical';
}

export interface LeakDiagnostics {
  detected: boolean;
  probability: number;
  sensor_status: 'OK' | 'FAULT';
  flow_delta_lpm: number;
  pressure_drop_kpa: number;
  status: 'dry' | 'suspected' | 'confirmed';
}

export interface TankDiagnostics {
  level_percent: number;
  fill_rate_lpm: number;
  empty_rate_lpm: number;
  stagnation_hours: number;
  status: 'normal' | 'low' | 'empty' | 'stagnation';
}

export interface PumpDiagnostics {
  current_a: number;
  power_w: number;
  efficiency_trend_7d: number;
  runtime_hours: number;
  start_count: number;
  status: 'normal' | 'degraded' | 'fault';
}

// --- Alerts ---
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type AlertState = 'ACTIVE' | 'ACKNOWLEDGED' | 'SNOOZED' | 'RESOLVED';

export interface Alert {
  id: string;
  device_id: string;
  alert_type: string;
  severity: AlertSeverity;
  trigger_source: string;
  dedupe_key: string;
  trigger_value: number | null;
  threshold_value: number | null;
  explanation: AlertExplanation | null;
  state: AlertState;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolved_reason: string | null;
  snoozed_until: string | null;
}

export interface AlertExplanation {
  message: string;
  evidence: AlertEvidence[];
  recommended_action?: string;
}

export interface AlertEvidence {
  label: string;
  value: string | number;
  unit?: string;
  severity?: AlertSeverity;
}

export interface AlertAcknowledgeRequest {
  acknowledged_by: string;
}

export interface AlertResolveRequest {
  resolved_by: string;
  resolved_reason: string;
}

export interface AlertSnoozeRequest {
  snoozed_by: string;
  snooze_duration_minutes: number;
}

// --- Maintenance ---
export type MaintenanceEventType = 'FILTER_REPLACEMENT' | 'CALIBRATION' | 'VERIFICATION';

export interface MaintenanceEvent {
  id: string;
  device_id: string;
  event_type: MaintenanceEventType;
  performed_at: string;
  performed_by: string | null;
  pre_metrics: Record<string, number> | null;
  post_metrics: Record<string, number> | null;
  notes: string | null;
  verified: boolean;
  verification_data: Record<string, unknown> | null;
}

// --- Dashboard Composite ---
export interface DashboardData {
  device: Device;
  latest_telemetry: TelemetryReading | null;
  water_quality: WaterQuality | null;
  filter_health: FilterHealth | null;
  diagnostics: DiagnosticsData | null;
  purification: PurificationPerformance | null;
  active_alert: Alert | null;
  data_freshness_seconds: number;
}

// --- Auth ---
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

export interface AuthUser {
  id: string;
  username: string;
  email: string;
  role: 'admin' | 'engineer' | 'operator' | 'viewer';
  display_name: string;
}

export interface RefreshTokenResponse {
  access_token: string;
  expires_in: number;
}

// --- Health Check ---
export interface HealthCheckResponse {
  status: 'ok' | 'degraded' | 'error';
  services: Record<string, { status: string; detail?: string }>;
}

// --- WebSocket Messages ---
export type WSMessageType =
  | 'telemetry'
  | 'alert_created'
  | 'alert_updated'
  | 'safety_action'
  | 'device_status'
  | 'pong';

export interface WSMessage<T = unknown> {
  type: WSMessageType;
  device_id: string;
  data: T;
  timestamp?: string;
}

// --- Pagination ---
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// --- API Error ---
export interface APIError {
  detail: string;
  status_code: number;
  error_code?: string;
}
