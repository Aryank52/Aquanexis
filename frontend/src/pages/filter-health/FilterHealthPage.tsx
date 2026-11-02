import { Link } from 'react-router-dom';
import { Filter, AlertTriangle, ArrowRight, Info } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useFilterHealth, useFailureRisk } from '@/hooks/useFilterHealth';
import type { MaintenanceBand, PredictionConfidence } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

function fsiColor(v: number) { return v < 40 ? 'text-success' : v < 70 ? 'text-warning' : 'text-critical'; }
function fhiColor(v: number) { return v > 70 ? 'text-success' : v > 40 ? 'text-warning' : 'text-critical'; }

const bandVariant: Record<MaintenanceBand, 'success' | 'info' | 'warning' | 'critical'> = {
  NORMAL: 'success', MONITOR: 'info', PLAN_MAINTENANCE: 'warning', REPLACE_RECOMMENDED: 'critical',
};

const confVariant: Record<PredictionConfidence, 'success' | 'warning' | 'critical'> = {
  HIGH: 'success', MEDIUM: 'warning', LOW: 'critical',
};

export function FilterHealthPage() {
  const fh = useFilterHealth(DEVICE_ID);
  const risk = useFailureRisk(DEVICE_ID);

  if (fh.isError) {
    return <QueryError message={(fh.error as Error)?.message ?? 'Failed to load filter health'} onRetry={fh.refetch} />;
  }

  const showReplaceCta = fh.data && (fh.data.fhi < 40 || fh.data.maintenance_band === 'REPLACE_RECOMMENDED');

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-h1 font-semibold text-text-primary">Filter Intelligence</h1>
        <p className="text-body-sm text-text-secondary mt-1">Filter Stress Index, Health Index, and Remaining Useful Life</p>
      </div>

      {/* Top Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* FSI */}
        <Card>
          <CardContent className="p-6">
            {fh.isLoading ? <Skeleton className="h-20 w-full" /> : fh.data ? (
              <div className="text-center">
                <div className="text-caption text-text-secondary mb-2">Filter Stress Index (FSI)</div>
                <div className={cn('text-data-xl', fsiColor(fh.data.fsi))}>{fh.data.fsi.toFixed(1)}</div>
                <p className="text-caption text-text-muted mt-2">Lower is better — measures membrane fouling stress</p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        {/* FHI */}
        <Card>
          <CardContent className="p-6">
            {fh.isLoading ? <Skeleton className="h-20 w-full" /> : fh.data ? (
              <div className="text-center">
                <div className="text-caption text-text-secondary mb-2">Filter Health Index (FHI)</div>
                <div className={cn('text-data-xl', fhiColor(fh.data.fhi))}>{fh.data.fhi.toFixed(1)}</div>
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
            {fh.isLoading ? <Skeleton className="h-20 w-full" /> : fh.data ? (
              <div className="text-center">
                <div className="text-caption text-text-secondary mb-2">Remaining Useful Life (RUL)</div>
                <div className="text-data-xl text-text-primary">
                  {fh.data.rul_days != null ? `${fh.data.rul_days}` : '—'}
                  <span className="text-h3 text-text-muted ml-1">days</span>
                </div>
                {fh.data.rul_confidence_lower != null && fh.data.rul_confidence_upper != null && (
                  <div className="text-caption text-text-muted mt-1">
                    Confidence band: {fh.data.rul_confidence_lower} – {fh.data.rul_confidence_upper} days
                  </div>
                )}
                <Badge variant={confVariant[fh.data.confidence_level]} className="mt-2">
                  {fh.data.confidence_level} confidence
                </Badge>
                <div className="text-caption text-text-muted mt-2">
                  {fh.data.model_name} v{fh.data.model_version}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>

      {/* Replace Filter CTA */}
      {showReplaceCta && (
        <Card className="border-critical bg-critical/5">
          <CardContent className="p-4 flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-critical flex-shrink-0" />
              <div>
                <p className="text-body-sm font-medium text-critical">Filter replacement recommended</p>
                <p className="text-caption text-text-secondary">Replace filter to restore system performance and water quality.</p>
              </div>
            </div>
            <Link to="/maintenance">
              <Button variant="danger">
                <Filter className="h-4 w-4 mr-1" /> Replace Filter <ArrowRight className="h-4 w-4 ml-1" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* AI Explanation */}
      {fh.data?.explanation?.top_contributors && fh.data.explanation.top_contributors.length > 0 && (
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
                    <span className={cn('text-caption', factor.direction === 'increases' ? 'text-critical' : 'text-success')}>
                      {factor.direction === 'increases' ? '↑' : '↓'} {factor.feature}
                    </span>
                  </div>
                  <div className="w-full h-1.5 bg-hover rounded-full overflow-hidden">
                    <div
                      className={cn('h-full rounded-full', factor.direction === 'increases' ? 'bg-critical' : 'bg-success')}
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
                <Badge variant={risk.data.risk_level === 'LOW' ? 'success' : risk.data.risk_level === 'MEDIUM' ? 'warning' : 'critical'}>
                  {risk.data.risk_level} RISK
                </Badge>
                <span className="text-data font-medium">{(risk.data.risk_score * 100).toFixed(0)}% risk score</span>
              </div>
              {risk.data.evidence.length > 0 && (
                <div className="space-y-2">
                  {risk.data.evidence.map((ev, i) => (
                    <div key={i} className="flex items-start gap-3 p-2 rounded bg-surface">
                      <Info className="h-4 w-4 text-text-muted mt-0.5 flex-shrink-0" />
                      <div className="text-body-sm">
                        <span className="font-medium text-text-primary">{ev.factor}:</span>{' '}
                        <span className="text-text-secondary">{ev.description}</span>
                        <span className="text-caption text-text-muted ml-2">(value: {ev.value}, threshold: {ev.threshold})</span>
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
      {fh.data?.explanation?.counterfactual?.scenarios && fh.data.explanation.counterfactual.scenarios.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>What-If Scenarios</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {fh.data.explanation.counterfactual.scenarios.map((scenario, i) => (
                <div key={i} className="flex items-center justify-between p-3 rounded bg-surface border border-subtle">
                  <span className="text-body-sm text-text-primary">{scenario.description}</span>
                  <div className="flex items-center gap-2">
                    <span className={cn('text-data font-medium', scenario.rul_change_days > 0 ? 'text-success' : 'text-critical')}>
                      {scenario.rul_change_days > 0 ? '+' : ''}{scenario.rul_change_days} days
                    </span>
                    <Badge variant={confVariant[scenario.confidence]}>{scenario.confidence}</Badge>
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
