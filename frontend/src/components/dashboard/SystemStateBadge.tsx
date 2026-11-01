import { cn } from '@utils/cn';
import { CheckCircle, AlertTriangle, XCircle, Pulse } from 'lucide-react';

type SystemState = 'healthy' | 'degraded' | 'critical';

interface SystemStateBadgeProps {
  state: SystemState;
  pulse?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

const stateConfig = {
  healthy: { icon: CheckCircle, bg: 'bg-success/10', text: 'text-success', label: 'SYSTEM HEALTHY' },
  degraded: { icon: AlertTriangle, bg: 'bg-warning/10', text: 'text-warning', label: 'DEGRADED' },
  critical: { icon: XCircle, bg: 'bg-critical/10', text: 'text-critical', label: 'CRITICAL' },
};

const sizeStyles = {
  sm: 'px-2 py-1 gap-1.5',
  md: 'px-3 py-1.5 gap-2',
  lg: 'px-4 py-2 gap-2.5',
};

const iconSizes = {
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
};

const textSizes = {
  sm: 'text-caption',
  md: 'text-body-sm',
  lg: 'text-body',
};

export function SystemStateBadge({ state, pulse = false, size = 'md' }: SystemStateBadgeProps) {
  const config = stateConfig[state];

  return (
    <span className={cn(
      'inline-flex items-center font-medium rounded-button border transition-all duration-200',
      config.bg,
      config.text,
      sizeStyles[size],
      pulse && 'animate-pulse-critical'
    )}>
      <config.icon className={cn(iconSizes[size], 'flex-shrink-0')} aria-hidden="true" />
      <span className={cn(textSizes[size], 'whitespace-nowrap')}>{config.label}</span>
      {pulse && state === 'critical' && (
        <Pulse className={cn(iconSizes[size], 'text-critical/50 animate-pulse')} aria-hidden="true" />
      )}
    </span>
  );
}