import { useQuery } from '@tanstack/react-query';
import { telemetryApi } from '@/api/endpoints';
import type { TelemetryReading, TelemetryHistoryResponse } from '@/types/api';

export function useLatestTelemetry(deviceId: string) {
  return useQuery<TelemetryReading>({
    queryKey: ['telemetry', 'latest', deviceId],
    queryFn: () => telemetryApi.latest(deviceId),
    enabled: !!deviceId,
    refetchInterval: 5000,
  });
}

export function useTelemetryHistory(
  deviceId: string,
  params: {
    start?: string;
    end?: string;
    sensors?: string;
    interval?: string;
    limit?: number;
  }
) {
  return useQuery<TelemetryHistoryResponse>({
    queryKey: ['telemetry', 'history', deviceId, params],
    queryFn: () => telemetryApi.history(deviceId, params),
    enabled: !!deviceId,
  });
}
