import { useEffect, useRef, useState } from 'react';
import { X, Clock, CheckCircle2, AlertTriangle, XCircle, Info, BellOff, Check } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAcknowledgeAlert, useResolveAlert, useSnoozeAlert } from '@/hooks/useAlerts';
import type { Alert, AlertSeverity } from '@/types/api';
import { formatDistanceToNow, format } from 'date-fns';

const SNOOZE_OPTIONS = [
  { label: '15 minutes', value: 15 },
  { label: '30 minutes', value: 30 },
  { label: '1 hour', value: 60 },
  { label: '4 hours', value: 240 },
  { label: '24 hours', value: 1440 },
];

const severityStyles: Record<AlertSeverity, { icon: typeof AlertTriangle; color: string; bg: string; border: string }> = {
  CRITICAL: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', border: 'border-critical/30' },
  WARNING: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', border: 'border-warning/30' },
  INFO: { icon: Info, color: 'text-info', bg: 'bg-info/10', border: 'border-info/30' },
};

interface Props {
  alert: Alert | null;
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
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
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
    resolve.mutate({ alertId: alert.id, data: { resolved_by: currentUser, resolved_reason: resolveReason } }, {
      onSuccess: onClose,
    });
  };

  const handleSnooze = (minutes: number) => {
    snooze.mutate({ alertId: alert.id, data: { snoozed_by: currentUser, snooze_duration_minutes: minutes } }, {
      onSuccess: () => { setShowSnooze(false); onClose(); },
    });
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
          'flex flex-col transition-transform duration-300 ease-out outline-none',
          open ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <div className={cn('flex items-start gap-3 p-5 border-b border-subtle', sev.bg)}>
          <SevIcon className={cn('w-5 h-5 flex-shrink-0 mt-0.5', sev.color)} />
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span id="drawer-title" className={cn('text-caption font-semibold uppercase tracking-wide', sev.color)}>
                {alert.severity}
              </span>
              <span className="text-caption text-text-muted">
                {alert.alert_type.replace(/_/g, ' ')}
              </span>
            </div>
            <p className="text-body-sm text-text-primary mt-1">{alert.explanation?.message || 'No message available.'}</p>
            <p className="text-caption text-text-muted mt-1">
              {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
            </p>
          </div>
          <button onClick={onClose} className="p-1.5 rounded-button hover:bg-hover text-text-muted" aria-label="Close">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-5">
          {/* Evidence */}
          {alert.explanation?.evidence && alert.explanation.evidence.length > 0 && (
            <section aria-label="Alert evidence">
              <h2 className="text-body-sm font-semibold text-text-primary mb-3">Evidence</h2>
              <div className="space-y-2">
                {alert.explanation.evidence.map((ev, i) => (
                  <div key={i} className="flex items-center justify-between p-3 bg-surface rounded-button border border-subtle">
                    <span className="text-caption text-text-secondary">{ev.label}</span>
                    <span className={cn(
                      'text-caption font-mono font-medium',
                      ev.severity === 'CRITICAL' ? 'text-critical' :
                      ev.severity === 'WARNING' ? 'text-warning' : 'text-text-primary'
                    )}>
                      {ev.value}{ev.unit ? ` ${ev.unit}` : ''}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* Trigger values */}
          {(alert.trigger_value !== null || alert.threshold_value !== null) && (
            <section className="grid grid-cols-2 gap-3">
              {alert.trigger_value !== null && (
                <div className="p-3 bg-surface border border-subtle rounded-button">
                  <p className="text-caption text-text-muted">Trigger Value</p>
                  <p className="text-data font-mono font-semibold text-text-primary">{alert.trigger_value}</p>
                </div>
              )}
              {alert.threshold_value !== null && (
                <div className="p-3 bg-surface border border-subtle rounded-button">
                  <p className="text-caption text-text-muted">Threshold</p>
                  <p className="text-data font-mono font-semibold text-text-primary">{alert.threshold_value}</p>
                </div>
              )}
            </section>
          )}

          {/* Recommended action */}
          {alert.explanation?.recommended_action && (
            <section className="p-3 bg-info/5 border border-info/20 rounded-button">
              <p className="text-caption font-semibold text-info mb-1">Recommended Action</p>
              <p className="text-body-sm text-text-primary">{alert.explanation.recommended_action}</p>
            </section>
          )}

          {/* Timeline */}
          <section aria-label="Alert timeline">
            <h2 className="text-body-sm font-semibold text-text-primary mb-3">Timeline</h2>
            <div className="space-y-2">
              <TimelineItem icon={Clock} label="Created" time={alert.created_at} color="text-text-muted" />
              {alert.acknowledged_at && (
                <TimelineItem icon={CheckCircle2} label={`Acknowledged by ${alert.acknowledged_by || 'user'}`} time={alert.acknowledged_at} color="text-warning" />
              )}
              {alert.resolved_at && (
                <TimelineItem icon={CheckCircle2} label={`Resolved by ${alert.resolved_by || 'user'}`} time={alert.resolved_at} color="text-success" />
              )}
              {alert.snoozed_until && (
                <TimelineItem icon={BellOff} label="Snoozed until" time={alert.snoozed_until} color="text-info" />
              )}
            </div>
          </section>

          {/* Snooze picker */}
          {showSnooze && (
            <section className="p-4 bg-surface border border-subtle rounded-card space-y-3">
              <h3 className="text-body-sm font-semibold text-text-primary">Snooze Duration</h3>
              <div className="grid grid-cols-2 gap-2">
                {SNOOZE_OPTIONS.map((opt) => (
                  <button key={opt.value}
                    className="btn btn-secondary btn-sm text-center"
                    onClick={() => handleSnooze(opt.value)}
                    disabled={snooze.isPending}>
                    {opt.label}
                  </button>
                ))}
              </div>
              <button className="btn btn-ghost btn-sm w-full" onClick={() => setShowSnooze(false)}>Cancel</button>
            </section>
          )}

          {/* Resolve form */}
          {showResolveForm && (
            <section className="p-4 bg-surface border border-subtle rounded-card space-y-3">
              <h3 className="text-body-sm font-semibold text-text-primary">Resolve Alert</h3>
              <div>
                <label className="label" htmlFor="resolve-reason">Resolution reason</label>
                <textarea
                  id="resolve-reason"
                  className="input resize-none"
                  rows={2}
                  placeholder="e.g. Leak fixed, valve reopened"
                  value={resolveReason}
                  onChange={(e) => setResolveReason(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <button className="btn btn-primary btn-sm flex-1"
                  onClick={handleResolve}
                  disabled={!resolveReason.trim() || resolve.isPending}>
                  {resolve.isPending ? 'Resolving…' : 'Confirm Resolve'}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => setShowResolveForm(false)}>Cancel</button>
              </div>
            </section>
          )}
        </div>

        {/* Actions */}
        {alert.state !== 'RESOLVED' && !showResolveForm && !showSnooze && (
          <div className="p-5 border-t border-subtle flex flex-wrap gap-2">
            {alert.state === 'ACTIVE' && (
              <button className="btn btn-secondary btn-sm flex-1"
                onClick={handleAcknowledge}
                disabled={acknowledge.isPending}>
                <Check className="w-4 h-4" />
                {acknowledge.isPending ? 'Acknowledging…' : 'Acknowledge'}
              </button>
            )}
            {(alert.state === 'ACTIVE' || alert.state === 'ACKNOWLEDGED') && (
              <>
                <button className="btn btn-primary btn-sm flex-1"
                  onClick={() => setShowResolveForm(true)}>
                  Resolve
                </button>
                <button className="btn btn-ghost btn-sm"
                  onClick={() => setShowSnooze(true)}
                  aria-label="Snooze alert">
                  <BellOff className="w-4 h-4" />
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function TimelineItem({ icon: Icon, label, time, color }: {
  icon: typeof Clock; label: string; time: string; color: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <Icon className={cn('w-4 h-4 flex-shrink-0', color)} />
      <div className="flex-1 min-w-0">
        <span className="text-caption text-text-secondary">{label}</span>
      </div>
      <span className="text-caption text-text-muted font-mono">
        {format(new Date(time), 'MMM d, HH:mm')}
      </span>
    </div>
  );
}
