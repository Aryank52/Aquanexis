import { useQuery } from '@tanstack/react-query';
import { filterHealthApi } from '@/api/endpoints';
import type {
  FilterHealth,
  FailureRisk,
  BaselineMetrics,
  RULStabilityReport,
  CounterfactualAnalysis,
} from '@/types/api';

export function useFilterHealth(deviceId: string) {
  return useQuery<FilterHealth>({
    queryKey: ['filter-health', deviceId],
    queryFn: () => filterHealthApi.get(deviceId),
    enabled: !!deviceId,
    staleTime: 5000,
    refetchInterval: 5000,
  });
}

export function useFailureRisk(deviceId: string) {
  return useQuery<FailureRisk>({
    queryKey: ['filter-health', 'risk', deviceId],
    queryFn: () => filterHealthApi.risk(deviceId),
    enabled: !!deviceId,
  });
}

export function useBaseline(deviceId: string) {
  return useQuery<BaselineMetrics>({
    queryKey: ['filter-health', 'baseline', deviceId],
    queryFn: () => filterHealthApi.baseline(deviceId),
    enabled: !!deviceId,
  });
}

export function useRULStability(deviceId: string) {
  return useQuery<RULStabilityReport>({
    queryKey: ['filter-health', 'rul-stability', deviceId],
    queryFn: () => filterHealthApi.rulStability(deviceId),
    enabled: !!deviceId,
  });
}

export function useCounterfactual(deviceId: string) {
  return useQuery<CounterfactualAnalysis>({
    queryKey: ['filter-health', 'counterfactual', deviceId],
    queryFn: () => filterHealthApi.counterfactual(deviceId),
    enabled: !!deviceId,
  });
}
