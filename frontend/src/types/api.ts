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
  provenance?: DataProvenance;
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

// --- Water Quality (matches backend AquaScoreResponse/WaterQualityResponse) ---
export type TrendDirection = 'improving' | 'stable' | 'degrading';

export interface ParameterScore {
  parameter: string;
  score: number;
  value: number;
  unit: string;
}

export interface TrendAnalysis {
  parameter: string;
  window: string;
  direction: TrendDirection;
  magnitude: number;
  points: TrendPoint[];
  slope_per_hour: number;
}

export interface TrendPoint {
  timestamp: string;
  value: number;
}

export interface WaterQualityResponse {
  device_id: string;
  timestamp: string;
  aquascore: number;
  parameter_scores: ParameterScore[];
  trends: Record<string, TrendAnalysis>;
  anomaly_score: number | null;
  anomaly_flags: Record<string, number>;
  provenance?: DataProvenance;
}

// Alias for backward compatibility
export type WaterQuality = WaterQualityResponse;

export interface TrendInfo {
  direction: TrendDirection;
  magnitude: number;
}

// --- Filter Health (matches backend FilterHealthResponse/FilterHealthIndex) ---
export type MaintenanceBand = 'NORMAL' | 'MONITOR' | 'PLAN_MAINTENANCE' | 'REPLACE_RECOMMENDED';
export type PredictionConfidence = 'HIGH' | 'MEDIUM' | 'LOW';

export interface FilterHealthResponse {
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
  provenance?: DataProvenance;
}

// Alias for backward compatibility
export type FilterHealth = FilterHealthResponse;

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

// --- Purification Performance (detailed - for detailed views) ---
export interface PurificationPerformance {
  device_id: string;
  timestamp: string;
  rejection_rate: number | null;
  recovery_ratio: number | null;
  permeate_quality: number | null;
  feed_quality: number | null;
  efficiency: number | null;
}

// Simplified version for dashboard (matches backend PurificationPerformanceResponse)
export interface PurificationPerformanceResponse {
  device_id: string;
  timestamp: string;
  rejection_rate: number | null;
  recovery_ratio: number | null;
  permeate_quality: number | null;
  feed_quality: number | null;
  efficiency: number | null;
}

// --- Diagnostics (detailed - for detailed views) ---
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

// Simplified version for dashboard (matches backend DiagnosticsDataResponse)
export interface DiagnosticsDataResponse {
  device_id: string;
  timestamp: string;
  pressure: number | null;
  flow: number | null;
  leak: boolean | null;
  tank: number | null;
  pump: number | null;
}

// --- Alerts (matches backend AlertResponse) ---
export type AlertSeverity = 'INFO' | 'WARNING' | 'CRITICAL';
export type AlertState = 'DETECTED' | 'OPEN' | 'ACKNOWLEDGED' | 'SNOOZED' | 'RESOLVED' | 'AUTO_CLEARED';

export interface AlertResponse {
  id: string;
  device_id: string;
  alert_code: string;
  severity: AlertSeverity;
  status: AlertState;
  title: string;
  message: string;
  trigger_source: string;
  trigger_value: number | null;
  threshold_value: number | null;
  evidence: Record<string, unknown>;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
  resolved_reason: string | null;
  snoozed_until: string | null;
  auto_cleared_at: string | null;
  created_by: string | null;
}

// Alias for backward compatibility
export type Alert = AlertResponse;

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

// --- Dashboard Composite (matches backend DashboardData) ---
export interface DashboardData {
  device: Device;
  latest_telemetry: TelemetryReading | null;
  water_quality: WaterQualityResponse | null;
  filter_health: FilterHealthResponse | null;
  diagnostics: DiagnosticsDataResponse | null;
  purification: PurificationPerformanceResponse | null;
  active_alert: AlertResponse | null;
  data_freshness_seconds: number;
}

