import { useQuery } from '@tanstack/react-query';
import { diagnosticsApi } from '@/api/endpoints';
import type { DiagnosticsData } from '@/types/api';

export function useDiagnostics(deviceId: string) {
  return useQuery<DiagnosticsData>({
    queryKey: ['diagnostics', deviceId],
    queryFn: () => diagnosticsApi.get(deviceId),
    enabled: !!deviceId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}
