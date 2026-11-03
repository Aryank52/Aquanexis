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

const severityConfig: Record<AlertSeverity, { icon: typeof AlertTriangle; color: string; bg: string; variant: 'critical' | 'warning' | 'info' }> = {
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
    return <QueryError message={(error as Error)?.message ?? 'Failed to load alerts'} onRetry={refetch} />;
  }

  const allAlerts = data?.items ?? [];
  const activeAlerts = allAlerts.filter(
    a => a.status === 'OPEN' || a.status === 'DETECTED' || a.status === 'ACKNOWLEDGED' || a.status === 'SNOOZED'
  );

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Alerts</h1>
          <p className="text-body-sm text-text-secondary mt-1">Monitor, acknowledge, and resolve system alerts</p>
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
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full rounded" />)}
            </div>
          ) : activeAlerts.length === 0 ? (
            <EmptyState title="No active alerts" description="All systems operating normally" />
          ) : (
            <div className="divide-y divide-subtle">
              {activeAlerts.map(alert => {
                const sev = severityConfig[alert.severity];
                const SevIcon = sev.icon;
                return (
                  <div key={alert.id} className={cn('flex items-center gap-4 py-3 px-2 rounded', sev.bg)}>
                    <SevIcon className={cn('h-5 w-5 flex-shrink-0', sev.color)} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="font-medium text-body-sm text-text-primary">{snakeToTitle(alert.alert_code)}</span>
                        <Badge variant={sev.variant}>{alert.severity}</Badge>
                        <Badge variant={stateVariant[alert.status]}>{alert.status}</Badge>
                      </div>
                      <span className="text-caption text-text-muted flex items-center gap-1 mt-1">
                        <Clock className="h-3 w-3" />
                        {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                      </span>
                    </div>
                    <div className="flex gap-2 flex-shrink-0">
                      {(alert.status === 'OPEN' || alert.status === 'DETECTED') && (
                        <Button
                          variant="secondary"
                          onClick={() => acknowledge.mutate({ alertId: alert.id, data: { acknowledged_by: 'operator' } })}
                          disabled={acknowledge.isPending}
                        >
                          <CheckCircle className="h-4 w-4 mr-1" />
                          Acknowledge
                        </Button>
                      )}
                      <Button variant="ghost" onClick={() => { setSelectedAlert(alert); setDrawerOpen(true); }}>
                        <Eye className="h-4 w-4 mr-1" />
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
              {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-12 w-full rounded" />)}
            </div>
          ) : allAlerts.length === 0 ? (
            <EmptyState title="No alerts" description="No alerts match the current filters" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-b border-subtle text-text-secondary text-left">
                    <th className="py-2 px-3 font-medium">Severity</th>
                    <th className="py-2 px-3 font-medium">Type</th>
                    <th className="py-2 px-3 font-medium">Message</th>
                    <th className="py-2 px-3 font-medium">Created</th>
                    <th className="py-2 px-3 font-medium">State</th>
                    <th className="py-2 px-3 font-medium sr-only">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-subtle">
                  {allAlerts.map(alert => {
                    const sev = severityConfig[alert.severity];
                    const SevIcon = sev.icon;
                    return (
                      <tr key={alert.id} className="hover:bg-hover transition-colors">
                        <td className="py-2 px-3"><SevIcon className={cn('h-4 w-4', sev.color)} /></td>
                        <td className="py-2 px-3 font-medium text-text-primary">{snakeToTitle(alert.alert_code)}</td>
                        <td className="py-2 px-3 text-text-secondary max-w-xs truncate">{alert.message ?? '—'}</td>
                        <td className="py-2 px-3 text-text-muted whitespace-nowrap">{formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}</td>
                        <td className="py-2 px-3"><Badge variant={stateVariant[alert.status]}>{alert.status}</Badge></td>
                        <td className="py-2 px-3">
                          <Button variant="ghost" onClick={() => { setSelectedAlert(alert); setDrawerOpen(true); }}>
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