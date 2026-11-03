import { Droplet, Gauge, Activity, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { usePurification } from '@/hooks/usePurification';
import { format } from 'date-fns';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

function metricColor(
  value: number | null,
  thresholds: { good: number; warn: number; invert?: boolean }
): string {
  if (value == null) return 'text-text-muted';
  if (thresholds.invert) {
    // lower is better (e.g. permeate TDS)
    if (value <= thresholds.good) return 'text-success';
    if (value <= thresholds.warn) return 'text-warning';
    return 'text-critical';
  }
  // higher is better
  if (value >= thresholds.good) return 'text-success';
  if (value >= thresholds.warn) return 'text-warning';
  return 'text-critical';
}

export function PurificationPerformancePage() {
  const { data, isLoading, isError, error, refetch } = usePurification(DEVICE_ID);

  if (isError) {
    return (
      <QueryError
        message={(error as Error)?.message ?? 'Failed to load purification data'}
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Purification Performance</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Membrane rejection, recovery, and overall purification efficiency
          </p>
        </div>
        {!isLoading && data?.timestamp && (
          <span className="text-caption text-text-muted">
            Last updated: {format(new Date(data.timestamp), 'dd MMM yyyy HH:mm')}
          </span>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Rejection Rate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Droplet className="h-4 w-4 text-text-secondary" /> Rejection Rate
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <div className="text-center">
                <div
                  className={cn(
                    'text-data-xl',
                    metricColor(data?.rejection_rate ?? null, { good: 0.95, warn: 0.9 })
                  )}
                >
                  {data?.rejection_rate != null
                    ? `${(data.rejection_rate * 100).toFixed(1)}%`
                    : 'N/A'}
                </div>
                <p className="mt-2 text-caption text-text-muted">
                  Percentage of contaminants removed by the membrane
                </p>
                <div className="mt-2 flex justify-center gap-2">
                  <Badge variant="success">≥95% Good</Badge>
                  <Badge variant="warning">90–95% Fair</Badge>
                  <Badge variant="critical">&lt;90% Poor</Badge>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recovery Ratio */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-text-secondary" /> Recovery Ratio
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <div className="text-center">
                <div
                  className={cn(
                    'text-data-xl',
                    metricColor(data?.recovery_ratio ?? null, { good: 0.75, warn: 0.6 })
                  )}
                >
                  {data?.recovery_ratio != null
                    ? `${(data.recovery_ratio * 100).toFixed(1)}%`
                    : 'N/A'}
                </div>
                <p className="mt-2 text-caption text-text-muted">
                  Ratio of purified water produced to total feed water
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Permeate Quality */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Gauge className="h-4 w-4 text-text-secondary" /> Permeate Quality
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <div className="text-center">
                <div
                  className={cn(
                    'text-data-xl',
                    metricColor(data?.permeate_quality ?? null, {
                      good: 50,
                      warn: 100,
                      invert: true,
                    })
                  )}
                >
                  {data?.permeate_quality != null ? `${data.permeate_quality.toFixed(0)}` : 'N/A'}
                  {data?.permeate_quality != null && (
                    <span className="ml-1 text-h3 text-text-muted">TDS</span>
                  )}
                </div>
                <p className="mt-2 text-caption text-text-muted">
                  Total Dissolved Solids in purified output water
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Overall Efficiency */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-text-secondary" /> Overall Efficiency
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            {isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <div className="text-center">
                <div
                  className={cn(
                    'text-data-xl',
                    metricColor(data?.efficiency ?? null, { good: 0.85, warn: 0.7 })
                  )}
                >
                  {data?.efficiency != null ? `${(data.efficiency * 100).toFixed(0)}%` : 'N/A'}
                </div>
                <p className="mt-2 text-caption text-text-muted">
                  Combined purification system efficiency score
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Feed Quality */}
      {!isLoading && data?.feed_quality != null && (
        <Card>
          <CardHeader>
            <CardTitle>Feed Water Quality</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <div className="text-data-lg">
                {data.feed_quality.toFixed(0)}{' '}
                <span className="text-body-sm text-text-muted">TDS</span>
              </div>
              <p className="text-body-sm text-text-secondary">
                Total Dissolved Solids in incoming feed water
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chart placeholder */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-3 text-text-muted">
            <Info className="h-5 w-5 flex-shrink-0" />
            <p className="text-body-sm">
              Time-series chart visualization pending — uPlot integration scheduled for Phase G.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
