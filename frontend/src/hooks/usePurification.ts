import { useQuery } from '@tanstack/react-query';
import { purificationApi } from '@/api/endpoints';
import type { PurificationPerformance } from '@/types/api';

export function usePurification(deviceId: string) {
  return useQuery<PurificationPerformance>({
    queryKey: ['purification', deviceId],
    queryFn: () => purificationApi.get(deviceId),
    enabled: !!deviceId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}
