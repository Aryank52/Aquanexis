import { Link } from 'react-router-dom';
import { Filter, AlertTriangle, ArrowRight, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useFilterHealth, useFailureRisk } from '@/hooks/useFilterHealth';
import { ProvenanceBadge, type DataProvenance } from '@components/dashboard/ProvenanceBadge';
import type { MaintenanceBand, PredictionConfidence } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

function fsiColor(v: number) {
  return v < 40 ? 'text-success' : v < 70 ? 'text-warning' : 'text-critical';
}
function fhiColor(v: number) {
  return v > 70 ? 'text-success' : v > 40 ? 'text-warning' : 'text-critical';
}

const bandVariant: Record<MaintenanceBand, 'success' | 'info' | 'warning' | 'critical'> = {
  NORMAL: 'success',
  MONITOR: 'info',
  PLAN_MAINTENANCE: 'warning',
  REPLACE_RECOMMENDED: 'critical',
};

const confVariant: Record<PredictionConfidence, 'success' | 'warning' | 'critical'> = {
  HIGH: 'success',
  MEDIUM: 'warning',
  LOW: 'critical',
};

export function FilterHealthPage() {
  const fh = useFilterHealth(DEVICE_ID);
  const risk = useFailureRisk(DEVICE_ID);

  if (fh.isError) {
    return (
      <QueryError
        message={(fh.error as Error)?.message ?? 'Failed to load filter health'}
        onRetry={fh.refetch}
      />
    );
  }

  const showReplaceCta =
    fh.data && (fh.data.fhi < 40 || fh.data.maintenance_band === 'REPLACE_RECOMMENDED');

  return (
    <div className="animate-fade-in space-y-6">
      <div>
        <h1 className="text-text-primary text-h1 font-semibold">Filter Intelligence</h1>
        <p className="mt-1 text-body-sm text-text-secondary">
          Filter Stress Index, Health Index, and Remaining Useful Life
        </p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* FSI */}
        <Card>
          <CardContent className="p-6">
            {fh.isLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : fh.data ? (
              <div className="text-center">
                <div className="mb-2 flex items-center justify-center gap-2 text-caption text-text-secondary">
                  <span>Filter Stress Index (FSI)</span>
                  <ProvenanceBadge provenance="CALCULATED" size="sm" />
                </div>
                <div className={cn('text-data-xl', fsiColor(fh.data.fsi))}>
                  {fh.data.fsi.toFixed(1)}
                </div>
                <p className="mt-2 text-caption text-text-muted">
                  Lower is better — measures membrane fouling stress
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* FHI */}
        <Card>
          <CardContent className="p-6">
            {fh.isLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : fh.data ? (
              <div className="text-center">
                <div className="mb-2 flex items-center justify-center gap-2 text-caption text-text-secondary">
                  <span>Filter Health Index (FHI)</span>
                  <ProvenanceBadge provenance="CALCULATED" size="sm" />
                </div>
                <div className={cn('text-data-xl', fhiColor(fh.data.fhi))}>
                  {fh.data.fhi.toFixed(1)}
                </div>
                <Badge variant={bandVariant[fh.data.maintenance_band]} className="mt-2">
                  {fh.data.maintenance_band.replace(/_/g, ' ')}
                </Badge>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* RUL */}
        <Card>
          <CardContent className="p-6">
            {fh.isLoading ? (
              <Skeleton className="h-20 w-full" />
            ) : fh.data ? (
              <div className="text-center">
                <div className="mb-2 flex items-center justify-center gap-2 text-caption text-text-secondary">
                  <span>Remaining Useful Life (RUL)</span>
                  <ProvenanceBadge
                    provenance={(fh.data.provenance as DataProvenance) ?? 'MODEL_PREDICTED'}
                    size="sm"
                  />
                </div>
                <div className="text-text-primary text-data-xl">
                  {fh.data.rul_days != null ? `${fh.data.rul_days}` : '—'}
                  <span className="ml-1 text-h3 text-text-muted">days</span>
                </div>
                {fh.data.rul_confidence_lower != null && fh.data.rul_confidence_upper != null && (
                  <div className="mt-1 text-caption text-text-muted">
                    Confidence band: {fh.data.rul_confidence_lower} – {fh.data.rul_confidence_upper}{' '}
                    days
                  </div>
                )}
                <Badge variant={confVariant[fh.data.confidence_level]} className="mt-2">
                  {fh.data.confidence_level} confidence
                </Badge>
                <div className="mt-2 font-mono text-caption text-text-muted">
                  {fh.data.model_name === 'MODEL_MISSING' ? (
                    <span className="inline-flex items-center gap-1 rounded bg-warning/15 px-2 py-0.5 font-semibold text-warning">
                      MODEL_MISSING (Deterministic Fallback v{fh.data.model_version})
                    </span>
                  ) : (
                    `${fh.data.model_name} v${fh.data.model_version}`
                  )}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* Replace Filter CTA */}
      {showReplaceCta && (
        <Card className="border-critical bg-critical/5">
          <CardContent className="flex flex-wrap items-center justify-between gap-4 p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 flex-shrink-0 text-critical" />
              <div>
                <p className="text-body-sm font-medium text-critical">
                  Filter replacement recommended
                </p>
                <p className="text-caption text-text-secondary">
                  Replace filter to restore system performance and water quality.
                </p>
              </div>
            </div>
            <Link to="/maintenance">
              <Button variant="danger">
                <Filter className="mr-1 h-4 w-4" /> Replace Filter{' '}
                <ArrowRight className="ml-1 h-4 w-4" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* AI Explanation */}
      {fh.data?.explanation?.top_contributors &&
        fh.data.explanation.top_contributors.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>AI Explanation — Top Contributing Factors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {fh.data.explanation.top_contributors.map((factor, i) => (
                  <div key={i} className="space-y-1">
                    <div className="flex justify-between text-body-sm">
                      <span className="text-text-primary">{factor.label}</span>
                      <span
                        className={cn(
                          'text-caption',
                          factor.direction === 'increases' ? 'text-critical' : 'text-success'
                        )}
                      >
                        {factor.direction === 'increases' ? '↑' : '↓'} {factor.feature}
                      </span>
                    </div>
                    <div className="h-1.5 w-full overflow-hidden rounded-full bg-hover">
                      <div
                        className={cn(
                          'h-full rounded-full',
                          factor.direction === 'increases' ? 'bg-critical' : 'bg-success'
                        )}
                        style={{ width: `${Math.min(Math.abs(factor.contribution) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

      {/* Failure Risk */}
      {risk.data && (
        <Card>
          <CardHeader>
            <CardTitle>Failure Risk Assessment</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Badge
                  variant={
                    risk.data.risk_level === 'LOW'
                      ? 'success'
                      : risk.data.risk_level === 'MEDIUM'
                        ? 'warning'
                        : 'critical'
                  }
                >
                  {risk.data.risk_level} RISK
                </Badge>
                <span className="text-data font-medium">
                  {(risk.data.risk_score > 1
                    ? risk.data.risk_score
                    : risk.data.risk_score * 100
                  ).toFixed(0)}
                  % risk score
                </span>
              </div>
              {risk.data.evidence.length > 0 && (
                <div className="space-y-2">
                  {risk.data.evidence.map((ev, i) => (
                    <div key={i} className="flex items-start gap-3 rounded bg-surface p-2">
                      <Info className="mt-0.5 h-4 w-4 flex-shrink-0 text-text-muted" />
                      <div className="text-body-sm">
                        <span className="text-text-primary font-medium">{ev.factor}:</span>{' '}
                        <span className="text-text-secondary">{ev.description}</span>
                        <span className="ml-2 text-caption text-text-muted">
                          (value: {ev.value}, threshold: {ev.threshold})
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Counterfactual — rendered from explanation.counterfactual if present */}
      {fh.data?.explanation?.counterfactual?.scenarios &&
        fh.data.explanation.counterfactual.scenarios.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>What-If Scenarios</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {fh.data.explanation.counterfactual.scenarios.map((scenario, i) => (
                  <div
                    key={i}
                    className="border-subtle flex items-center justify-between rounded border bg-surface p-3"
                  >
                    <span className="text-text-primary text-body-sm">{scenario.description}</span>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'text-data font-medium',
                          scenario.rul_change_days > 0 ? 'text-success' : 'text-critical'
                        )}
                      >
                        {scenario.rul_change_days > 0 ? '+' : ''}
                        {scenario.rul_change_days} days
                      </span>
                      <Badge variant={confVariant[scenario.confidence]}>
                        {scenario.confidence}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
    </div>
  );
}
