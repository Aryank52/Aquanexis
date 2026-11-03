import { useState } from 'react';
import { AlertTriangle, XCircle, Info, CheckCircle, Clock, Eye } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { AlertEvidenceDrawer } from '@/components/alerts/AlertEvidenceDrawer';
import { cn } from '@utils/cn';
import { useAlerts, useAcknowledgeAlert } from '@/hooks/useAlerts';
import type { AlertResponse, AlertSeverity, AlertState } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const severityConfig: Record<
  AlertSeverity,
  {
    icon: typeof AlertTriangle;
    color: string;
    bg: string;
    variant: 'critical' | 'warning' | 'info';
  }
> = {
  CRITICAL: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', variant: 'critical' },
  WARNING: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', variant: 'warning' },
  INFO: { icon: Info, color: 'text-info', bg: 'bg-info/10', variant: 'info' },
};

const stateVariant: Record<AlertState, 'critical' | 'warning' | 'info' | 'success'> = {
  DETECTED: 'critical',
  OPEN: 'critical',
  ACKNOWLEDGED: 'warning',
  SNOOZED: 'info',
  RESOLVED: 'success',
  AUTO_CLEARED: 'success',
};

function snakeToTitle(s: string): string {
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function AlertsPage() {
  const [filterState, setFilterState] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [selectedAlert, setSelectedAlert] = useState<AlertResponse | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const { data, isLoading, isError, error, refetch } = useAlerts(DEVICE_ID, {
    state: filterState === 'all' ? undefined : filterState,
    severity: filterSeverity === 'all' ? undefined : filterSeverity,
  });

  const acknowledge = useAcknowledgeAlert();

  if (isError) {
    return (
      <QueryError
        message={(error as Error)?.message ?? 'Failed to load alerts'}
        onRetry={refetch}
      />
    );
  }

  const allAlerts = data?.items ?? [];
  const activeAlerts = allAlerts.filter(
    a =>
      a.status === 'OPEN' ||
      a.status === 'DETECTED' ||
      a.status === 'ACKNOWLEDGED' ||
      a.status === 'SNOOZED'
  );

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Alerts</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Monitor, acknowledge, and resolve system alerts
          </p>
        </div>
        <div className="flex gap-3">
          <select
            className="input text-body-sm"
            value={filterState}
            onChange={e => setFilterState(e.target.value)}
            aria-label="Filter by state"
          >
            <option value="all">All States</option>
            <option value="OPEN">Open</option>
            <option value="DETECTED">Detected</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="SNOOZED">Snoozed</option>
            <option value="RESOLVED">Resolved</option>
            <option value="AUTO_CLEARED">Auto Cleared</option>
          </select>
          <select
            className="input text-body-sm"
            value={filterSeverity}
            onChange={e => setFilterSeverity(e.target.value)}
            aria-label="Filter by severity"
          >
            <option value="all">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="WARNING">Warning</option>
            <option value="INFO">Info</option>
          </select>
        </div>
      </div>

      {/* Active Alerts */}
      <Card>
        <CardHeader>
          <CardTitle>Active Alerts ({isLoading ? '…' : activeAlerts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded" />
              ))}
            </div>
          ) : activeAlerts.length === 0 ? (
            <EmptyState title="No active alerts" description="All systems operating normally" />
          ) : (
            <div className="divide-subtle divide-y">
              {activeAlerts.map(alert => {
                const sev = severityConfig[alert.severity];
                const SevIcon = sev.icon;
                return (
                  <div
                    key={alert.id}
                    className={cn('flex items-center gap-4 rounded px-2 py-3', sev.bg)}
                  >
                    <SevIcon className={cn('h-5 w-5 flex-shrink-0', sev.color)} />
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-text-primary text-body-sm font-medium">
                          {snakeToTitle(alert.alert_code)}
                        </span>
                        <Badge variant={sev.variant}>{alert.severity}</Badge>
                        <Badge variant={stateVariant[alert.status]}>{alert.status}</Badge>
                      </div>
                      <span className="mt-1 flex items-center gap-1 text-caption text-text-muted">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex flex-shrink-0 gap-2">
                      {(alert.status === 'OPEN' || alert.status === 'DETECTED') && (
                        <Button
                          variant="secondary"
                          onClick={() =>
                            acknowledge.mutate({
                              alertId: alert.id,
                              data: { acknowledged_by: 'operator' },
                            })
                          }
                          disabled={acknowledge.isPending}
                        >
                          <CheckCircle className="mr-1 h-4 w-4" />
                          Acknowledge
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        onClick={() => {
                          setSelectedAlert(alert);
                          setDrawerOpen(true);
                        }}
                      >
                        <Eye className="mr-1 h-4 w-4" />
                        Details
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* All Alerts History */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History ({isLoading ? '…' : allAlerts.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full rounded" />
              ))}
            </div>
          ) : allAlerts.length === 0 ? (
            <EmptyState title="No alerts" description="No alerts match the current filters" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-subtle border-b text-left text-text-secondary">
                    <th className="px-3 py-2 font-medium">Severity</th>
                    <th className="px-3 py-2 font-medium">Type</th>
                    <th className="px-3 py-2 font-medium">Message</th>
                    <th className="px-3 py-2 font-medium">Created</th>
                    <th className="px-3 py-2 font-medium">State</th>
                    <th className="sr-only px-3 py-2 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-subtle divide-y">
                  {allAlerts.map(alert => {
                    const sev = severityConfig[alert.severity];
                    const SevIcon = sev.icon;
                    return (
                      <tr key={alert.id} className="transition-colors hover:bg-hover">
                        <td className="px-3 py-2">
                          <SevIcon className={cn('h-4 w-4', sev.color)} />
                        </td>
                        <td className="text-text-primary px-3 py-2 font-medium">
                          {snakeToTitle(alert.alert_code)}
                        </td>
                        <td className="max-w-xs truncate px-3 py-2 text-text-secondary">
                          {alert.message ?? '—'}
                        </td>
                        <td className="whitespace-nowrap px-3 py-2 text-text-muted">
                          {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                        </td>
                        <td className="px-3 py-2">
                          <Badge variant={stateVariant[alert.status]}>{alert.status}</Badge>
                        </td>
                        <td className="px-3 py-2">
                          <Button
                            variant="ghost"
                            onClick={() => {
                              setSelectedAlert(alert);
                              setDrawerOpen(true);
                            }}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Evidence Drawer */}
      <AlertEvidenceDrawer
        alert={selectedAlert}
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      />
    </div>
  );
}
