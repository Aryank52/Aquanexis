import { useQuery } from '@tanstack/react-query';
import { waterQualityApi } from '@/api/endpoints';
import type { WaterQuality } from '@/types/api';

export function useWaterQuality(deviceId: string) {
  return useQuery<WaterQuality>({
    queryKey: ['water-quality', deviceId],
    queryFn: () => waterQualityApi.get(deviceId),
    enabled: !!deviceId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}
