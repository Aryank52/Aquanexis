import { Droplet, Filter, Gauge, Activity, Clock, Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useDashboard } from '@/hooks/useDashboard';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ProvenanceBadge, type DataProvenance } from '@components/dashboard/ProvenanceBadge';
import type { DeviceStatus } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const statusConfig: Record<DeviceStatus, { label: string; variant: 'success' | 'warning' | 'critical' | 'info' | 'default' }> = {
  online: { label: 'Online', variant: 'success' },
  degraded: { label: 'Degraded', variant: 'warning' },
  offline: { label: 'Offline', variant: 'critical' },
  maintenance: { label: 'Maintenance', variant: 'info' },
  error: { label: 'Error', variant: 'critical' },
};

function scoreColor(score: number): string {
  if (score >= 80) return 'text-success';
  if (score >= 60) return 'text-warning';
  return 'text-critical';
}

function bandVariant(band: string): 'success' | 'warning' | 'critical' | 'info' {
  switch (band) {
    case 'NORMAL': return 'success';
    case 'MONITOR': return 'info';
    case 'PLAN_MAINTENANCE': return 'warning';
    case 'REPLACE_RECOMMENDED': return 'critical';
    default: return 'info';
  }
}

const sensorLabels: Record<string, { label: string; unit: string; icon: typeof Droplet }> = {
  tds: { label: 'TDS', unit: 'ppm', icon: Droplet },
  ph: { label: 'pH', unit: '', icon: Gauge },
  turbidity: { label: 'Turbidity', unit: 'NTU', icon: Filter },
  temperature: { label: 'Temperature', unit: '°C', icon: Activity },
  flow: { label: 'Feed Flow', unit: 'L/min', icon: Activity },
  pressure: { label: 'Pressure', unit: 'kPa', icon: Gauge },
};

