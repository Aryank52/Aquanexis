import { useState } from 'react';
import { Filter, Wrench, CheckCircle, XCircle, AlertTriangle } from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useMaintenanceHistory, useFilterReplacement } from '@/hooks/useMaintenance';
import { useFilterHealth } from '@/hooks/useFilterHealth';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const eventTypeLabels: Record<string, string> = {
  FILTER_REPLACEMENT: 'Filter Replacement',
  CALIBRATION: 'Calibration',
  VERIFICATION: 'Verification',
};

function metricsToString(m: Record<string, number> | null): string {
  if (!m || Object.keys(m).length === 0) return '—';
  return Object.entries(m).map(([k, v]) => `${k}: ${typeof v === 'number' ? v.toFixed(2) : v}`).join(', ');
}

export function MaintenancePage() {
  const history = useMaintenanceHistory(DEVICE_ID);
  const fh = useFilterHealth(DEVICE_ID);
  const replacement = useFilterReplacement();
  const [confirmReplace, setConfirmReplace] = useState(false);
  const [replaceNotes, setReplaceNotes] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  if (history.isError) {
    return <QueryError message={(history.error as Error)?.message ?? 'Failed to load maintenance history'} onRetry={history.refetch} />;
  }

  const isCritical = fh.data && (fh.data.fhi < 40 || fh.data.maintenance_band === 'REPLACE_RECOMMENDED');

  const handleReplace = () => {
    replacement.mutate(
      { device_id: DEVICE_ID, performed_by: 'operator', notes: replaceNotes || undefined },
      {
        onSuccess: () => { setConfirmReplace(false); setReplaceNotes(''); setShowSuccess(true); setTimeout(() => setShowSuccess(false), 5000); },
      },
    );
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-h1 font-semibold text-text-primary">Maintenance</h1>
        <p className="text-body-sm text-text-secondary mt-1">Filter replacement, calibration, and maintenance history</p>
      </div>

      {/* Filter Replacement Action */}
      <Card className={cn(isCritical ? 'border-critical bg-critical/5' : 'border-info bg-info/5')}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" /> Filter Replacement
          </CardTitle>
        </CardHeader>
        <CardContent>
          {fh.isLoading ? <Skeleton className="h-16 w-full" /> : (
            <div className="space-y-4">
              <div className="flex items-center gap-4 flex-wrap">
                {fh.data && (
                  <>
                    <span className="text-body-sm">
                      FHI: <strong className={cn(fh.data.fhi > 70 ? 'text-success' : fh.data.fhi > 40 ? 'text-warning' : 'text-critical')}>
                        {fh.data.fhi.toFixed(1)}
                      </strong>
                    </span>
                    <span className="text-body-sm">
                      Band: <Badge variant={isCritical ? 'critical' : 'success'}>
                        {fh.data.maintenance_band.replace(/_/g, ' ')}
                      </Badge>
                    </span>
                    <span className="text-body-sm">
                      RUL: <strong>{fh.data.rul_days ?? '—'} days</strong>
                    </span>
                  </>
                )}
              </div>

              {showSuccess && (
                <div className="bg-success/10 border border-success/30 rounded-button px-3 py-2 text-success text-body-sm flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" /> Filter replaced successfully. History updated.
                </div>
              )}

              {replacement.isError && (
                <div className="bg-critical/10 border border-critical/30 rounded-button px-3 py-2 text-critical text-body-sm">
                  Error: {(replacement.error as Error)?.message ?? 'Failed to record replacement'}
                </div>
              )}

              {!confirmReplace ? (
                <Button
                  variant={isCritical ? 'danger' : 'primary'}
                  onClick={() => setConfirmReplace(true)}
                >
                  <Wrench className="h-4 w-4 mr-1" /> Replace Filter
                </Button>
              ) : (
                <div className="space-y-3 p-3 bg-surface rounded-card border border-subtle">
                  <p className="text-body-sm text-text-primary font-medium">Confirm Filter Replacement</p>
                  <textarea
                    className="input w-full text-body-sm"
                    rows={2}
                    placeholder="Optional notes (e.g., replacement part number, reason)..."
                    value={replaceNotes}
                    onChange={e => setReplaceNotes(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button variant="danger" onClick={handleReplace} disabled={replacement.isPending}>
                      {replacement.isPending ? 'Recording…' : 'Confirm Replacement'}
                    </Button>
                    <Button variant="ghost" onClick={() => setConfirmReplace(false)} disabled={replacement.isPending}>
                      Cancel
                    </Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Maintenance History */}
      <Card>
        <CardHeader>
          <CardTitle>Maintenance History</CardTitle>
        </CardHeader>
        <CardContent>
          {history.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-12 w-full rounded" />)}
            </div>
          ) : !history.data || history.data.length === 0 ? (
            <EmptyState title="No maintenance records" description="No maintenance events have been recorded for this device" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-b border-subtle text-text-secondary text-left">
                    <th className="py-2 px-3 font-medium">Date</th>
                    <th className="py-2 px-3 font-medium">Type</th>
                    <th className="py-2 px-3 font-medium">Performed By</th>
                    <th className="py-2 px-3 font-medium">Pre-metrics</th>
                    <th className="py-2 px-3 font-medium">Post-metrics</th>
                    <th className="py-2 px-3 font-medium">Notes</th>
                    <th className="py-2 px-3 font-medium">Verified</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-subtle">
                  {history.data.map(event => (
                    <tr key={event.id} className="hover:bg-hover transition-colors">
                      <td className="py-2 px-3 whitespace-nowrap">{format(new Date(event.performed_at), 'dd MMM yyyy HH:mm')}</td>
                      <td className="py-2 px-3">
                        <Badge variant="default">{eventTypeLabels[event.event_type] ?? event.event_type}</Badge>
                      </td>
                      <td className="py-2 px-3 text-text-secondary">{event.performed_by ?? '—'}</td>
                      <td className="py-2 px-3 text-text-muted text-caption max-w-[160px] truncate" title={metricsToString(event.pre_metrics)}>
                        {metricsToString(event.pre_metrics)}
                      </td>
                      <td className="py-2 px-3 text-text-muted text-caption max-w-[160px] truncate" title={metricsToString(event.post_metrics)}>
                        {metricsToString(event.post_metrics)}
                      </td>
                      <td className="py-2 px-3 text-text-secondary max-w-[200px] truncate">{event.notes ?? '—'}</td>
                      <td className="py-2 px-3">
                        {event.verified ? (
                          <CheckCircle className="h-4 w-4 text-success" />
                        ) : (
                          <XCircle className="h-4 w-4 text-text-muted" />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
