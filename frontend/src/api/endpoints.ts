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
  // Notifications
  NotificationOutboxResponse,
  NotificationStatsResponse,
  NotificationProviderConfigResponse,
  NotificationProviderConfigCreate,
  NotificationProviderConfigUpdate,
  NotificationTemplateResponse,
  NotificationTemplateCreate,
  NotificationTestRequest,
  NotificationTestResponse,
  // Maintenance - Filter Catalog
  FilterCatalogResponse,
  FilterCatalogCreate,
  FilterCatalogUpdate,
  // Maintenance - Installed Filters
  InstalledFilterResponse,
  InstalledFilterInstall,
  InstalledFilterReplace,
  // Maintenance - Compatibility
  CompatibilityCheckRequest,
  CompatibilityCheckResponse,
  // Maintenance - Events
  MaintenanceEventResponse,
  MaintenanceEventCreate,
  // Maintenance - Workflows
  MaintenanceWorkflowResponse,
  MaintenanceWorkflowTransition,
  // Maintenance - Calibration
  CalibrationRecordResponse,
  CalibrationRecordCreate,
  CalibrationDueResponse,
  // Maintenance - Verification
  VerificationRunStart,
  VerificationRunComplete,
  VerificationRunResponse,
  // Maintenance - Baseline
  BaselineVersionResponse,
  // Maintenance - Recommendations
  MaintenanceRecommendationResponse,
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

  // Filter Catalog
  listFilters: (params?: { category?: string; is_active?: boolean; limit?: number; offset?: number }) =>
    apiClient.get<FilterCatalogResponse[]>('/maintenance/filters', { params }).then((r) => r.data),

  getFilter: (filterId: string) =>
    apiClient.get<FilterCatalogResponse>(`/maintenance/filters/${filterId}`).then((r) => r.data),

  createFilter: (data: FilterCatalogCreate) =>
    apiClient.post<FilterCatalogResponse>('/maintenance/filters', data).then((r) => r.data),

  updateFilter: (filterId: string, data: FilterCatalogUpdate) =>
    apiClient.patch<FilterCatalogResponse>(`/maintenance/filters/${filterId}`, data).then((r) => r.data),

  // Installed Filters
  listInstalledFilters: (deviceId: string) =>
    apiClient.get<InstalledFilterResponse[]>(`/maintenance/devices/${deviceId}/filters`).then((r) => r.data),

  getInstalledFilter: (deviceId: string, stagePosition: number) =>
    apiClient.get<InstalledFilterResponse>(`/maintenance/devices/${deviceId}/filters/${stagePosition}`).then((r) => r.data),

  installFilter: (deviceId: string, data: InstalledFilterInstall) =>
    apiClient.post<InstalledFilterResponse>(`/maintenance/devices/${deviceId}/filters/install`, data).then((r) => r.data),

  replaceFilter: (deviceId: string, data: InstalledFilterReplace) =>
    apiClient.post<InstalledFilterResponse>(`/maintenance/devices/${deviceId}/filters/replace`, data).then((r) => r.data),

  getFilterInstance: (instanceId: string) =>
    apiClient.get<InstalledFilterResponse>(`/maintenance/filters/instances/${instanceId}`).then((r) => r.data),

  // Compatibility Check
  checkCompatibility: (data: CompatibilityCheckRequest) =>
    apiClient.post<CompatibilityCheckResponse>('/maintenance/filters/compatibility/check', data).then((r) => r.data),

  // Maintenance Events
  listEvents: (params?: { device_id?: string; event_type?: string; start?: string; end?: string; limit?: number; offset?: number }) =>
    apiClient.get<MaintenanceEventResponse[]>('/maintenance/events', { params }).then((r) => r.data),

  createEvent: (data: MaintenanceEventCreate) =>
    apiClient.post<MaintenanceEventResponse>('/maintenance/events', data).then((r) => r.data),

  // Maintenance Workflows
  getWorkflow: (workflowId: string) =>
    apiClient.get<MaintenanceWorkflowResponse>(`/maintenance/workflows/${workflowId}`).then((r) => r.data),

  transitionWorkflow: (workflowId: string, data: MaintenanceWorkflowTransition) =>
    apiClient.post<MaintenanceWorkflowResponse>(`/maintenance/workflows/${workflowId}/transition`, data).then((r) => r.data),

  // Calibration
  getCalibrationDue: (deviceId: string) =>
    apiClient.get<CalibrationDueResponse[]>(`/maintenance/calibration/due`, { params: { device_id: deviceId } }).then((r) => r.data),

  listCalibrationRecords: (deviceId: string, params?: { sensor_type?: string; limit?: number }) =>
    apiClient.get<CalibrationRecordResponse[]>(`/maintenance/calibration`, { params: { device_id: deviceId, ...params } }).then((r) => r.data),

  recordCalibration: (data: CalibrationRecordCreate) =>
    apiClient.post<CalibrationRecordResponse>('/maintenance/calibration', data).then((r) => r.data),

  // Verification
  startVerification: (data: VerificationRunStart) =>
    apiClient.post<VerificationRunResponse>('/maintenance/verification/start', data).then((r) => r.data),

  completeVerification: (verificationId: string, data: VerificationRunComplete) =>
    apiClient.post<VerificationRunResponse>(`/maintenance/verification/${verificationId}/complete`, data).then((r) => r.data),

  getVerification: (verificationId: string) =>
    apiClient.get<VerificationRunResponse>(`/maintenance/verification/${verificationId}`).then((r) => r.data),

  // Baseline Versions
  getActiveBaseline: (deviceId: string) =>
    apiClient.get<BaselineVersionResponse>(`/maintenance/baseline/${deviceId}`).then((r) => r.data),

  // Maintenance Recommendations
  getRecommendations: (deviceId: string) =>
    apiClient.get<MaintenanceRecommendationResponse[]>(`/maintenance/recommendations`, { params: { device_id: deviceId } }).then((r) => r.data),
};

