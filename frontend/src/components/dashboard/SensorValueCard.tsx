import { cn } from '@utils/cn';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface SensorValueCardProps {
  label: string;
  value: number | string | null;
  unit: string;
  quality?: 'GOOD' | 'SUSPECT' | 'BAD' | null;
  trend?: number | null; // percentage change
  freshness?: number; // seconds since last update
  icon?: React.ReactNode;
}

const qualityConfig = {
  GOOD: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/10', label: 'Good' },
  SUSPECT: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', label: 'Suspect' },
  BAD: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', label: 'Bad' },
  null: { icon: Minus, color: 'text-text-muted', bg: 'bg-text-muted/10', label: 'No Data' },
};

const freshnessConfig = (seconds: number) => {
  if (seconds < 10) return { color: 'text-success', label: 'Live' };
  if (seconds < 60) return { color: 'text-warning', label: `${seconds}s ago` };
  return { color: 'text-critical', label: `${Math.round(seconds / 60)}m ago` };
};

export function SensorValueCard({
  label,
  value,
  unit,
  quality = null,
  trend = null,
  freshness = 0,
  icon,
}: SensorValueCardProps) {
  const q = qualityConfig[quality];
  const f = freshnessConfig(freshness);

  const trendIcon = trend === null ? null :
    trend > 0 ? <TrendingUp className="w-4 h-4 text-success" /> :
    trend < 0 ? <TrendingDown className="w-4 h-4 text-critical" /> :
    <Minus className="w-4 h-4 text-text-muted" />;

  const trendText = trend === null ? null :
    trend > 0 ? `+${trend.toFixed(1)}%` :
    trend < 0 ? `${trend.toFixed(1)}%` : '—';

  return (
    <article className="card p-4 transition-all duration-200 hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          {icon && <span className="w-8 h-8 bg-info/10 rounded-lg flex items-center justify-center">{icon}</span>}
          <div>
            <p className="text-caption text-text-secondary font-medium">{label}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <span className={cn('status-dot', q.bg.replace('bg-', 'bg-'))} />
              <span className={cn('text-caption font-medium', q.color)}>{q.label}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-caption">
          <span className={cn('px-1.5 py-0.5 rounded', f.color.replace('text-', 'bg-').replace('text-', 'bg-') + '/10', f.color)}>
            {f.label}
          </span>
        </div>
      </div>

      <div className="flex items-baseline justify-between">
        <div className="flex items-baseline gap-1">
          <span className="text-data-xl font-bold text-text-primary tabular-nums">{value}</span>
          <span className="text-data text-text-secondary">{unit}</span>
        </div>
        <div className="flex items-center gap-1">
          {trendIcon && trendText && (
            <span className={cn('flex items-center gap-0.5 text-caption font-medium', trend > 0 ? 'text-success' : trend < 0 ? 'text-critical' : 'text-text-muted')}>
              {trendIcon}
              <span>{trendText}</span>
            </span>
          )}
        </div>
      </div>
    </article>
  );
}