import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { maintenanceApi } from '@/api/endpoints';
import type {
  FilterCatalogResponse,
  FilterCatalogCreate,
  FilterCatalogUpdate,
  InstalledFilterResponse,
  InstalledFilterInstall,
  InstalledFilterReplace,
  CompatibilityCheckRequest,
  CompatibilityCheckResponse,
  MaintenanceEventResponse,
  MaintenanceEventCreate,
  MaintenanceWorkflowResponse,
  MaintenanceWorkflowTransition,
  CalibrationRecordResponse,
  CalibrationRecordCreate,
  CalibrationDueResponse,
  VerificationRunStart,
  VerificationRunComplete,
  VerificationRunResponse,
  BaselineVersionResponse,
  MaintenanceRecommendationResponse,
  MaintenanceEvent,
} from '@/types/api';

// ===== Filter Catalog =====

export function useFilterCatalog(params?: {
  category?: string;
  is_active?: boolean;
  limit?: number;
  offset?: number;
}) {
  return useQuery<FilterCatalogResponse[]>({
    queryKey: ['maintenance', 'filters', params],
    queryFn: () => maintenanceApi.listFilters(params),
  });
}

export function useFilter(filterId: string) {
  return useQuery<FilterCatalogResponse>({
    queryKey: ['maintenance', 'filters', filterId],
    queryFn: () => maintenanceApi.getFilter(filterId),
    enabled: !!filterId,
  });
}

export function useCreateFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: FilterCatalogCreate) => maintenanceApi.createFilter(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'filters'] });
    },
  });
}

export function useUpdateFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ filterId, data }: { filterId: string; data: FilterCatalogUpdate }) =>
      maintenanceApi.updateFilter(filterId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'filters'] });
    },
  });
}

// ===== Installed Filters =====

export function useInstalledFilters(deviceId: string) {
  return useQuery<InstalledFilterResponse[]>({
    queryKey: ['maintenance', 'installed-filters', deviceId],
    queryFn: () => maintenanceApi.listInstalledFilters(deviceId),
    enabled: !!deviceId,
  });
}

export function useInstalledFilter(deviceId: string, stagePosition: number) {
  return useQuery<InstalledFilterResponse>({
    queryKey: ['maintenance', 'installed-filters', deviceId, stagePosition],
    queryFn: () => maintenanceApi.getInstalledFilter(deviceId, stagePosition),
    enabled: !!deviceId && stagePosition > 0,
  });
}

export function useInstallFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: string; data: InstalledFilterInstall }) =>
      maintenanceApi.installFilter(deviceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'installed-filters'] });
    },
  });
}

export function useReplaceFilter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ deviceId, data }: { deviceId: string; data: InstalledFilterReplace }) =>
      maintenanceApi.replaceFilter(deviceId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'installed-filters'] });
      queryClient.invalidateQueries({ queryKey: ['filter-health'] });
    },
  });
}

export function useFilterInstance(instanceId: string) {
  return useQuery<InstalledFilterResponse>({
    queryKey: ['maintenance', 'filter-instance', instanceId],
    queryFn: () => maintenanceApi.getFilterInstance(instanceId),
    enabled: !!instanceId,
  });
}

// ===== Compatibility Check =====

export function useCheckCompatibility() {
  return useMutation<CompatibilityCheckResponse, Error, CompatibilityCheckRequest>({
    mutationFn: data => maintenanceApi.checkCompatibility(data),
  });
}

// ===== Maintenance Events =====

export function useMaintenanceEvents(params?: {
  device_id?: string;
  event_type?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<MaintenanceEventResponse[]>({
    queryKey: ['maintenance', 'events', params],
    queryFn: () => maintenanceApi.listEvents(params),
  });
}

export function useCreateMaintenanceEvent() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: MaintenanceEventCreate) => maintenanceApi.createEvent(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'events'] });
    },
  });
}

// ===== Maintenance Workflows =====

export function useWorkflow(workflowId: string) {
  return useQuery<MaintenanceWorkflowResponse>({
    queryKey: ['maintenance', 'workflows', workflowId],
    queryFn: () => maintenanceApi.getWorkflow(workflowId),
    enabled: !!workflowId,
  });
}

export function useTransitionWorkflow() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      workflowId,
      data,
    }: {
      workflowId: string;
      data: MaintenanceWorkflowTransition;
    }) => maintenanceApi.transitionWorkflow(workflowId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'workflows'] });
    },
  });
}

// ===== Calibration =====

export function useCalibrationDue(deviceId: string) {
  return useQuery<CalibrationDueResponse[]>({
    queryKey: ['maintenance', 'calibration', 'due', deviceId],
    queryFn: () => maintenanceApi.getCalibrationDue(deviceId),
    enabled: !!deviceId,
  });
}

export function useCalibrationRecords(
  deviceId: string,
  params?: { sensor_type?: string; limit?: number }
) {
  return useQuery<CalibrationRecordResponse[]>({
    queryKey: ['maintenance', 'calibration', 'records', deviceId, params],
    queryFn: () => maintenanceApi.listCalibrationRecords(deviceId, params),
    enabled: !!deviceId,
  });
}

export function useRecordCalibration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: CalibrationRecordCreate) => maintenanceApi.recordCalibration(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'calibration'] });
    },
  });
}

// ===== Verification =====

export function useStartVerification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: VerificationRunStart) => maintenanceApi.startVerification(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'verification'] });
    },
  });
}

export function useCompleteVerification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      verificationId,
      data,
    }: {
      verificationId: string;
      data: VerificationRunComplete;
    }) => maintenanceApi.completeVerification(verificationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'verification'] });
      queryClient.invalidateQueries({ queryKey: ['maintenance', 'baseline'] });
    },
  });
}

export function useVerification(verificationId: string) {
  return useQuery<VerificationRunResponse>({
    queryKey: ['maintenance', 'verification', verificationId],
    queryFn: () => maintenanceApi.getVerification(verificationId),
    enabled: !!verificationId,
  });
}

// ===== Baseline Versions =====

export function useActiveBaseline(deviceId: string) {
  return useQuery<BaselineVersionResponse>({
    queryKey: ['maintenance', 'baseline', deviceId],
    queryFn: () => maintenanceApi.getActiveBaseline(deviceId),
    enabled: !!deviceId,
  });
}

// ===== Maintenance Recommendations =====

export function useMaintenanceRecommendations(deviceId: string) {
  return useQuery<MaintenanceRecommendationResponse[]>({
    queryKey: ['maintenance', 'recommendations', deviceId],
    queryFn: () => maintenanceApi.getRecommendations(deviceId),
    enabled: !!deviceId,
  });
}

// ===== Legacy hooks for backward compatibility =====

export function useMaintenanceHistory(deviceId: string) {
  return useQuery<MaintenanceEvent[]>({
    queryKey: ['maintenance', deviceId],
    queryFn: () => maintenanceApi.history(deviceId),
    enabled: !!deviceId,
  });
}

export function useFilterReplacement() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { device_id: string; performed_by: string; notes?: string }) =>
      maintenanceApi.filterReplacement(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] });
      queryClient.invalidateQueries({ queryKey: ['filter-health'] });
    },
  });
}
