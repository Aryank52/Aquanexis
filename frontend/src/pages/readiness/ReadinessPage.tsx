import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { CheckCircle, AlertTriangle, XCircle, Clock, Database, Cpu, Shield, Bell, Wifi, Zap, Filter, Gauge, RotateCcw, HelpCircle } from 'lucide-react';

const checks = [
  { id: 'device', label: 'Device Connected', status: 'pass' as const, detail: 'Last seen 3s ago', icon: Wifi },
  { id: 'sensors', label: 'Sensors Ready', status: 'pass' as const, detail: '9/9 GOOD', icon: Gauge },
  { id: 'calibration', label: 'Calibration Current', status: 'warn' as const, detail: 'pH due in 3 days', icon: RotateCcw },
  { id: 'freshness', label: 'Data Fresh', status: 'pass' as const, detail: '3 seconds', icon: Clock },
  { id: 'backend', label: 'Backend Healthy', status: 'pass' as const, detail: 'All services up', icon: Cpu },
  { id: 'database', label: 'Database Healthy', status: 'pass' as const, detail: 'Primary + replica', icon: Database },
  { id: 'models', label: 'Models Ready', status: 'pass' as const, detail: 'v1.2.0 loaded', icon: Filter },
  { id: 'alerts', label: 'Alert System Ready', status: 'pass' as const, detail: 'Email + Webhook', icon: Bell },
  { id: 'safety', label: 'Safety System Ready', status: 'pass' as const, detail: 'Valves responsive', icon: Shield },
  { id: 'tests', label: 'Last Test Passed', status: 'pass' as const, detail: '2026-10-30 02:00', icon: HelpCircle },
];

const statusConfig = {
  pass: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/10', border: 'border-success', label: 'PASS' },
  warn: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning', label: 'WARN' },
  fail: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', border: 'border-critical', label: 'FAIL' },
};

export function ReadinessPage() {
  const allPass = checks.every(c => c.status === 'pass');
  const warnCount = checks.filter(c => c.status === 'warn').length;
  const failCount = checks.filter(c => c.status === 'fail').length;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">System Readiness</h1>
          <p className="text-body-sm text-text-secondary mt-1">Engineering readiness checklist for operational deployment</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="primary" iconLeft={<RotateCcw className="w-4 h-4" />}>
            Run Full Diagnostic
          </Button>
          <Button variant="secondary" iconLeft={<Gauge className="w-4 h-4" />}>
            View Test Results
          </Button>
        </div>
      </div>

      {/* Overall Status */}
      <Card className={allPass ? 'border-success' : warnCount > 0 ? 'border-warning' : 'border-critical'}>
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className={cn('w-16 h-16 rounded-xl flex items-center justify-center', allPass ? 'bg-success/10' : warnCount > 0 ? 'bg-warning/10' : 'bg-critical/10')}>
                {allPass ? (
                  <CheckCircle className="w-8 h-8 text-success" />
                ) : warnCount > 0 ? (
                  <AlertTriangle className="w-8 h-8 text-warning" />
                ) : (
                  <XCircle className="w-8 h-8 text-critical" />
                )}
              </div>
              <div>
                <div className={cn('text-data-xl font-bold', allPass ? 'text-success' : warnCount > 0 ? 'text-warning' : 'text-critical')}>
                  {allPass ? 'READY' : warnCount > 0 ? 'ATTENTION NEEDED' : 'NOT READY'}
                </div>
                <div className="text-body-sm text-text-secondary">
                  {checks.filter(c => c.status === 'pass').length} of {checks.length} checks passing
                  {warnCount > 0 && <span className="ml-2 text-warning">• {warnCount} warnings</span>}
                  {failCount > 0 && <span className="ml-2 text-critical">• {failCount} failures</span>}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Badge variant={allPass ? 'success' : warnCount > 0 ? 'warning' : 'critical'} className="text-body">
                {allPass ? 'SYSTEM READY' : 'REVIEW REQUIRED'}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Readiness Checklist */}
      <Card>
        <CardHeader>
          <CardTitle>Readiness Checklist</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {checks.map((check) => {
              const config = statusConfig[check.status];
              const Icon = config.icon;
              const checkIcon = check.icon;
              
              return (
                <div
                  key={check.id}
                  className={cn(
                    'flex items-center gap-4 p-4 rounded-button border transition-colors',
                    config.bg,
                    config.border
                  )}
                >
                  <checkIcon className="w-5 h-5 text-info flex-shrink-0" />
                  <Icon className={cn('w-5 h-5 flex-shrink-0', config.color)} />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-text-primary">{check.label}</p>
                    <p className="text-caption text-text-secondary">{check.detail}</p>
                  </div>
                  <Badge variant={check.status}>{config.label}</Badge>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* System Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Backend Services</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { name: 'API Server', status: 'healthy' },
                { name: 'WebSocket Server', status: 'healthy' },
                { name: 'Background Workers', status: 'healthy' },
                { name: 'ML Inference', status: 'healthy' },
                { name: 'Notification Service', status: 'healthy' },
              ].map((svc) => (
                <div key={svc.name} className="flex items-center justify-between">
                  <span className="text-body-sm text-text-primary">{svc.name}</span>
                  <Badge variant="success"><CheckCircle className="w-3 h-3 mr-1" /> Running</Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Quality</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-body-sm text-text-primary">Data Freshness</span>
                <span className="font-mono text-data text-success">3s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body-sm text-text-primary">Sensor Quality</span>
                <span className="text-caption text-success">9/9 GOOD</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body-sm text-text-primary">Ingestion Rate</span>
                <span className="text-caption text-text-secondary">1/10s</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-body-sm text-text-primary">Error Rate (24h)</span>
                <span className="text-caption text-success">0.0%</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Test Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[
                { name: 'Full Diagnostic Suite', date: '2026-10-30 02:00', status: 'passed' },
                { name: 'Safety System Test', date: '2026-10-29 02:00', status: 'passed' },
                { name: 'ML Model Validation', date: '2026-10-28 02:00', status: 'passed' },
                { name: 'Alert Pipeline Test', date: '2026-10-27 02:00', status: 'passed' },
                { name: 'Database Integrity', date: '2026-10-26 02:00', status: 'passed' },
              ].map((test) => (
                <div key={test.name} className="flex items-center justify-between p-2 bg-surface rounded-button border border-subtle">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-success" />
                    <span className="text-body-sm text-text-primary">{test.name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="success">Passed</Badge>
                    <span className="text-caption text-text-secondary">{test.date}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}