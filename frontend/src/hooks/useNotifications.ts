import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notificationsApi } from '@/api/endpoints';
import type {
  NotificationOutboxResponse,
  NotificationStatsResponse,
  NotificationProviderConfigResponse,
  NotificationProviderConfigCreate,
  NotificationProviderConfigUpdate,
  NotificationTemplateResponse,
  NotificationTemplateCreate,
  NotificationTestRequest,
  NotificationTestResponse,
  PaginatedResponse,
} from '@/types/api';

export function useNotifications(params?: {
  device_id?: string;
  alert_id?: string;
  channel?: string;
  status?: string;
  start?: string;
  end?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery<NotificationOutboxResponse[]>({
    queryKey: ['notifications', params],
    queryFn: () => notificationsApi.list(params),
  });
}

export function useNotificationStats(deviceId?: string) {
  return useQuery<NotificationStatsResponse>({
    queryKey: ['notifications', 'stats', deviceId],
    queryFn: () => notificationsApi.getStats(deviceId),
    enabled: !!deviceId,
  });
}

export function useNotification(notificationId: string) {
  return useQuery<NotificationOutboxResponse>({
    queryKey: ['notifications', 'detail', notificationId],
    queryFn: () => notificationsApi.get(notificationId),
    enabled: !!notificationId,
  });
}

export function useRetryNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => notificationsApi.retry(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useCancelNotification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (notificationId: string) => notificationsApi.cancel(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
    },
  });
}

export function useProviderConfigs(deviceId?: string) {
  return useQuery<NotificationProviderConfigResponse[]>({
    queryKey: ['notifications', 'providers', deviceId],
    queryFn: () => notificationsApi.listProviderConfigs(deviceId),
    enabled: !!deviceId,
  });
}

export function useCreateProviderConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NotificationProviderConfigCreate) =>
      notificationsApi.createProviderConfig(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'providers'] });
    },
  });
}

export function useUpdateProviderConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      configId,
      data,
    }: {
      configId: string;
      data: NotificationProviderConfigUpdate;
    }) => notificationsApi.updateProviderConfig(configId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'providers'] });
    },
  });
}

export function useDeleteProviderConfig() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (configId: string) => notificationsApi.deleteProviderConfig(configId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'providers'] });
    },
  });
}

export function useTemplates(channel?: string) {
  return useQuery<NotificationTemplateResponse[]>({
    queryKey: ['notifications', 'templates', channel],
    queryFn: () => notificationsApi.listTemplates(channel),
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NotificationTemplateCreate) => notificationsApi.createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications', 'templates'] });
    },
  });
}

export function useTestNotification() {
  return useMutation<NotificationTestResponse, Error, NotificationTestRequest>({
    mutationFn: data => notificationsApi.testNotification(data),
  });
}

export function useWorkerStats() {
  return useQuery({
    queryKey: ['notifications', 'worker', 'stats'],
    queryFn: () => notificationsApi.getWorkerStats(),
  });
}
