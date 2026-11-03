import { useEffect, useRef, useState } from 'react';
import { X, Clock, CheckCircle2, AlertTriangle, XCircle, Info, BellOff, Check } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAcknowledgeAlert, useResolveAlert, useSnoozeAlert } from '@/hooks/useAlerts';
import type { AlertResponse, AlertSeverity } from '@/types/api';
import { formatDistanceToNow, format } from 'date-fns';

const SNOOZE_OPTIONS = [
  { label: '15 minutes', value: 15 },
  { label: '30 minutes', value: 30 },
  { label: '1 hour', value: 60 },
  { label: '4 hours', value: 240 },
  { label: '24 hours', value: 1440 },
];

const severityStyles: Record<
  AlertSeverity,
  { icon: typeof XCircle; color: string; bg: string; border: string }
> = {
  CRITICAL: {
    icon: XCircle,
    color: 'text-critical',
    bg: 'bg-critical/10',
    border: 'border-critical/30',
  },
  WARNING: {
    icon: AlertTriangle,
    color: 'text-warning',
    bg: 'bg-warning/10',
    border: 'border-warning/30',
  },
  INFO: { icon: Info, color: 'text-info', bg: 'bg-info/10', border: 'border-info/30' },
};

interface Props {
  alert: AlertResponse | null;
  open: boolean;
  onClose: () => void;
  currentUser?: string;
}

