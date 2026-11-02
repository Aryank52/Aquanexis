import { RefreshCw, TrendingUp, TrendingDown, Minus, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useWaterQuality } from '@/hooks/useWaterQuality';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

function scoreVariant(score: number): 'success' | 'warning' | 'critical' {
  if (score >= 80) return 'success';
  if (score >= 60) return 'warning';
  return 'critical';
}

function scoreColor(score: number): string {
  if (score >= 80) return 'text-success';
  if (score >= 60) return 'text-warning';
  return 'text-critical';
}

function scoreBarColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 60) return 'bg-yellow-400';
  return 'bg-red-500';
}

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1).replace(/_/g, ' ');
}

export function WaterQualityPage() {
  const { data, isLoading, isError, error, refetch } = useWaterQuality(DEVICE_ID);

  if (isLoading) {
    return (
      <div className="space-y-6 animate-fade-in">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <QueryError
        message={error instanceof Error ? error.message : 'Failed to load water quality data'}
        onRetry={() => refetch()}
      />
    );
  }

  const trends = data.trends ?? {};
  const anomalyFlags = data.anomaly_flags ?? {};
  const hasAnomalyFlags = Object.keys(anomalyFlags).length > 0;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 text-text-primary">Water Quality Analysis</h1>
          <p className="text-body-sm text-text-secondary mt-1">
            Last updated: {format(new Date(data.timestamp), 'dd MMM yyyy HH:mm')}
          </p>
        </div>
        <Button variant="ghost" onClick={() => refetch()} className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* AquaScore Banner */}
      <Card className="bg-surface">
        <CardContent className="flex flex-col items-center justify-center py-10 gap-2">
          <span className={cn('text-data-lg font-bold text-7xl', scoreColor(data.aquascore))}>
            {data.aquascore.toFixed(0)}
          </span>
          <span className="text-h3 text-text-secondary tracking-wider">AquaScore™</span>
          {data.anomaly_score != null && (
            <Badge variant="warning" className="mt-2">
              {(data.anomaly_score * 100).toFixed(0)}% anomaly
            </Badge>
          )}
        </CardContent>
      </Card>

      {/* Parameter Scores */}
      <section>
        <h2 className="text-h2 text-text-primary mb-4">Parameter Scores</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {data.parameter_scores.map((item) => (
            <Card key={item.parameter} className="bg-surface">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span className="text-body-sm text-text-primary">{capitalize(item.parameter)}</span>
                  <Badge variant={scoreVariant(item.score)}>{item.score.toFixed(0)}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <p className="text-data text-text-secondary">
                  {item.value} <span className="text-caption text-text-muted">{item.unit}</span>
                </p>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1">
                  <div
                    style={{ width: `${Math.min(item.score, 100)}%` }}
                    className={cn('h-1 rounded-full', scoreBarColor(item.score))}
                  />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>

      {/* Trends */}
      {Object.keys(trends).length > 0 && (
        <section>
          <h2 className="text-h2 text-text-primary mb-4">Trends</h2>
          <Card className="bg-surface">
            <CardContent className="divide-y divide-gray-100 dark:divide-gray-800">
              {Object.entries(trends).map(([param, trend]) => {
                const direction = trend.direction;
                return (
                  <div key={param} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3">
                      {direction === 'improving' && (
                        <TrendingUp className="h-4 w-4 text-success" />
                      )}
                      {direction === 'stable' && (
                        <Minus className="h-4 w-4 text-text-secondary" />
                      )}
                      {direction === 'degrading' && (
                        <TrendingDown className="h-4 w-4 text-critical" />
                      )}
                      <span className="text-body-sm text-text-primary">{capitalize(param)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'text-caption font-medium',
                          direction === 'improving'
                            ? 'text-success'
                            : direction === 'degrading'
                            ? 'text-critical'
                            : 'text-text-secondary',
                        )}
                      >
                        {capitalize(direction)}
                      </span>
                      <span className="text-caption text-text-muted">
                        ({trend.magnitude >= 0 ? '+' : ''}
                        {trend.magnitude.toFixed(2)})
                      </span>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>
        </section>
      )}

      {/* Anomaly Flags */}
      {hasAnomalyFlags && (
        <section>
          <h2 className="text-h2 text-text-primary mb-4 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-warning" />
            Anomaly Flags
          </h2>
          <Card className="bg-surface border border-yellow-400/30">
            <CardContent className="divide-y divide-gray-100 dark:divide-gray-800">
              {Object.entries(anomalyFlags).map(([key, value]) => (
                <div key={key} className="flex items-start gap-3 py-3">
                  <AlertTriangle className="h-4 w-4 text-warning mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-body-sm font-medium text-text-primary">{capitalize(key)}</p>
                    <p className="text-caption text-text-muted">
                      {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      )}
    </div>
  );
}