// --- Dashboard Response Types (matching backend) ---
export interface WaterQualityResponse {
  device_id: string;
  timestamp: string;
  aquascore: number;
  parameter_scores: ParameterScore[];
  trends: Record<string, TrendAnalysis>;
  anomaly_score: number | null;
  anomaly_flags: Record<string, number>;
  provenance?: DataProvenance;
}

export interface FilterHealthResponse {
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
  provenance?: DataProvenance;
}

export interface DiagnosticsDataResponse {
  device_id: string;
  timestamp: string;
  pressure: number | null;
  flow: number | null;
  leak: boolean | null;
  tank: number | null;
  pump: number | null;
}

export interface PurificationPerformanceResponse {
  device_id: string;
  timestamp: string;
  rejection_rate: number | null;
  recovery_ratio: number | null;
  permeate_quality: number | null;
  feed_quality: number | null;
  efficiency: number | null;
}

export interface WaterQualityResponse {
  device_id: string;
  timestamp: string;
  aquascore: number;
  parameter_scores: ParameterScore[];
  trends: Record<string, TrendAnalysis>;
  anomaly_score: number | null;
  anomaly_flags: Record<string, number>;
  provenance?: DataProvenance;
}

export interface FilterHealthResponse {
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
  provenance?: DataProvenance;
}

export interface DiagnosticsDataResponse {
  device_id: string;
  timestamp: string;
  pressure: number | null;
  flow: number | null;
  leak: boolean | null;
  tank: number | null;
  pump: number | null;
}

export interface PurificationPerformanceResponse {
  device_id: string;
  timestamp: string;
  rejection_rate: number | null;
  recovery_ratio: number | null;
  permeate_quality: number | null;
  feed_quality: number | null;
  efficiency: number | null;
}

