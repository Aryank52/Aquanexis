import { useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { CheckCircle, AlertTriangle, XCircle, RefreshCw, Shield } from 'lucide-react';
import { Card, CardContent } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import { useDevice } from '@/hooks/useDevice';
import { useLatestTelemetry } from '@/hooks/useTelemetry';
import { useDiagnostics } from '@/hooks/useDiagnostics';
import { healthApi } from '@/api/endpoints';
import type { HealthCheckResponse } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

type CheckStatus = 'pass' | 'warn' | 'fail' | 'loading';

interface ReadinessCheck {
  name: string;
  status: CheckStatus;
  detail: string;
}

const statusIcon: Record<CheckStatus, { icon: typeof CheckCircle; color: string }> = {
  pass: { icon: CheckCircle, color: 'text-success' },
  warn: { icon: AlertTriangle, color: 'text-warning' },
  fail: { icon: XCircle, color: 'text-critical' },
  loading: { icon: RefreshCw, color: 'text-text-muted animate-spin' },
};

export function ReadinessPage() {
  const queryClient = useQueryClient();
  const device = useDevice(DEVICE_ID);
  const telemetry = useLatestTelemetry(DEVICE_ID);
  const diagnostics = useDiagnostics(DEVICE_ID);

  const health = useQuery<HealthCheckResponse>({
    queryKey: ['health'],
    queryFn: () => healthApi.check(),
    refetchInterval: 10000,
  });

  // ── Derive checks ────────────────────────────────────────────────────────
  const checks: ReadinessCheck[] = [];

  // 1. Device Connected
  if (device.isLoading) {
    checks.push({ name: 'Device Connected', status: 'loading', detail: 'Checking…' });
  } else if (device.data?.status === 'online') {
    checks.push({ name: 'Device Connected', status: 'pass', detail: `Device "${device.data.name}" is online` });
  } else if (device.data?.status === 'degraded') {
    checks.push({ name: 'Device Connected', status: 'warn', detail: 'Device is in degraded state' });
  } else {
    checks.push({ name: 'Device Connected', status: 'fail', detail: `Device is ${device.data?.status ?? 'unreachable'}` });
  }

  // 2. Backend Healthy
  if (health.isLoading) {
    checks.push({ name: 'Backend Healthy', status: 'loading', detail: 'Checking…' });
  } else if (health.data?.status === 'ok') {
    checks.push({ name: 'Backend Healthy', status: 'pass', detail: 'All backend services operational' });
  } else if (health.data?.status === 'degraded') {
    checks.push({ name: 'Backend Healthy', status: 'warn', detail: 'Backend is in degraded state' });
  } else {
    checks.push({ name: 'Backend Healthy', status: 'fail', detail: health.isError ? 'Backend unreachable' : `Backend status: ${health.data?.status ?? 'unknown'}` });
  }

  // 3. Sensors Ready
  if (telemetry.isLoading) {
    checks.push({ name: 'Sensors Ready', status: 'loading', detail: 'Checking…' });
  } else if (telemetry.data?.quality?.flags) {
    const flags = telemetry.data.quality.flags;
    const entries = Object.entries(flags);
    const total = entries.length;
    const okCount = entries.filter(([, f]) => f.range === 'OK' && f.rate === 'OK' && f.cross_sensor === 'OK').length;
    const hasBad = entries.some(([, f]) => f.range === 'BAD' || f.rate === 'BAD' || f.cross_sensor === 'BAD');
    if (hasBad) {
      checks.push({ name: 'Sensors Ready', status: 'fail', detail: `${okCount}/${total} sensors healthy — some sensors reporting BAD` });
    } else if (okCount < total) {
      checks.push({ name: 'Sensors Ready', status: 'warn', detail: `${okCount}/${total} sensors healthy — some sensors suspect` });
    } else {
      checks.push({ name: 'Sensors Ready', status: 'pass', detail: `All ${total} sensors reporting OK` });
    }
  } else {
    checks.push({ name: 'Sensors Ready', status: 'fail', detail: 'No sensor quality data available' });
  }

  // 4. Data Fresh
  if (telemetry.isLoading) {
    checks.push({ name: 'Data Fresh', status: 'loading', detail: 'Checking…' });
  } else if (telemetry.data?.received_at) {
    const ageS = (Date.now() - new Date(telemetry.data.received_at).getTime()) / 1000;
    if (ageS < 30) {
      checks.push({ name: 'Data Fresh', status: 'pass', detail: `Last reading ${Math.round(ageS)}s ago` });
    } else if (ageS < 120) {
      checks.push({ name: 'Data Fresh', status: 'warn', detail: `Last reading ${Math.round(ageS)}s ago — slightly stale` });
    } else {
      checks.push({ name: 'Data Fresh', status: 'fail', detail: `Last reading ${Math.round(ageS)}s ago — data is stale` });
    }
  } else {
    checks.push({ name: 'Data Fresh', status: 'fail', detail: 'No telemetry data received' });
  }

  // 5. Diagnostics OK
  if (diagnostics.isLoading) {
    checks.push({ name: 'Diagnostics OK', status: 'loading', detail: 'Checking…' });
  } else if (diagnostics.data) {
    const d = diagnostics.data;
    const hasCritical = d.leak.detected || d.pressure.status === 'critical' || d.pump.status === 'fault';
    const hasWarning = d.pressure.status === 'elevated' || d.flow.status === 'low' || d.pump.status === 'degraded' || d.leak.probability > 0.3;
    if (hasCritical) {
      checks.push({ name: 'Diagnostics OK', status: 'fail', detail: 'Critical diagnostic issue detected' });
    } else if (hasWarning) {
      checks.push({ name: 'Diagnostics OK', status: 'warn', detail: 'Minor diagnostic warnings present' });
    } else {
      checks.push({ name: 'Diagnostics OK', status: 'pass', detail: 'All diagnostics normal' });
    }
  } else {
    checks.push({ name: 'Diagnostics OK', status: 'fail', detail: 'Diagnostics data unavailable' });
  }

  // ── Overall ───────────────────────────────────────────────────────────────
  const anyLoading = checks.some(c => c.status === 'loading');
  const anyFail = checks.some(c => c.status === 'fail');
  const anyWarn = checks.some(c => c.status === 'warn');

  let overallLabel: string;
  let overallVariant: 'success' | 'warning' | 'critical' | 'default';
  if (anyLoading) {
    overallLabel = 'Checking…';
    overallVariant = 'default';
  } else if (anyFail) {
    overallLabel = 'Not Ready';
    overallVariant = 'critical';
  } else if (anyWarn) {
    overallLabel = 'Degraded';
    overallVariant = 'warning';
  } else {
    overallLabel = 'System Ready';
    overallVariant = 'success';
  }

  const handleRecheck = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['device'] });
    queryClient.invalidateQueries({ queryKey: ['telemetry'] });
    queryClient.invalidateQueries({ queryKey: ['diagnostics'] });
    queryClient.invalidateQueries({ queryKey: ['health'] });
  }, [queryClient]);

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">System Readiness</h1>
          <p className="text-body-sm text-text-secondary mt-1">Pre-flight checks for safe and reliable operation</p>
        </div>
        <Button variant="secondary" onClick={handleRecheck}>
          <RefreshCw className="h-4 w-4 mr-1" /> Recheck
        </Button>
      </div>

      {/* Overall Status */}
      <Card className={cn(
        'text-center py-8',
        overallVariant === 'success' && 'border-success bg-success/5',
        overallVariant === 'warning' && 'border-warning bg-warning/5',
        overallVariant === 'critical' && 'border-critical bg-critical/5',
      )}>
        <CardContent>
          <Shield className={cn('h-12 w-12 mx-auto mb-3', `text-${overallVariant}`)} />
          <div className="text-h1 font-semibold">{overallLabel}</div>
          <Badge variant={overallVariant} className="mt-2">
            {checks.filter(c => c.status === 'pass').length}/{checks.length} checks passed
          </Badge>
        </CardContent>
      </Card>

      {/* Individual Checks */}
      <div className="space-y-3">
        {checks.map(check => {
          const cfg = statusIcon[check.status];
          const Icon = cfg.icon;
          return (
            <Card key={check.name}>
              <CardContent className="p-4 flex items-center gap-4">
                <Icon className={cn('h-5 w-5 flex-shrink-0', cfg.color)} />
                <div className="flex-1">
                  <div className="text-body-sm font-medium text-text-primary">{check.name}</div>
                  <div className="text-caption text-text-secondary">{check.detail}</div>
                </div>
                <Badge variant={check.status === 'pass' ? 'success' : check.status === 'warn' ? 'warning' : check.status === 'fail' ? 'critical' : 'default'}>
                  {check.status === 'pass' ? 'PASS' : check.status === 'warn' ? 'WARN' : check.status === 'fail' ? 'FAIL' : '…'}
                </Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