export function AlertEvidenceDrawer({ alert, open, onClose, currentUser = 'operator' }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const [showSnooze, setShowSnooze] = useState(false);
  const [resolveReason, setResolveReason] = useState('');
  const [showResolveForm, setShowResolveForm] = useState(false);

  const acknowledge = useAcknowledgeAlert();
  const resolve = useResolveAlert();
  const snooze = useSnoozeAlert();

  // Focus trap
  useEffect(() => {
    if (open) {
      panelRef.current?.focus();
    }
  }, [open]);

  // Escape to close
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    if (open) document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [open, onClose]);

  if (!alert) return null;
  const sev = severityStyles[alert.severity];
  const SevIcon = sev.icon;

  const handleAcknowledge = () => {
    acknowledge.mutate({ alertId: alert.id, data: { acknowledged_by: currentUser } });
  };

  const handleResolve = () => {
    if (!resolveReason.trim()) return;
    resolve.mutate(
      { alertId: alert.id, data: { resolved_by: currentUser, resolved_reason: resolveReason } },
      {
        onSuccess: onClose,
      }
    );
  };

  const handleSnooze = (minutes: number) => {
    snooze.mutate(
      { alertId: alert.id, data: { snoozed_by: currentUser, snooze_duration_minutes: minutes } },
      {
        onSuccess: () => {
          setShowSnooze(false);
          onClose();
        },
      }
    );
  };

  return (
    <>
      {/* Backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel */}
      <div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-title"
        className={cn(
          'fixed inset-y-0 right-0 z-50 w-full max-w-md bg-elevated shadow-elevated',
          'flex flex-col outline-none transition-transform duration-300 ease-out',
          open ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className={cn('border-subtle flex items-start gap-3 border-b p-5', sev.bg)}>
          <SevIcon className={cn('mt-0.5 h-5 w-5 flex-shrink-0', sev.color)} />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <span
                id="drawer-title"
                className={cn('text-caption font-semibold uppercase tracking-wide', sev.color)}
              >
                {alert.severity}
              </span>
              <span className="text-caption text-text-muted">
                {alert.alert_code.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-text-primary mt-1 text-body-sm">
              {alert.message || 'No message available.'}
            </p>
            <p className="mt-1 text-caption text-text-muted">
              {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-button p-1.5 text-text-muted hover:bg-hover"
            aria-label="Close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 space-y-5 overflow-y-auto p-5">
          {/* Trigger values */}
          {(alert.trigger_value !== null || alert.threshold_value !== null) && (
            <section className="grid grid-cols-2 gap-3">
              {alert.trigger_value !== null && (
                <div className="border-subtle rounded-button border bg-surface p-3">
                  <p className="text-caption text-text-muted">Trigger Value</p>
                  <p className="text-text-primary font-mono text-data font-semibold">
                    {alert.trigger_value}
                  </p>
                </div>
              )}
              {alert.threshold_value !== null && (
                <div className="border-subtle rounded-button border bg-surface p-3">
                  <p className="text-caption text-text-muted">Threshold</p>
                  <p className="text-text-primary font-mono text-data font-semibold">
                    {alert.threshold_value}
                  </p>
                </div>
              )}
            </section>
          )}

          {/* Evidence Details */}
          {alert.evidence && Object.keys(alert.evidence).length > 0 && (
            <section aria-label="Alert evidence">
              <h2 className="text-text-primary mb-2 text-body-sm font-semibold">
                Diagnostic Evidence
              </h2>
              <div className="border-subtle space-y-1.5 rounded-button border bg-surface p-3">
                {Object.entries(alert.evidence).map(([key, val]) => (
                  <div key={key} className="flex items-start justify-between gap-2 text-caption">
                    <span className="font-medium text-text-secondary">
                      {key.replace(/_/g, ' ')}
                    </span>
                    <span className="text-text-primary break-all text-right font-mono">
                      {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Timeline */}
          <section aria-label="Alert timeline">
            <h2 className="text-text-primary mb-3 text-body-sm font-semibold">Timeline</h2>
            <div className="space-y-2">
              <TimelineItem
                icon={Clock}
                label="Created"
                time={alert.created_at}
                color="text-text-muted"
              />
              {alert.acknowledged_at && (
                <TimelineItem
                  icon={CheckCircle2}
                  label={`Acknowledged by ${alert.acknowledged_by || 'user'}`}
                  time={alert.acknowledged_at}
                  color="text-warning"
                />
              )}
              {alert.resolved_at && (
                <TimelineItem
                  icon={CheckCircle2}
                  label={`Resolved by ${alert.resolved_by || 'user'}`}
                  time={alert.resolved_at}
                  color="text-success"
                />
              )}
              {alert.snoozed_until && (
                <TimelineItem
                  icon={BellOff}
                  label="Snoozed until"
                  time={alert.snoozed_until}
                  color="text-info"
                />
              )}
            </div>
          </section>

          {/* Snooze picker */}
          {showSnooze && (
            <section className="border-subtle space-y-3 rounded-card border bg-surface p-4">
              <h3 className="text-text-primary text-body-sm font-semibold">Snooze Duration</h3>
              <div className="grid grid-cols-2 gap-2">
                {SNOOZE_OPTIONS.map(opt => (
                  <button
                    key={opt.value}
                    className="btn btn-secondary btn-sm text-center"
                    onClick={() => handleSnooze(opt.value)}
                    disabled={snooze.isPending}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
              <button className="btn btn-ghost btn-sm w-full" onClick={() => setShowSnooze(false)}>
                Cancel
              </button>
            </section>
          )}

          {/* Resolve form */}
          {showResolveForm && (
            <section className="border-subtle space-y-3 rounded-card border bg-surface p-4">
              <h3 className="text-text-primary text-body-sm font-semibold">Resolve Alert</h3>
              <div>
                <label className="label" htmlFor="resolve-reason">
                  Resolution reason
                </label>
                <textarea
                  id="resolve-reason"
                  className="input resize-none"
                  rows={2}
                  placeholder="e.g. Leak fixed, valve reopened"
                  value={resolveReason}
                  onChange={e => setResolveReason(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <button
                  className="btn btn-primary btn-sm flex-1"
                  onClick={handleResolve}
                  disabled={!resolveReason.trim() || resolve.isPending}
                >
                  {resolve.isPending ? 'Resolving…' : 'Confirm Resolve'}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => setShowResolveForm(false)}>
                  Cancel
                </button>
              </div>
            </section>
          )}
        </div>

        {/* Actions */}
        {alert.status !== 'RESOLVED' &&
          alert.status !== 'AUTO_CLEARED' &&
          !showResolveForm &&
          !showSnooze && (
            <div className="border-subtle flex flex-wrap gap-2 border-t p-5">
              {(alert.status === 'OPEN' || alert.status === 'DETECTED') && (
                <button
                  className="btn btn-secondary btn-sm flex-1"
                  onClick={handleAcknowledge}
                  disabled={acknowledge.isPending}
                >
                  <Check className="h-4 w-4" />
                  {acknowledge.isPending ? 'Acknowledging…' : 'Acknowledge'}
                </button>
              )}
              {(alert.status === 'OPEN' ||
                alert.status === 'DETECTED' ||
                alert.status === 'ACKNOWLEDGED') && (
                <>
                  <button
                    className="btn btn-primary btn-sm flex-1"
                    onClick={() => setShowResolveForm(true)}
                  >
                    Resolve
                  </button>
                  <button
                    className="btn btn-ghost btn-sm"
                    onClick={() => setShowSnooze(true)}
                    aria-label="Snooze alert"
                  >
                    <BellOff className="h-4 w-4" />
                  </button>
                </>
              )}
            </div>
          )}
      </div>
    </>
  );
}

function TimelineItem({
  icon: Icon,
  label,
  time,
  color,
}: {
  icon: typeof Clock;
  label: string;
  time: string;
  color: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <Icon className={cn('h-4 w-4 flex-shrink-0', color)} />
      <div className="min-w-0 flex-1">
        <span className="text-caption text-text-secondary">{label}</span>
      </div>
      <span className="font-mono text-caption text-text-muted">
        {format(new Date(time), 'MMM d, HH:mm')}
      </span>
    </div>
  );
}
