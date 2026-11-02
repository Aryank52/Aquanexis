// ============================================================================
// AquaNexis API Endpoints — typed API calls using the shared client
// ============================================================================
import { apiClient } from './client';
import type {
  Device,
  DashboardData,
  TelemetryReading,
  TelemetryHistoryResponse,
  WaterQuality,
  FilterHealth,
  PurificationPerformance,
  DiagnosticsData,
  Alert,
  AlertAcknowledgeRequest,
  AlertResolveRequest,
  AlertSnoozeRequest,
  MaintenanceEvent,
  BaselineMetrics,
  FailureRisk,
  RULStabilityReport,
  CounterfactualAnalysis,
  HealthCheckResponse,
  LoginRequest,
  LoginResponse,
  PaginatedResponse,
} from '@/types/api';

// ── Auth ─────────────────────────────────────────────────────────────────────

export const authApi = {
  login: (data: LoginRequest) =>
    apiClient.post<LoginResponse>('/auth/login', data).then((r) => r.data),

  logout: () =>
    apiClient.post('/auth/logout').then((r) => r.data),

  refreshToken: (refresh_token: string) =>
    apiClient.post<{ access_token: string; expires_in: number }>(
      '/auth/refresh',
      { refresh_token }
    ).then((r) => r.data),
};

// ── Health ────────────────────────────────────────────────────────────────────

export const healthApi = {
  check: () =>
    apiClient.get<HealthCheckResponse>('/health').then((r) => r.data),

  ready: () =>
    apiClient.get<HealthCheckResponse>('/ready').then((r) => r.data),
};

// ── Devices ──────────────────────────────────────────────────────────────────

export const deviceApi = {
  get: (deviceId: string) =>
    apiClient.get<Device>(`/devices/${deviceId}`).then((r) => r.data),

  list: () =>
    apiClient.get<Device[]>('/devices').then((r) => r.data),

  update: (deviceId: string, data: Partial<Device>) =>
    apiClient.put<Device>(`/devices/${deviceId}`, data).then((r) => r.data),
};

// ── Telemetry ────────────────────────────────────────────────────────────────

export const telemetryApi = {
  latest: (deviceId: string) =>
    apiClient.get<TelemetryReading>(`/devices/${deviceId}/telemetry/latest`)
      .then((r) => r.data),

  history: (
    deviceId: string,
    params: {
      start?: string;
      end?: string;
      sensors?: string;
      interval?: string;
      limit?: number;
    }
  ) =>
    apiClient.get<TelemetryHistoryResponse>(
      `/devices/${deviceId}/telemetry/history`,
      { params }
    ).then((r) => r.data),
};

// ── Dashboard ────────────────────────────────────────────────────────────────

export const dashboardApi = {
  get: (deviceId: string) =>
    apiClient.get<DashboardData>(`/devices/${deviceId}/dashboard`)
      .then((r) => r.data),
};

// ── Water Quality ────────────────────────────────────────────────────────────

export const waterQualityApi = {
  get: (deviceId: string) =>
    apiClient.get<WaterQuality>(`/devices/${deviceId}/water-quality`)
      .then((r) => r.data),

  trends: (deviceId: string, params?: { window?: string }) =>
    apiClient.get(`/devices/${deviceId}/water-quality/trends`, { params })
      .then((r) => r.data),

  anomalies: (deviceId: string, params?: { start?: string; end?: string }) =>
    apiClient.get(`/devices/${deviceId}/water-quality/anomalies`, { params })
      .then((r) => r.data),
};

// ── Filter Health ────────────────────────────────────────────────────────────

export const filterHealthApi = {
  get: (deviceId: string) =>
    apiClient.get<FilterHealth>(`/devices/${deviceId}/filter-health`)
      .then((r) => r.data),

  risk: (deviceId: string) =>
    apiClient.get<FailureRisk>(`/devices/${deviceId}/filter-health/risk`)
      .then((r) => r.data),

  baseline: (deviceId: string) =>
    apiClient.get<BaselineMetrics>(`/devices/${deviceId}/filter-health/baseline`)
      .then((r) => r.data),

  rulStability: (deviceId: string) =>
    apiClient.get<RULStabilityReport>(
      `/devices/${deviceId}/filter-health/rul-stability`
    ).then((r) => r.data),

  maintenanceBand: (deviceId: string) =>
    apiClient.get<{ band: string; fhi: number; rul_days: number }>(
      `/devices/${deviceId}/filter-health/maintenance-band`
    ).then((r) => r.data),

  counterfactual: (deviceId: string) =>
    apiClient.get<CounterfactualAnalysis>(
      `/devices/${deviceId}/filter-health/counterfactual`
    ).then((r) => r.data),
};

// ── Purification Performance ─────────────────────────────────────────────────

export const purificationApi = {
  get: (deviceId: string) =>
    apiClient.get<PurificationPerformance>(
      `/devices/${deviceId}/purification-performance`
    ).then((r) => r.data),

  history: (deviceId: string, params?: { start?: string; end?: string }) =>
    apiClient.get(`/devices/${deviceId}/purification-performance/history`, { params })
      .then((r) => r.data),
};

// ── Diagnostics ──────────────────────────────────────────────────────────────

export const diagnosticsApi = {
  get: (deviceId: string) =>
    apiClient.get<DiagnosticsData>(`/devices/${deviceId}/diagnostics`)
      .then((r) => r.data),
};

// ── Alerts ───────────────────────────────────────────────────────────────────

export const alertsApi = {
  list: (
    deviceId: string,
    params?: {
      state?: string;
      severity?: string;
      page?: number;
      page_size?: number;
    }
  ) =>
    apiClient.get<PaginatedResponse<Alert>>(
      `/devices/${deviceId}/alerts`,
      { params }
    ).then((r) => r.data),

  get: (alertId: string) =>
    apiClient.get<Alert>(`/alerts/${alertId}`).then((r) => r.data),

  acknowledge: (alertId: string, data: AlertAcknowledgeRequest) =>
    apiClient.post<Alert>(`/alerts/${alertId}/acknowledge`, data)
      .then((r) => r.data),

  resolve: (alertId: string, data: AlertResolveRequest) =>
    apiClient.post<Alert>(`/alerts/${alertId}/resolve`, data)
      .then((r) => r.data),

  snooze: (alertId: string, data: AlertSnoozeRequest) =>
    apiClient.post<Alert>(`/alerts/${alertId}/snooze`, data)
      .then((r) => r.data),
};

// ── Maintenance ──────────────────────────────────────────────────────────────

export const maintenanceApi = {
  history: (deviceId: string) =>
    apiClient.get<MaintenanceEvent[]>(
      `/devices/${deviceId}/maintenance/history`
    ).then((r) => r.data),

  filterReplacement: (data: {
    device_id: string;
    performed_by: string;
    notes?: string;
  }) =>
    apiClient.post<MaintenanceEvent>(
      '/maintenance/filter-replacement',
      data
    ).then((r) => r.data),

  calibration: (data: {
    device_id: string;
    sensor: string;
    performed_by: string;
    reference_values: Record<string, number>;
    notes?: string;
  }) =>
    apiClient.post<MaintenanceEvent>(
      '/maintenance/calibration',
      data
    ).then((r) => r.data),
};
