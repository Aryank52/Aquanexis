import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { maintenanceApi } from '@/api/endpoints';
import type { MaintenanceEvent } from '@/types/api';

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
    mutationFn: (data: {
      device_id: string;
      performed_by: string;
      notes?: string;
    }) => maintenanceApi.filterReplacement(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] });
      queryClient.invalidateQueries({ queryKey: ['filter-health'] });
    },
  });
}

export function useCalibration() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      device_id: string;
      sensor: string;
      performed_by: string;
      reference_values: Record<string, number>;
      notes?: string;
    }) => maintenanceApi.calibration(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['maintenance'] });
    },
  });
}
