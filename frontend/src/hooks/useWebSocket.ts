import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WebSocketManager, type WSConnectionStatus } from '@/api/websocket';
import type { WSMessage, TelemetryReading } from '@/types/api';

export function useWebSocket(deviceId: string) {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<WSConnectionStatus>('disconnected');
  const managerRef = useRef<WebSocketManager | null>(null);

  const handleMessage = useCallback(
    (message: WSMessage) => {
      switch (message.type) {
        case 'telemetry':
          queryClient.setQueryData<TelemetryReading>(
            ['telemetry', 'latest', deviceId],
            message.data as TelemetryReading
          );
          break;

        case 'alert_created':
        case 'alert_updated':
          queryClient.invalidateQueries({ queryKey: ['alerts'] });
          break;

        case 'device_status':
          queryClient.invalidateQueries({ queryKey: ['device'] });
          break;
      }
    },
    [deviceId, queryClient]
  );

  useEffect(() => {
    if (!deviceId) return;

    const manager = new WebSocketManager({
      deviceId,
      onMessage: handleMessage,
      onStatusChange: setStatus,
    });

    managerRef.current = manager;
    manager.connect();

    return () => {
      manager.disconnect();
      managerRef.current = null;
    };
  }, [deviceId, handleMessage]);

  return { status };
}