export interface DashboardData {
  device: Device;
  latest_telemetry: TelemetryReading | null;
  water_quality: WaterQualityResponse | null;
  filter_health: FilterHealthResponse | null;
  diagnostics: DiagnosticsDataResponse | null;
  purification: PurificationPerformanceResponse | null;
  active_alert: AlertResponse | null;
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
  | 'sensor_health'
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

// --- Notifications ---
export type NotificationChannel = 'email' | 'sms' | 'webhook' | 'push';
export type NotificationStatus = 'pending' | 'processing' | 'sent' | 'retry' | 'dead_letter' | 'failed';
export type NotificationErrorCategory = 'TRANSIENT' | 'PERMANENT' | 'RATE_LIMITED' | 'QUOTA_EXCEEDED' | 'UNKNOWN';

export interface NotificationOutboxResponse {
  id: string;
  alert_id: string;
  device_id: string;
  channel: NotificationChannel;
  provider: string;
  recipient: string;
  subject: string | null;
  body: string;
  template_name: string | null;
  template_data: Record<string, unknown> | null;
  dedupe_key: string;
  status: NotificationStatus;
  error_category: NotificationErrorCategory | null;
  last_error: string | null;
  attempt_count: number;
  max_attempts: number;
  next_attempt_at: string | null;
  created_at: string;
  sent_at: string | null;
  updated_at: string;
}

export interface NotificationStatsResponse {
  total_pending: number;
  total_processing: number;
  total_sent: number;
  total_retry: number;
  total_dead_letter: number;
  total_failed: number;
}

export interface NotificationProviderConfigResponse {
  id: string;
  device_id: string;
  channel: NotificationChannel;
  provider: string;
  enabled: boolean;
  config: Record<string, unknown>;
  min_severity: string;
  alert_codes: string[] | null;
  rate_limit_per_hour: number | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationProviderConfigCreate {
  device_id: string;
  channel: NotificationChannel;
  provider: string;
  enabled?: boolean;
  config?: Record<string, unknown>;
  min_severity?: string;
  alert_codes?: string[];
  rate_limit_per_hour?: number;
}

export interface NotificationProviderConfigUpdate {
  provider?: string;
  enabled?: boolean;
  config?: Record<string, unknown>;
  min_severity?: string;
  alert_codes?: string[];
  rate_limit_per_hour?: number;
}

export interface NotificationTemplateResponse {
  id: string;
  name: string;
  channel: NotificationChannel;
  subject_template: string | null;
  body_template: string;
  description: string | null;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationTemplateCreate {
  name: string;
  channel: NotificationChannel;
  subject_template?: string;
  body_template: string;
  description?: string;
  is_default?: boolean;
}

export interface NotificationTestRequest {
  device_id?: string;
  channel: NotificationChannel;
  provider?: string;
  recipient: string;
  template_name?: string;
  template_data?: Record<string, unknown>;
}

export interface NotificationTestResponse {
  success: boolean;
  channel: NotificationChannel;
  recipient: string;
  error_category: NotificationErrorCategory | null;
  error_message: string | null;
  provider_response: Record<string, unknown> | null;
}

// --- Maintenance - Filter Catalog ---
export type FilterCategory = 'SEDIMENT' | 'CARBON' | 'RO_MEMBRANE' | 'POST_CARBON' | 'UV' | 'MINERALIZATION' | 'OTHER';

export interface FilterCatalogResponse {
  id: string;
  filter_identifier: string;
  manufacturer: string;
  product_name: string;
  category: FilterCategory;
  purifier_compatibility: string[];
  stage_position: number;
  specifications: Record<string, unknown>;
  connector_details: string | null;
  dimensions_mm: Record<string, number> | null;
  rated_service_interval_days: number | null;
  rated_usage_volume_liters: number | null;
  installation_requirements: string | null;
  maintenance_instructions: string | null;
  datasheet_reference: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface FilterCatalogCreate {
  filter_identifier: string;
  manufacturer: string;
  product_name: string;
  category: FilterCategory;
  purifier_compatibility?: string[];
  stage_position: number;
  specifications?: Record<string, unknown>;
  connector_details?: string;
  dimensions_mm?: Record<string, number>;
  rated_service_interval_days?: number;
  rated_usage_volume_liters?: number;
  installation_requirements?: string;
  maintenance_instructions?: string;
  datasheet_reference?: string;
}

export interface FilterCatalogUpdate {
  manufacturer?: string;
  product_name?: string;
  category?: FilterCategory;
  purifier_compatibility?: string[];
  stage_position?: number;
  specifications?: Record<string, unknown>;
  connector_details?: string;
  dimensions_mm?: Record<string, number>;
  rated_service_interval_days?: number;
  rated_usage_volume_liters?: number;
  installation_requirements?: string;
  maintenance_instructions?: string;
  datasheet_reference?: string;
  is_active?: boolean;
}

// --- Maintenance - Installed Filters ---
export type FilterLifecycleState = 'INSTALLED' | 'ACTIVE' | 'REPLACED' | 'REMOVED' | 'EXPIRED';

export interface InstalledFilterResponse {
  id: string;
  device_id: string;
  catalog_id: string;
  stage_position: number;
  installer: string | null;
  serial_number: string | null;
  batch_identifier: string | null;
  lifecycle_state: FilterLifecycleState;
  cumulative_volume_liters: number;
  operating_hours: number;
  previous_installation_id: string | null;
  removal_date: string | null;
  replacement_reason: string | null;
  created_at: string;
  updated_at: string;
}

export interface InstalledFilterInstall {
  catalog_id: string;
  stage_position: number;
  installer?: string;
  serial_number?: string;
  batch_identifier?: string;
}

export interface InstalledFilterReplace {
  stage_position: number;
  new_catalog_id: string;
  installer?: string;
  serial_number?: string;
  batch_identifier?: string;
  replacement_reason?: string;
}

// --- Maintenance - Compatibility Check ---
export type CompatibilityResult = 'COMPATIBLE' | 'INCOMPATIBLE' | 'UNKNOWN';

export interface CompatibilityCheckRequest {
  purifier_model: string;
  filter_id: string;
  stage_position?: number;
}

export interface CompatibilityCheckResponse {
  result: CompatibilityResult;
  reasons: string[];
  details: Record<string, unknown> | null;
}

// --- Maintenance - Events ---
export interface MaintenanceEventResponse {
  id: string;
  device_id: string;
  event_type: MaintenanceEventType;
  description: string;
  initiated_by: string | null;
  filter_instance_id: string | null;
  evidence: Record<string, unknown>;
  timestamp: string;
  pre_maintenance_state: Record<string, unknown>;
  post_maintenance_state: Record<string, unknown>;
  verification_status: string | null;
  correlation_id: string | null;
  created_at: string;
}

export interface MaintenanceEventCreate {
  device_id: string;
  event_type: MaintenanceEventType;
  description: string;
  initiated_by?: string;
  filter_instance_id?: string;
  evidence?: Record<string, unknown>;
}

// --- Maintenance - Workflows ---
export type MaintenanceWorkflowState = 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface MaintenanceWorkflowTransition {
  new_state: string;
  error_message?: string;
}

export interface MaintenanceWorkflowResponse {
  id: string;
  device_id: string;
  maintenance_event_id: string;
  state: MaintenanceWorkflowState;
  started_at: string | null;
  completed_at: string | null;
  failed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

// --- Maintenance - Calibration ---
export type CalibrationState = 'PENDING' | 'VALID' | 'EXPIRED' | 'OUT_OF_TOLERANCE' | 'FAILED';

export interface CalibrationRecordResponse {
  id: string;
  device_id: string;
  sensor_id: string;
  sensor_type: string;
  calibration_method: string;
  reference_standard: string;
  reference_value: number;
  measured_value: number;
  tolerance: number;
  technician: string | null;
  notes: string | null;
  calibration_date: string;
  correction_offset: number;
  result: string;
  next_calibration_due: string | null;
  calibration_state: CalibrationState;
  created_at: string;
  updated_at: string;
}

export interface CalibrationRecordCreate {
  device_id: string;
  sensor_id: string;
  sensor_type: string;
  calibration_method: string;
  reference_standard: string;
  reference_value: number;
  measured_value: number;
  tolerance: number;
  technician?: string;
  notes?: string;
}

export interface CalibrationDueResponse {
  sensor_type: string;
  sensor_id: string;
  status: string;
  last_calibration: string | null;
  next_due: string | null;
  days_overdue: number | null;
  message: string | null;
}

// --- Maintenance - Verification ---
export type VerificationState = 'PENDING' | 'RUNNING' | 'PASSED' | 'FAILED' | 'CANCELLED';

export interface VerificationRunStart {
  device_id: string;
  maintenance_event_id: string;
  baseline_before?: Record<string, unknown>;
}

export interface VerificationRunComplete {
  current_readings: Record<string, number>;
}

export interface VerificationRunResponse {
  id: string;
  maintenance_event_id: string;
  device_id: string;
  state: VerificationState;
  started_at: string | null;
  completed_at: string | null;
  checks: Array<Record<string, unknown>>;
  overall_result: boolean | null;
  failure_reasons: string[];
  baseline_before: Record<string, unknown> | null;
  baseline_after: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

// --- Maintenance - Baseline Versions ---
export interface BaselineVersionResponse {
  id: string;
  device_id: string;
  version: number;
  maintenance_event_id: string | null;
  is_active: boolean;
  metrics: Record<string, unknown>;
  created_at: string;
  activated_at: string | null;
}

// --- Maintenance - Recommendations ---
export interface MaintenanceRecommendationResponse {
  id: string;
  device_id: string;
  filter_instance_id: string | null;
  trigger: string;
  severity: string;
  evidence: Record<string, unknown>;
  urgency_days: number | null;
  recommended_action: string;
  acknowledged_at: string | null;
  dismissed_at: string | null;
  created_at: string;
}

// --- Data Provenance ---
export type DataProvenance = 'MEASURED' | 'SIMULATED' | 'CALCULATED' | 'MODEL_PREDICTED';

export interface ProvenanceInfo {
  provenance: DataProvenance;
  source?: string;
  model_version?: string;
  calculated_at?: string;
  confidence?: number;
}