// ── Notifications ──────────────────────────────────────────────────────────────

export const notificationsApi = {
  list: (params?: {
    device_id?: string;
    alert_id?: string;
    channel?: string;
    status?: string;
    start?: string;
    end?: string;
    limit?: number;
    offset?: number;
  }) =>
    apiClient.get<NotificationOutboxResponse[]>('/notifications', { params }).then((r) => r.data),

  getStats: (deviceId?: string) =>
    apiClient.get<NotificationStatsResponse>('/notifications/stats', { params: { device_id: deviceId } }).then((r) => r.data),

  get: (notificationId: string) =>
    apiClient.get<NotificationOutboxResponse>(`/notifications/${notificationId}`).then((r) => r.data),

  retry: (notificationId: string) =>
    apiClient.post<NotificationOutboxResponse>(`/notifications/${notificationId}/retry`).then((r) => r.data),

  cancel: (notificationId: string) =>
    apiClient.post<NotificationOutboxResponse>(`/notifications/${notificationId}/cancel`).then((r) => r.data),

  // Provider Configs
  listProviderConfigs: (deviceId?: string) =>
    apiClient.get<NotificationProviderConfigResponse[]>('/notifications/providers', { params: { device_id: deviceId } }).then((r) => r.data),

  createProviderConfig: (data: NotificationProviderConfigCreate) =>
    apiClient.post<NotificationProviderConfigResponse>('/notifications/providers', data).then((r) => r.data),

  updateProviderConfig: (configId: string, data: NotificationProviderConfigUpdate) =>
    apiClient.put<NotificationProviderConfigResponse>(`/notifications/providers/${configId}`, data).then((r) => r.data),

  deleteProviderConfig: (configId: string) =>
    apiClient.delete(`/notifications/providers/${configId}`).then((r) => r.data),

  // Templates
  listTemplates: (channel?: string) =>
    apiClient.get<NotificationTemplateResponse[]>('/notifications/templates', { params: { channel } }).then((r) => r.data),

  createTemplate: (data: NotificationTemplateCreate) =>
    apiClient.post<NotificationTemplateResponse>('/notifications/templates', data).then((r) => r.data),

  // Test
  testNotification: (data: NotificationTestRequest) =>
    apiClient.post<NotificationTestResponse>('/notifications/test', data).then((r) => r.data),

  // Worker Stats
  getWorkerStats: () =>
    apiClient.get('/notifications/worker/stats').then((r) => r.data),
};
