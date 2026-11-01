import { cn } from '@utils/cn';
import { X, AlertTriangle, XCircle, Info, CheckCircle } from 'lucide-react';
import { useState, useEffect } from 'react';

interface Alert {
  id: string;
  type: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  message: string;
  triggerValue?: number;
  thresholdValue?: number;
  createdAt: string;
  acknowledged: boolean;
}

interface ActiveAlertBannerProps {
  alert: Alert | null;
  onAcknowledge: (id: string) => void;
  onDismiss: () => void;
}

const severityConfig = {
  INFO: { icon: Info, bg: 'bg-info/10', border: 'border-info', text: 'text-info', label: 'INFO' },
  WARNING: { icon: AlertTriangle, bg: 'bg-warning/10', border: 'border-warning', text: 'text-warning', label: 'WARNING' },
  CRITICAL: { icon: XCircle, bg: 'bg-critical/10', border: 'border-critical', text: 'text-critical', label: 'CRITICAL' },
};

export function ActiveAlertBanner({ alert, onAcknowledge, onDismiss }: ActiveAlertBannerProps) {
  const [visible, setVisible] = useState(false);
  const [exiting, setExiting] = useState(false);

  if (!alert || !visible && !exiting) return null;

  const config = severityConfig[alert.severity];

  useEffect(() => {
    if (alert) {
      setExiting(false);
      setVisible(true);
    }
  }, [alert]);

  const handleDismiss = () => {
    setExiting(true);
    setTimeout(() => {
      setVisible(false);
      onDismiss();
    }, 300);
  };

  const handleAcknowledge = () => {
    onAcknowledge(alert.id);
    // Don't auto-dismiss on acknowledge, let user dismiss manually
  };

  return (
    <div
      className={cn(
        'fixed top-16 left-6 right-6 z-50 animate-slide-down',
        exiting && 'animate-fade-out',
        config.bg,
        config.border,
        'border-l-4 rounded-r-button shadow-elevated'
      )}
      role="alert"
      aria-live={alert.severity === 'CRITICAL' ? 'assertive' : 'polite'}
    >
      <div className="p-4">
        <div className="flex items-start gap-3">
          <config.icon className={cn('w-6 h-6 flex-shrink-0 mt-0.5', config.text)} aria-hidden="true" />
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className={cn('font-semibold text-body-sm', config.text)}>
                {config.label} ALERT
              </span>
              <span className="text-caption text-text-muted">{new Date(alert.createdAt).toLocaleTimeString()}</span>
            </div>
            <p className="text-body text-text-primary">{alert.message}</p>
            {(alert.triggerValue !== undefined || alert.thresholdValue !== undefined) && (
              <div className="mt-2 flex items-center gap-2 text-caption text-text-secondary">
                {alert.triggerValue !== undefined && (
                  <span>Trigger: <span className="font-mono text-text-primary">{alert.triggerValue}</span></span>
                )}
                {alert.thresholdValue !== undefined && (
                  <span>Threshold: <span className="font-mono text-text-primary">{alert.thresholdValue}</span></span>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 flex-shrink-0">
            {!alert.acknowledged && (
              <button
                onClick={handleAcknowledge}
                className={cn(
                  'btn btn-secondary btn-sm whitespace-nowrap',
                  alert.severity === 'CRITICAL' && 'btn-danger'
                )}
              >
                Acknowledge
              </button>
            )}
            <button
              onClick={handleDismiss}
              className="btn btn-ghost btn-sm p-2"
              aria-label="Dismiss alert"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}