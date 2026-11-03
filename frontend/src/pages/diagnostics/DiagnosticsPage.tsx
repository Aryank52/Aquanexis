import { Gauge, Waves, Droplets, Database, Zap, TrendingUp, TrendingDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useDiagnostics } from '@/hooks/useDiagnostics';
import { useDevice } from '@/hooks/useDevice';
import type { DeviceStatus } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const deviceStatusVariant: Record<DeviceStatus, 'success' | 'warning' | 'critical' | 'info'> = {
  online: 'success',
  degraded: 'warning',
  offline: 'critical',
  maintenance: 'info',
  error: 'critical',
};

function statusBadgeVariant(status: string): 'success' | 'warning' | 'critical' {
  if (['normal', 'dry'].includes(status)) return 'success';
  if (['elevated', 'low', 'suspected', 'degraded', 'stagnation'].includes(status)) return 'warning';
  return 'critical';
}

function TrendIndicator({ value, unit = '' }: { value: number; unit?: string }) {
  if (value > 0)
    return (
      <span className="flex items-center gap-0.5 text-caption text-warning">
        <TrendingUp className="h-3 w-3" />+{value.toFixed(2)}
        {unit}
      </span>
    );
  if (value < 0)
    return (
      <span className="flex items-center gap-0.5 text-caption text-success">
        <TrendingDown className="h-3 w-3" />
        {value.toFixed(2)}
        {unit}
      </span>
    );
  return <span className="text-caption text-text-muted">Stable</span>;
}

