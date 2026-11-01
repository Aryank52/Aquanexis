import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { AlertTriangle, XCircle, Info, CheckCircle, Clock, CheckCircle2, X } from 'lucide-react';

const mockAlerts = [
  { id: '1', type: 'leak_detected', severity: 'CRITICAL' as const, message: 'Leak confirmed via sensor + flow delta', triggerValue: 1, thresholdValue: 0.8, createdAt: new Date(Date.now() - 2 * 60 * 1000).toISOString(), acknowledged: false, state: 'ACTIVE' as const },
  { id: '2', type: 'filter_health_critical', severity: 'WARNING' as const, message: 'FHI 38, RUL 5 days', triggerValue: 38, thresholdValue: 40, createdAt: new Date(Date.now() - 60 * 60 * 1000).toISOString(), acknowledged: false, state: 'ACTIVE' as const },
  { id: '3', type: 'calibration_due', severity: 'INFO' as const, message: 'pH sensor calibration overdue by 3 days', triggerValue: 0, thresholdValue: 0, createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(), acknowledged: true, state: 'ACKNOWLEDGED' as const },
  { id: '4', type: 'water_quality_degraded', severity: 'WARNING' as const, message: 'AquaScore dropped to 68', triggerValue: 68, thresholdValue: 70, createdAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(), acknowledged: true, state: 'RESOLVED' as const },
  { id: '5', type: 'pressure_anomaly', severity: 'WARNING' as const, message: 'Pressure exceeded 580 kPa', triggerValue: 585, thresholdValue: 580, createdAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(), acknowledged: true, state: 'RESOLVED' as const },
];

const severityConfig = {
  CRITICAL: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', border: 'border-critical' },
  WARNING: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning' },
  INFO: { icon: Info, color: 'text-info', bg: 'bg-info/10', border: 'border-info' },
};

const stateConfig = {
  ACTIVE: { icon: Clock, label: 'Active', color: 'text-critical', bg: 'bg-critical/10' },
  ACKNOWLEDGED: { icon: CheckCircle2, label: 'Acknowledged', color: 'text-warning', bg: 'bg-warning/10' },
  RESOLVED: { icon: CheckCircle, label: 'Resolved', color: 'text-success', bg: 'bg-success/10' },
};

export function AlertsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Alerts</h1>
          <p className="text-body-sm text-text-secondary mt-1">Monitor and manage system alerts</p>
        </div>
        <div className="flex items-center gap-3">
          <select className="input w-auto px-3 py-1.5 text-body-sm">
            <option value="all">All States</option>
            <option value="ACTIVE">Active</option>
            <option value="ACKNOWLEDGED">Acknowledged</option>
            <option value="RESOLVED">Resolved</option>
          </select>
          <select className="input w-auto px-3 py-1.5 text-body-sm">
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
          <div className="flex items-center justify-between">
            <CardTitle>Active Alerts ({mockAlerts.filter(a => a.state === 'ACTIVE').length})</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          {mockAlerts.filter(a => a.state === 'ACTIVE').map((alert) => (
            <AlertRow key={alert.id} alert={alert} />
          ))}
        </CardContent>
      </Card>

      {/* Alert History */}
      <Card>
        <CardHeader>
          <CardTitle>Alert History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Type</th>
                  <th>Severity</th>
                  <th>State</th>
                  <th>Message</th>
                  <th className="w-24">Actions</th>
                </tr>
              </thead>
              <tbody>
                {mockAlerts.map((alert) => (
                  <tr key={alert.id}>
                    <td className="text-body-sm text-text-primary">{new Date(alert.createdAt).toLocaleString()}</td>
                    <td>
                      <span className="text-caption font-medium text-text-secondary">{alert.type.replace('_', ' ')}</span>
                    </td>
                    <td>
                      <Badge variant={alert.severity.toLowerCase() as any}>{alert.severity}</Badge>
                    </td>
                    <td>
                      <Badge variant={alert.state.toLowerCase() as any}>{stateConfig[alert.state as keyof typeof stateConfig].label}</Badge>
                    </td>
                    <td className="text-body-sm text-text-primary max-w-md truncate">{alert.message}</td>
                    <td>
                      <div className="flex items-center gap-1">
                        {alert.state === 'ACTIVE' && (
                          <Button variant="ghost" size="sm" className="h-8 px-2">
                            Acknowledge
                          </Button>
                        )}
                        <Button variant="ghost" size="sm" className="h-8 px-2">
                          View
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function AlertRow({ alert }: { alert: typeof mockAlerts[0] }) {
  const config = severityConfig[alert.severity];
  const Icon = config.icon;

  return (
    <div className={config.bg + ' border-l-4 ' + config.border + ' rounded-r-button p-4 mb-3 animate-slide-down'}>
      <div className="flex items-start gap-3">
        <Icon className={config.color + ' w-5 h-5 flex-shrink-0 mt-0.5'} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-body-sm">{config.border.replace('border-', '').toUpperCase()} ALERT</span>
            <span className="text-caption text-text-secondary">{new Date(alert.createdAt).toLocaleString()}</span>
          </div>
          <p className="text-body text-text-primary mb-2">{alert.message}</p>
          <div className="flex items-center gap-3 text-caption text-text-secondary">
            {alert.triggerValue !== undefined && <span>Trigger: <span className="font-mono text-text-primary">{alert.triggerValue}</span></span>}
            {alert.thresholdValue !== undefined && <span>Threshold: <span className="font-mono text-text-primary">{alert.thresholdValue}</span></span>}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {!alert.acknowledged && (
            <Button variant="secondary" size="sm" onClick={() => {}}>
              Acknowledge
            </Button>
          )}
          <Button variant="ghost" size="sm">
            View Details
          </Button>
        </div>
      </div>
    </div>
  );
}