export function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboard(DEVICE_ID);
  const { status: wsStatus } = useWebSocket(DEVICE_ID);

  if (isError) {
    return <QueryError message={(error as Error)?.message ?? 'Failed to load dashboard'} onRetry={refetch} />;
  }

  const deviceStatus = data?.device?.status ?? 'offline';
  const cfg = statusConfig[deviceStatus] ?? statusConfig.offline;
  const aquascore = data?.water_quality?.aquascore ?? 0;
  
  // Determine data freshness status
  const dataFreshness = data?.data_freshness_seconds ?? 0;
  const isDataStale = dataFreshness > 30; // Stale if older than 30 seconds
  const isDataVeryStale = dataFreshness > 120; // Very stale if older than 2 minutes

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">
            {isLoading ? <Skeleton className="h-8 w-48" /> : (data?.device?.name ?? 'AquaNexis Dashboard')}
          </h1>
          <div className="flex items-center gap-3 mt-1 flex-wrap">
            {!isLoading && <Badge variant={cfg.variant}>{cfg.label}</Badge>}
            <span className="flex items-center gap-1 text-caption text-text-muted">
              {wsStatus === 'connected' ? (
                <><Wifi className="h-3 w-3 text-success" /> Live</>
              ) : wsStatus === 'reconnecting' ? (
                <><Activity className="h-3 w-3 text-warning animate-spin" /> Reconnecting...</>
              ) : (
                <><WifiOff className="h-3 w-3 text-critical" /> Offline</>
              )}
            </span>
            {!isLoading && data?.data_freshness_seconds != null && (
              <span className={cn(
                'text-caption flex items-center gap-1',
                isDataVeryStale ? 'text-critical' : isDataStale ? 'text-warning' : 'text-text-muted'
              )}>
                <Clock className="h-3 w-3" />
                {isDataVeryStale ? 'Data stale - ' : isDataStale ? 'Data aging - ' : ''}
                Updated {dataFreshness < 60
                  ? `${Math.round(dataFreshness)}s ago`
                  : `${Math.round(dataFreshness / 60)}m ago`}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Offline/Stale Data Banner */}
      {!isLoading && (wsStatus !== 'connected' || isDataStale) && (
        <div className={cn(
          'rounded-card border px-4 py-3 flex items-center gap-3 text-sm',
          wsStatus !== 'connected' ? 'bg-critical/10 border-critical/30 text-critical' : 'bg-warning/10 border-warning/30 text-warning'
        )}>
          {wsStatus !== 'connected' ? (
            <>
              <WifiOff className="h-4 w-4 flex-shrink-0" />
              <span>Connection lost. Showing last known data.</span>
            </>
          ) : (
            <>
              <Activity className="h-4 w-4 flex-shrink-0" />
              <span>Data is {isDataVeryStale ? 'very stale' : 'aging'}. Last update {dataFreshness < 60 ? `${Math.round(dataFreshness)}s` : `${Math.round(dataFreshness / 60)}m`} ago.</span>
            </>
          )}
        </div>
      )}

      {/* Active Alert Banner */}
      {data?.active_alert && (
        <div className={cn(
          'rounded-card border px-4 py-3 flex items-center gap-3',
          data.active_alert.severity === 'CRITICAL' ? 'bg-critical/10 border-critical/30 text-critical' :
          data.active_alert.severity === 'WARNING' ? 'bg-warning/10 border-warning/30 text-warning' :
          'bg-info/10 border-info/30 text-info',
        )}>
          <span className="font-semibold text-body-sm">{data.active_alert.alert_code.replace(/_/g, ' ')}</span>
          <span className="text-body-sm">{data.active_alert.message ?? ''}</span>
        </div>
      )}

      {/* AquaScore + Filter Health Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* AquaScore */}
        <Card>
          <CardContent className="p-6 text-center">
            {isLoading ? (
              <Skeleton className="h-20 w-20 rounded-full mx-auto" />
            ) : (
              <>
                <div className="flex items-center justify-center gap-2 mb-2">
                  <div className={cn('text-data-xl', scoreColor(aquascore))}>{aquascore.toFixed(0)}</div>
                  {data?.water_quality?.provenance && (
                    <ProvenanceBadge provenance={data.water_quality.provenance as DataProvenance} size="sm" />
                  )}
                </div>
                <div className="text-caption text-text-secondary mt-1">AquaScore™</div>
              </>
            )}
          </CardContent>
        </Card>

        {/* Filter Health */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Filter Health</CardTitle>
              {data?.filter_health?.provenance && (
                <ProvenanceBadge provenance={data.filter_health.provenance as DataProvenance} size="sm" />
              )}
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></div>
            ) : data?.filter_health ? (
              <div className="space-y-2">
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">FHI</span>
                  <span className={cn('font-medium', data.filter_health.fhi > 70 ? 'text-success' : data.filter_health.fhi > 40 ? 'text-warning' : 'text-critical')}>
                    {data.filter_health.fhi.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">FSI</span>
                  <span className={cn('font-medium', data.filter_health.fsi < 40 ? 'text-success' : data.filter_health.fsi < 70 ? 'text-warning' : 'text-critical')}>
                    {data.filter_health.fsi.toFixed(1)}
                  </span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">RUL</span>
                  <span className="font-medium">{data.filter_health.rul_days != null ? `${data.filter_health.rul_days} days` : '—'}</span>
                </div>
                <div className="flex justify-between text-caption text-text-muted">
                  <span>Model</span>
                  <span className="font-mono">
                    {data.filter_health.model_name === 'MODEL_MISSING'
                      ? 'MODEL_MISSING (Fallback)'
                      : `${data.filter_health.model_name} v${data.filter_health.model_version}`}
                  </span>
                </div>
                <div className="flex items-center gap-2 flex-wrap pt-1">
                  <Badge variant={bandVariant(data.filter_health.maintenance_band)}>
                    {data.filter_health.maintenance_band.replace(/_/g, ' ')}
                  </Badge>
                  <Badge variant={data.filter_health.confidence_level === 'HIGH' ? 'success' : data.filter_health.confidence_level === 'MEDIUM' ? 'warning' : 'critical'}>
                    {data.filter_health.confidence_level} CONFIDENCE
                  </Badge>
                </div>
              </div>
            ) : (
              <span className="text-body-sm text-text-muted">No filter data</span>
            )}
          </CardContent>
        </Card>

        {/* Purification Quick */}
        <Card>
          <CardHeader>
            <CardTitle>Purification</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2"><Skeleton className="h-4 w-full" /><Skeleton className="h-4 w-3/4" /></div>
            ) : data?.purification ? (
              <div className="space-y-2">
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Rejection</span>
                  <span className="font-medium">{data.purification.rejection_rate != null ? `${(data.purification.rejection_rate * 100).toFixed(1)}%` : '—'}</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Recovery</span>
                  <span className="font-medium">{data.purification.recovery_ratio != null ? `${(data.purification.recovery_ratio * 100).toFixed(1)}%` : '—'}</span>
                </div>
                <div className="flex justify-between text-body-sm">
                  <span className="text-text-secondary">Efficiency</span>
                  <span className="font-medium">{data.purification.efficiency != null ? `${(data.purification.efficiency * 100).toFixed(0)}%` : '—'}</span>
                </div>
              </div>
            ) : (
              <span className="text-body-sm text-text-muted">No purification data</span>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sensor Grid */}
      <div>
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <div className="flex items-center gap-3">
            <h2 className="text-h2 font-semibold text-text-primary">Live Sensor Readings</h2>
            {data?.latest_telemetry?.quality?.overall && (
              <Badge
                variant={
                  data.latest_telemetry.quality.overall === 'GOOD'
                    ? 'success'
                    : data.latest_telemetry.quality.overall === 'SUSPECT'
                    ? 'warning'
                    : 'critical'
                }
              >
                Quality: {data.latest_telemetry.quality.overall}
              </Badge>
            )}
          </div>
          {data?.latest_telemetry?.provenance && (
            <ProvenanceBadge provenance={data.latest_telemetry.provenance as DataProvenance} size="sm" showDescription />
          )}
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {Object.entries(sensorLabels).map(([key, meta]) => {
            const value = data?.latest_telemetry?.readings?.[key as keyof typeof data.latest_telemetry.readings];
            const Icon = meta.icon;
            return (
              <Card key={key}>
                <CardContent className="p-4 text-center">
                  {isLoading ? (
                    <Skeleton className="h-10 w-full" />
                  ) : (
                    <>
                      <Icon className="h-4 w-4 text-text-muted mx-auto mb-1" />
                      <div className="text-data-lg">{value != null ? (typeof value === 'number' ? value.toFixed(key === 'ph' ? 1 : key === 'flow' ? 2 : 0) : String(value)) : '—'}</div>
                      <div className="text-caption text-text-muted">{meta.label}</div>
                      {meta.unit && <div className="text-caption text-text-muted">{meta.unit}</div>}
                    </>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Diagnostics Quick Summary */}
      {data?.diagnostics && (
        <div>
          <h2 className="text-h2 font-semibold text-text-primary mb-4">System Diagnostics</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <Card key="pressure">
              <CardContent className="p-3 text-center">
                <div className="text-body-sm text-text-secondary">Pressure</div>
                <Badge variant={data.diagnostics.pressure !== null && data.diagnostics.pressure > 500 ? 'critical' : data.diagnostics.pressure !== null && data.diagnostics.pressure > 400 ? 'warning' : 'success'}>
                  {data.diagnostics.pressure !== null ? `${data.diagnostics.pressure} kPa` : '—'}
                </Badge>
              </CardContent>
            </Card>
            <Card key="flow">
              <CardContent className="p-3 text-center">
                <div className="text-body-sm text-text-secondary">Flow</div>
                <Badge variant="success">
                  {data.diagnostics.flow !== null ? `${data.diagnostics.flow} L/min` : '—'}
                </Badge>
              </CardContent>
            </Card>
            <Card key="leak">
              <CardContent className="p-3 text-center">
                <div className="text-body-sm text-text-secondary">Leak</div>
                <Badge variant={data.diagnostics.leak === true ? 'critical' : 'success'}>
                  {data.diagnostics.leak ? 'Detected' : 'None'}
                </Badge>
              </CardContent>
            </Card>
            <Card key="tank">
              <CardContent className="p-3 text-center">
                <div className="text-body-sm text-text-secondary">Tank</div>
                <Badge variant={data.diagnostics.tank !== null && data.diagnostics.tank < 20 ? 'warning' : 'success'}>
                  {data.diagnostics.tank !== null ? `${data.diagnostics.tank}%` : '—'}
                </Badge>
              </CardContent>
            </Card>
            <Card key="pump">
              <CardContent className="p-3 text-center">
                <div className="text-body-sm text-text-secondary">Pump</div>
                <Badge variant={data.diagnostics.pump !== null && data.diagnostics.pump > 3 ? 'warning' : 'success'}>
                  {data.diagnostics.pump !== null ? `${data.diagnostics.pump} A` : '—'}
                </Badge>
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}