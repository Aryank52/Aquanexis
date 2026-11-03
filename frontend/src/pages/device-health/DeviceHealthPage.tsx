import { Cpu, Wifi, WifiOff, Clock, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useDevice } from '@/hooks/useDevice';
import { useLatestTelemetry } from '@/hooks/useTelemetry';
import type { DeviceStatus, QualityFlags } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const statusConfig: Record<
  DeviceStatus,
  { variant: 'success' | 'warning' | 'critical' | 'info'; icon: typeof Wifi }
> = {
  online: { variant: 'success', icon: Wifi },
  degraded: { variant: 'warning', icon: Wifi },
  offline: { variant: 'critical', icon: WifiOff },
  maintenance: { variant: 'info', icon: Wifi },
  error: { variant: 'critical', icon: WifiOff },
};

const sensorMeta: Record<string, { label: string; unit: string }> = {
  tds: { label: 'TDS', unit: 'ppm' },
  ec: { label: 'EC', unit: 'µS/cm' },
  ph: { label: 'pH', unit: '' },
  turbidity: { label: 'Turbidity', unit: 'NTU' },
  temperature: { label: 'Temperature', unit: '°C' },
  flow: { label: 'Feed Flow', unit: 'L/min' },
  pressure: { label: 'Pressure', unit: 'kPa' },
  tank_level: { label: 'Tank Level', unit: '%' },
  pump_current: { label: 'Pump Current', unit: 'A' },
  permeate_flow: { label: 'Permeate Flow', unit: 'L/min' },
  reject_flow: { label: 'Reject Flow', unit: 'L/min' },
};

function checkColor(status: string): string {
  if (status === 'OK') return 'text-success';
  if (status === 'SUSPECT') return 'text-warning';
  return 'text-critical';
}

function sensorOverallVariant(flags: QualityFlags): 'success' | 'warning' | 'critical' {
  const vals = [flags.range, flags.rate, flags.cross_sensor];
  if (vals.some(v => v === 'BAD')) return 'critical';
  if (vals.some(v => v === 'SUSPECT')) return 'warning';
  return 'success';
}

export function DeviceHealthPage() {
  const device = useDevice(DEVICE_ID);
  const telemetry = useLatestTelemetry(DEVICE_ID);

  if (device.isError) {
    return (
      <QueryError
        message={(device.error as Error)?.message ?? 'Failed to load device'}
        onRetry={device.refetch}
      />
    );
  }

  const devStatus = device.data?.status ?? 'offline';
  const cfg = statusConfig[devStatus] ?? statusConfig.offline;
  const StatusIcon = cfg.icon;

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-text-primary text-h1 font-semibold">Device Health</h1>
        <p className="mt-1 text-body-sm text-text-secondary">
          Device status, sensor health, and current readings
        </p>
      </div>

      {/* Device Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-text-secondary" /> Device Overview
          </CardTitle>
        </CardHeader>
        <CardContent>
          {device.isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-6 w-48" />
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-4 w-40" />
            </div>
          ) : device.data ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
              <div>
                <div className="text-caption text-text-muted">Name</div>
                <div className="text-data font-medium">{device.data.name}</div>
              </div>
              <div>
                <div className="text-caption text-text-muted">Serial Number</div>
                <div className="font-mono text-data">{device.data.serial_number}</div>
              </div>
              <div>
                <div className="text-caption text-text-muted">Firmware</div>
                <div className="font-mono text-data">{device.data.firmware_version}</div>
              </div>
              <div>
                <div className="text-caption text-text-muted">Status</div>
                <div className="mt-0.5 flex items-center gap-2">
                  <StatusIcon className={cn('h-4 w-4', `text-${cfg.variant}`)} />
                  <Badge variant={cfg.variant}>{devStatus}</Badge>
                </div>
              </div>
              <div>
                <div className="text-caption text-text-muted">Last Seen</div>
                <div className="flex items-center gap-1 text-body-sm">
                  <Clock className="h-3 w-3 text-text-muted" />
                  {device.data.last_seen
                    ? formatDistanceToNow(new Date(device.data.last_seen), { addSuffix: true })
                    : 'Never'}
                </div>
              </div>
            </div>
          ) : null}
        </CardContent>
      </Card>

      {/* Sensor Health Grid */}
      <div>
        <h2 className="text-text-primary mb-4 text-h2 font-semibold">Sensor Health</h2>
        {telemetry.isLoading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {Array.from({ length: 8 }).map((_, i) => (
              <Skeleton key={i} className="h-24 w-full rounded-card" />
            ))}
          </div>
        ) : telemetry.data?.quality?.flags ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
            {Object.entries(telemetry.data.quality.flags).map(([sensor, flags]) => {
              const meta = sensorMeta[sensor] ?? { label: sensor.replace(/_/g, ' '), unit: '' };
              const variant = sensorOverallVariant(flags);
              return (
                <Card key={sensor}>
                  <CardContent className="p-3">
                    <div className="mb-2 flex items-center justify-between">
                      <span className="text-text-primary text-body-sm font-medium capitalize">
                        {meta.label}
                      </span>
                      <Badge variant={variant}>
                        {variant === 'success' ? 'OK' : variant === 'warning' ? 'Suspect' : 'Bad'}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-caption">
                      <div className="flex justify-between">
                        <span className="text-text-muted">Range</span>
                        <span className={checkColor(flags.range)}>{flags.range}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">Rate</span>
                        <span className={checkColor(flags.rate)}>{flags.rate}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-text-muted">Cross-sensor</span>
                        <span className={checkColor(flags.cross_sensor)}>{flags.cross_sensor}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        ) : (
          <Card>
            <CardContent className="p-4 text-body-sm text-text-muted">
              No sensor quality data available
            </CardContent>
          </Card>
        )}
      </div>

      {/* Current Readings */}
      <div>
        <h2 className="text-text-primary mb-4 text-h2 font-semibold">Current Readings</h2>
        {telemetry.isLoading ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-16 w-full rounded-card" />
            ))}
          </div>
        ) : telemetry.data?.readings ? (
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
            {Object.entries(telemetry.data.readings)
              .filter(([, v]) => v != null && typeof v === 'number')
              .map(([key, value]) => {
                const meta = sensorMeta[key] ?? { label: key.replace(/_/g, ' '), unit: '' };
                return (
                  <Card key={key}>
                    <CardContent className="p-3 text-center">
                      <div className="text-data-lg">
                        {(value as number).toFixed(
                          key === 'ph'
                            ? 1
                            : key === 'flow' || key === 'permeate_flow' || key === 'reject_flow'
                              ? 2
                              : 0
                        )}
                      </div>
                      <div className="text-caption text-text-muted">{meta.label}</div>
                      {meta.unit && <div className="text-caption text-text-muted">{meta.unit}</div>}
                    </CardContent>
                  </Card>
                );
              })}
          </div>
        ) : (
          <Card>
            <CardContent className="p-4 text-body-sm text-text-muted">
              No telemetry data available
            </CardContent>
          </Card>
        )}
      </div>

      {/* Calibration Info */}
      <Card>
        <CardHeader>
          <CardTitle>Calibration Data</CardTitle>
        </CardHeader>
        <CardContent>
          {device.isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : device.data?.calibration && Object.keys(device.data.calibration).length > 0 ? (
            <pre className="overflow-x-auto rounded-button bg-surface p-3 font-mono text-body-sm text-text-secondary">
              {JSON.stringify(device.data.calibration, null, 2)}
            </pre>
          ) : (
            <p className="text-body-sm text-text-muted">No calibration data recorded</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
