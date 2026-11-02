import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '@/api/endpoints';
import type { DashboardData } from '@/types/api';

export function useDashboard(deviceId: string) {
  return useQuery<DashboardData>({
    queryKey: ['dashboard', deviceId],
    queryFn: () => dashboardApi.get(deviceId),
    enabled: !!deviceId,
    staleTime: 3000,
    refetchInterval: 5000,
  });
}
