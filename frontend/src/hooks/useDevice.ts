import { useQuery } from '@tanstack/react-query';
import { deviceApi } from '@/api/endpoints';
import type { Device } from '@/types/api';

export function useDevice(deviceId: string) {
  return useQuery<Device>({
    queryKey: ['device', deviceId],
    queryFn: () => deviceApi.get(deviceId),
    enabled: !!deviceId,
  });
}

export function useDeviceList() {
  return useQuery<Device[]>({
    queryKey: ['device', 'list'],
    queryFn: () => deviceApi.list(),
  });
}
