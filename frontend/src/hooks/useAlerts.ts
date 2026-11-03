import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { alertsApi } from '@/api/endpoints';
import type {
  Alert,
  AlertAcknowledgeRequest,
  AlertResolveRequest,
  AlertSnoozeRequest,
  PaginatedResponse,
} from '@/types/api';

export function useAlerts(
  deviceId: string,
  params?: {
    state?: string;
    severity?: string;
    page?: number;
    page_size?: number;
  }
) {
  return useQuery<PaginatedResponse<Alert>>({
    queryKey: ['alerts', deviceId, params],
    queryFn: () => alertsApi.list(deviceId, params),
    enabled: !!deviceId,
  });
}

export function useAlert(alertId: string) {
  return useQuery<Alert>({
    queryKey: ['alerts', 'detail', alertId],
    queryFn: () => alertsApi.get(alertId),
    enabled: !!alertId,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, data }: { alertId: string; data: AlertAcknowledgeRequest }) =>
      alertsApi.acknowledge(alertId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function useResolveAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, data }: { alertId: string; data: AlertResolveRequest }) =>
      alertsApi.resolve(alertId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}

export function useSnoozeAlert() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ alertId, data }: { alertId: string; data: AlertSnoozeRequest }) =>
      alertsApi.snooze(alertId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] });
    },
  });
}
