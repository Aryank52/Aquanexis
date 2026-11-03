import { useState } from 'react';
import {
  CheckCircle,
  XCircle,
  Clock,
  Play,
  RotateCcw,
  AlertTriangle,
  Info,
  ClipboardCheck,
} from 'lucide-react';
import { format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import {
  useMaintenanceEvents,
  useStartVerification,
  useCompleteVerification,
  useVerification,
} from '@/hooks/useMaintenance';
import type { VerificationRunResponse, VerificationState } from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const stateVariant: Record<
  VerificationState,
  'success' | 'warning' | 'critical' | 'info' | 'default'
> = {
  PENDING: 'info',
  RUNNING: 'warning',
  PASSED: 'success',
  FAILED: 'critical',
  CANCELLED: 'default',
};

function stateIcon(state: VerificationState) {
  switch (state) {
    case 'PASSED':
      return <CheckCircle className="h-4 w-4 text-success" />;
    case 'FAILED':
      return <XCircle className="h-4 w-4 text-critical" />;
    case 'RUNNING':
      return <RotateCcw className="h-4 w-4 animate-spin text-warning" />;
    case 'PENDING':
      return <Clock className="h-4 w-4 text-info" />;
    default:
      return <XCircle className="h-4 w-4 text-text-muted" />;
  }
}

function CheckIcon({ passed }: { passed: boolean }): JSX.Element {
  return passed ? (
    <CheckCircle className="h-4 w-4 text-success" />
  ) : (
    <XCircle className="h-4 w-4 text-critical" />
  );
}

export function VerificationPage() {
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [showCompleteForm, setShowCompleteForm] = useState<VerificationRunResponse | null>(null);
  const [currentReadings, setCurrentReadings] = useState<Record<string, number>>({});

  const events = useMaintenanceEvents({
    device_id: DEVICE_ID,
    event_type: 'VERIFICATION',
    limit: 20,
  });
  const startVerification = useStartVerification();
  const completeVerification = useCompleteVerification();
  const verificationDetail = useVerification(selectedEventId ?? '');

  if (events.isError) {
    return (
      <QueryError
        message={(events.error as Error)?.message ?? 'Failed to load verification events'}
        onRetry={events.refetch}
      />
    );
  }

  const handleStartVerification = (
    maintenanceEventId: string,
    baselineBefore?: Record<string, unknown>
  ) => {
    startVerification.mutate(
      {
        device_id: DEVICE_ID,
        maintenance_event_id: maintenanceEventId,
        baseline_before: baselineBefore,
      },
      {
        onSuccess: newVerification => {
          setSelectedEventId(newVerification.id);
          events.refetch();
        },
      }
    );
  };

  const handleCompleteVerification = (verificationId: string) => {
    completeVerification.mutate(
      {
        verificationId,
        data: { current_readings: currentReadings },
      },
      {
        onSuccess: completed => {
          setSelectedEventId(completed.id);
          setShowCompleteForm(null);
          setCurrentReadings({});
          events.refetch();
        },
      }
    );
  };

  const handleReadingChange = (sensor: string, value: string) => {
    setCurrentReadings(prev => ({ ...prev, [sensor]: parseFloat(value) || 0 }));
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Verification Runs</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Post-maintenance verification and baseline validation
          </p>
        </div>
        <Button
          variant="ghost"
          onClick={() => events.refetch()}
          className="flex items-center gap-2"
        >
          <RotateCcw className="h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Verification List */}
      <Card>
        <CardHeader>
          <CardTitle>Verification History</CardTitle>
        </CardHeader>
        <CardContent>
          {events.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded" />
              ))}
            </div>
          ) : !events.data || events.data.length === 0 ? (
            <EmptyState
              title="No verification runs"
              description="Start a verification after a maintenance event"
            />
          ) : (
            <div className="space-y-3">
              {events.data.map(event => {
                const state = (event.verification_status as VerificationState) || 'PENDING';
                return (
                  <div
                    key={event.id}
                    className="border-subtle flex items-center justify-between rounded-card border bg-surface p-4"
                  >
                    <div className="flex items-center gap-4">
                      {stateIcon(state)}
                      <div>
                        <div className="text-text-primary text-body-sm font-medium">
                          Maintenance #{event.id.slice(0, 8)}
                        </div>
                        <div className="text-caption text-text-muted">
                          {event.event_type.replace('_', ' ')} {' • '}
                          {format(new Date(event.timestamp), 'dd MMM yyyy HH:mm')}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={stateVariant[state]}>{state}</Badge>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setSelectedEventId(event.id)}
                        disabled={verificationDetail.isLoading}
                      >
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

      {/* Start New Verification */}
      <Card className="border-info bg-info/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Play className="h-4 w-4 text-info" /> Start New Verification
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-4 text-body-sm text-text-secondary">
            Select a completed maintenance event to start a post-maintenance verification run.
          </p>
          <div className="space-y-2">
            {events.data
              ?.filter(e => e.verification_status === 'PENDING' || !e.verification_status)
              .map(event => (
                <div
                  key={event.id}
                  className="border-subtle flex items-center justify-between rounded-button border bg-surface p-3"
                >
                  <div>
                    <div className="text-body-sm font-medium">
                      Maintenance #{event.id.slice(0, 8)}
                    </div>
                    <div className="text-caption text-text-muted">
                      {event.event_type.replace('_', ' ')} •{' '}
                      {format(new Date(event.timestamp), 'dd MMM yyyy HH:mm')}
                    </div>
                  </div>
                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() =>
                      handleStartVerification(
                        event.id,
                        (event.post_maintenance_state as Record<string, unknown>) || undefined
                      )
                    }
                    disabled={startVerification.isPending}
                  >
                    {startVerification.isPending ? 'Starting…' : 'Start Verification'}
                  </Button>
                </div>
              ))}
            {(!events.data ||
              events.data.filter(e => e.verification_status === 'PENDING' || !e.verification_status)
                .length === 0) && (
              <p className="py-4 text-center text-body-sm text-text-muted">
                No maintenance events pending verification
              </p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Verification Detail Drawer */}
      {selectedEventId && (
        <VerificationDetailDrawer
          verification={verificationDetail.data}
          isLoading={verificationDetail.isLoading}
          onClose={() => setSelectedEventId(null)}
          onComplete={showCompleteForm ? handleCompleteVerification : undefined}
          isCompleting={completeVerification.isPending}
        />
      )}

      {/* Complete Verification Form */}
      {showCompleteForm && (
        <CompleteVerificationForm
          currentReadings={currentReadings}
          onReadingChange={handleReadingChange}
          onSubmit={() => handleCompleteVerification(showCompleteForm.id)}
          onCancel={() => {
            setShowCompleteForm(null);
            setCurrentReadings({});
          }}
          isSubmitting={completeVerification.isPending}
        />
      )}
    </div>
  );
}

interface VerificationDetailDrawerProps {
  verification: VerificationRunResponse | undefined;
  isLoading: boolean;
  onClose: () => void;
  onComplete?: (id: string) => void;
  isCompleting: boolean;
}

function VerificationDetailDrawer({
  verification,
  isLoading,
  onClose,
  onComplete,
  isCompleting,
}: VerificationDetailDrawerProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center sm:items-center">
      <div className="fixed inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative max-h-[80vh] w-full max-w-2xl overflow-y-auto rounded-t-lg bg-elevated shadow-elevated sm:rounded-card">
        <div className="border-subtle sticky top-0 flex items-center justify-between border-b bg-elevated p-4">
          <h2 className="text-h2 font-semibold">Verification Details</h2>
          <button onClick={onClose} className="rounded-button p-1 hover:bg-hover">
            ✕
          </button>
        </div>

        {isLoading ? (
          <div className="space-y-4 p-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : verification ? (
          <div className="space-y-6 p-6">
            <div className="flex items-center gap-4 rounded-card bg-surface p-4">
              {stateIcon(verification.state)}
              <div>
                <div className="text-text-primary text-h3 font-semibold">
                  {verification.state === 'PASSED'
                    ? 'Verification Passed'
                    : verification.state === 'FAILED'
                      ? 'Verification Failed'
                      : verification.state === 'RUNNING'
                        ? 'Running Checks…'
                        : 'Pending'}
                </div>
                <div className="text-caption text-text-muted">ID: {verification.id}</div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 text-body-sm">
              <div>
                <span className="text-text-secondary">Started:</span>{' '}
                <span className="ml-2">
                  {verification.started_at
                    ? format(new Date(verification.started_at), 'dd MMM yyyy HH:mm')
                    : '—'}
                </span>
              </div>
              <div>
                <span className="text-text-secondary">Completed:</span>{' '}
                <span className="ml-2">
                  {verification.completed_at
                    ? format(new Date(verification.completed_at), 'dd MMM yyyy HH:mm')
                    : '—'}
                </span>
              </div>
              <div>
                <span className="text-text-secondary">Maintenance Event:</span>{' '}
                <span className="ml-2 font-mono">{verification.maintenance_event_id}</span>
              </div>
              <div>
                <span className="text-text-secondary">Device:</span>{' '}
                <span className="ml-2 font-mono">{verification.device_id}</span>
              </div>
            </div>

            {verification.checks && verification.checks.length > 0 && (
              <div>
                <h3 className="mb-3 text-body font-medium">Checks</h3>
                <div className="space-y-2">
                  {verification.checks.map((check, i) => {
                    const details = (check as Record<string, unknown>).details;
                    const hasDetails =
                      details !== undefined &&
                      details !== null &&
                      Object.keys(details as Record<string, unknown>).length > 0;
                    const passed = (check as Record<string, unknown>).passed as boolean;
                    const checkName = String(check.name ?? 'Check ' + (i + 1));
                    return (
                      <div
                        key={i}
                        className="border-subtle flex items-center justify-between rounded-button border bg-surface p-3"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-text-primary text-body-sm">{checkName}</span>
                        </div>
                        {hasDetails ? (
                          <span className="text-caption text-text-muted">
                            {JSON.stringify(details)}
                          </span>
                        ) : null}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {verification.failure_reasons && verification.failure_reasons.length > 0 && (
              <div className="rounded-card border border-critical/30 bg-critical/10 p-4">
                <h3 className="mb-2 flex items-center gap-2 text-body font-medium text-critical">
                  <AlertTriangle className="h-4 w-4" /> Failure Reasons
                </h3>
                <ul className="space-y-1">
                  {verification.failure_reasons.map((reason, i) => (
                    <li key={i} className="text-text-primary flex items-center gap-2 text-body-sm">
                      <XCircle className="h-3 w-3 text-critical" /> {reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {verification.baseline_before &&
              Object.keys(verification.baseline_before).length > 0 && (
                <div>
                  <h3 className="mb-2 text-body font-medium">Baseline Before</h3>
                  <pre className="text-text-primary bg-background max-h-40 overflow-auto rounded-button p-3 text-caption">
                    {JSON.stringify(verification.baseline_before, null, 2)}
                  </pre>
                </div>
              )}

            {verification.baseline_after && Object.keys(verification.baseline_after).length > 0 && (
              <div>
                <h3 className="mb-2 text-body font-medium">Baseline After</h3>
                <pre className="text-text-primary bg-background max-h-40 overflow-auto rounded-button p-3 text-caption">
                  {JSON.stringify(verification.baseline_after, null, 2)}
                </pre>
              </div>
            )}

            <div className="border-subtle flex gap-2 border-t pt-4">
              {onComplete && verification.state === 'PENDING' && (
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() => onComplete(verification.id)}
                  disabled={isCompleting}
                >
                  {isCompleting ? 'Completing…' : 'Complete Verification'}
                </Button>
              )}
              <Button variant="ghost" className="flex-1" onClick={onClose}>
                Close
              </Button>
            </div>
          </div>
        ) : (
          <div className="p-6 text-center text-text-muted">Verification not found</div>
        )}
      </div>
    </div>
  );
}

interface CompleteVerificationFormProps {
  currentReadings: Record<string, number>;
  onReadingChange: (sensor: string, value: string) => void;
  onSubmit: () => void;
  onCancel: () => void;
  isSubmitting: boolean;
}

function CompleteVerificationForm({
  currentReadings,
  onReadingChange,
  onSubmit,
  onCancel,
  isSubmitting,
}: CompleteVerificationFormProps) {
  // Common sensors to check
  const sensors = [
    { key: 'tds', label: 'TDS (ppm)', unit: 'ppm' },
    { key: 'ph', label: 'pH', unit: '' },
    { key: 'turbidity', label: 'Turbidity (NTU)', unit: 'NTU' },
    { key: 'temperature', label: 'Temperature (°C)', unit: '°C' },
    { key: 'pressure', label: 'Pressure (kPa)', unit: 'kPa' },
    { key: 'flow', label: 'Flow (L/min)', unit: 'L/min' },
    { key: 'tank_level', label: 'Tank Level (%)', unit: '%' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-card bg-elevated p-6 shadow-elevated">
        <h2 className="mb-4 text-h2 font-semibold">Complete Verification</h2>
        <p className="mb-4 text-body-sm text-text-secondary">
          Enter current sensor readings to complete the verification run.
        </p>

        <div className="max-h-60 space-y-3 overflow-y-auto">
          {sensors.map(sensor => (
            <div
              key={sensor.key}
              className="border-subtle flex items-center gap-4 rounded-button border bg-surface p-3"
            >
              <div className="flex-1">
                <label className="text-caption text-text-secondary">{sensor.label}</label>
                <input
                  type="number"
                  step="any"
                  className="input mt-1 w-full"
                  value={currentReadings[sensor.key] ?? ''}
                  onChange={e => onReadingChange(sensor.key, e.target.value)}
                  placeholder={`Current ${sensor.label}`}
                />
              </div>
              {sensor.unit && <span className="text-caption text-text-muted">{sensor.unit}</span>}
            </div>
          ))}
        </div>

        <div className="border-subtle flex gap-2 border-t pt-4">
          <Button variant="primary" className="flex-1" onClick={onSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Completing…' : 'Complete Verification'}
          </Button>
          <Button variant="ghost" className="flex-1" onClick={onCancel}>
            Cancel
          </Button>
        </div>
      </div>
    </div>
  );
}