export function DiagnosticsPage() {
  const { data, isLoading, isError, error, refetch } = useDiagnostics(DEVICE_ID);
  const device = useDevice(DEVICE_ID);

  if (isError) {
    return (
      <QueryError
        message={(error as Error)?.message ?? 'Failed to load diagnostics'}
        onRetry={refetch}
      />
    );
  }

  const devStatus = device.data?.status ?? 'offline';

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">System Diagnostics</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Pressure, flow, leak, tank, and pump energy diagnostics
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-body-sm text-text-secondary">Device:</span>
          {device.isLoading ? (
            <Skeleton className="h-6 w-20" />
          ) : (
            <Badge variant={deviceStatusVariant[devStatus]}>{devStatus}</Badge>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Pressure Panel */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-text-secondary" /> Pressure
            </CardTitle>
            {!isLoading && data && (
              <Badge variant={statusBadgeVariant(data.pressure.status)}>
                {data.pressure.status}
              </Badge>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : data ? (
              <div className="space-y-3">
                <div className="text-data-lg">
                  {data.pressure.current_kpa.toFixed(0)}{' '}
                  <span className="text-body-sm text-text-muted">kPa</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Fouling Index</span>
                  <span
                    className={cn(
                      'font-medium',
                      data.pressure.fouling_indicator > 0.7
                        ? 'text-critical'
                        : data.pressure.fouling_indicator > 0.4
                          ? 'text-warning'
                          : 'text-success'
                    )}
                  >
                    {(data.pressure.fouling_indicator * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">1h Trend</span>
                  <TrendIndicator value={data.pressure.trend_1h} unit=" kPa" />
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Flow Panel */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Waves className="h-4 w-4 text-text-secondary" /> Flow
            </CardTitle>
            {!isLoading && data && (
              <Badge variant={statusBadgeVariant(data.flow.status)}>{data.flow.status}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : data ? (
              <div className="space-y-3">
                <div className="text-data-lg">
                  {data.flow.current_lpm.toFixed(2)}{' '}
                  <span className="text-body-sm text-text-muted">L/min</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Permeate</span>
                  <span className="font-medium">{data.flow.permeate_lpm.toFixed(2)} L/min</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Reject</span>
                  <span className="font-medium">{data.flow.reject_lpm.toFixed(2)} L/min</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Recovery Ratio</span>
                  <span className="font-medium">
                    {(data.flow.recovery_ratio * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">1h Trend</span>
                  <TrendIndicator value={data.flow.trend_1h} unit=" L/min" />
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Leak Detection Panel */}
        <Card className={cn(data?.leak?.detected && 'border-critical ring-1 ring-critical/20')}>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Droplets className="h-4 w-4 text-text-secondary" /> Leak Detection
            </CardTitle>
            {!isLoading && data && (
              <Badge variant={statusBadgeVariant(data.leak.status)}>{data.leak.status}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : data ? (
              <div className="space-y-3">
                {data.leak.detected && (
                  <div className="rounded-button border border-critical/30 bg-critical/10 px-3 py-2 text-body-sm font-medium text-critical">
                    ⚠ Leak Confirmed
                  </div>
                )}
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Probability</span>
                  <span
                    className={cn(
                      'font-medium',
                      data.leak.probability > 0.7
                        ? 'text-critical'
                        : data.leak.probability > 0.3
                          ? 'text-warning'
                          : 'text-success'
                    )}
                  >
                    {(data.leak.probability * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Flow Delta</span>
                  <span className="font-medium">{data.leak.flow_delta_lpm.toFixed(3)} L/min</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Pressure Drop</span>
                  <span className="font-medium">{data.leak.pressure_drop_kpa.toFixed(1)} kPa</span>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Tank Status Panel */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4 text-text-secondary" /> Tank Status
            </CardTitle>
            {!isLoading && data && (
              <Badge variant={statusBadgeVariant(data.tank.status)}>{data.tank.status}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : data ? (
              <div className="space-y-3">
                <div className="text-data-lg">
                  {data.tank.level_percent.toFixed(0)}
                  <span className="text-body-sm text-text-muted">%</span>
                </div>
                {/* Level bar */}
                <div className="h-2 w-full overflow-hidden rounded-full bg-hover">
                  <div
                    className={cn(
                      'h-full rounded-full transition-all duration-500',
                      data.tank.level_percent > 50
                        ? 'bg-success'
                        : data.tank.level_percent > 20
                          ? 'bg-warning'
                          : 'bg-critical'
                    )}
                    style={{ width: `${Math.min(data.tank.level_percent, 100)}%` }}
                  />
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Fill Rate</span>
                  <span className="font-medium">{data.tank.fill_rate_lpm.toFixed(2)} L/min</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Empty Rate</span>
                  <span className="font-medium">{data.tank.empty_rate_lpm.toFixed(2)} L/min</span>
                </div>
                {data.tank.stagnation_hours > 0 && (
                  <div className="rounded-button border border-warning/30 bg-warning/10 px-3 py-1.5 text-caption text-warning">
                    Stagnation: {data.tank.stagnation_hours.toFixed(0)}h
                  </div>
                )}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* Pump Energy Panel */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-text-secondary" /> Pump Energy
            </CardTitle>
            {!isLoading && data && (
              <Badge variant={statusBadgeVariant(data.pump.status)}>{data.pump.status}</Badge>
            )}
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-10 w-full" />
                <Skeleton className="h-4 w-3/4" />
              </div>
            ) : data ? (
              <div className="space-y-3">
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Current</span>
                  <span className="font-medium">{data.pump.current_a.toFixed(2)} A</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Power</span>
                  <span className="font-medium">{data.pump.power_w.toFixed(0)} W</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">7d Efficiency Trend</span>
                  {data.pump.efficiency_trend_7d < 0 ? (
                    <Badge variant="warning">Degrading</Badge>
                  ) : data.pump.efficiency_trend_7d > 0 ? (
                    <Badge variant="success">Improving</Badge>
                  ) : (
                    <Badge variant="default">Stable</Badge>
                  )}
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Runtime</span>
                  <span className="font-medium">{data.pump.runtime_hours.toFixed(0)} h</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Start Count</span>
                  <span className="font-medium">{data.pump.start_count}</span>
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
