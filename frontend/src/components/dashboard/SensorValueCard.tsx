import { cn } from '@utils/cn';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

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
  GOOD: { color: 'text-success', bg: 'bg-success/10', label: 'Good' },
  SUSPECT: { color: 'text-warning', bg: 'bg-warning/10', label: 'Suspect' },
  BAD: { color: 'text-critical', bg: 'bg-critical/10', label: 'Bad' },
  UNKNOWN: { color: 'text-text-muted', bg: 'bg-text-muted/10', label: 'No Data' },
};

const qualityIcons = {
  GOOD: CheckCircle,
  SUSPECT: AlertTriangle,
  BAD: XCircle,
  UNKNOWN: Minus,
};

const freshnessConfig = (seconds: number) => {
  if (seconds < 10) return { color: 'text-success', label: 'Live', isStale: false };
  if (seconds < 60) return { color: 'text-warning', label: `${seconds}s ago`, isStale: false };
  if (seconds < 300) return { color: 'text-critical', label: `${Math.round(seconds / 60)}m ago`, isStale: true };
  return { color: 'text-critical', label: `${Math.round(seconds / 60)}m ago (stale)`, isStale: true };
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
  const qKey = (quality ?? 'UNKNOWN') as keyof typeof qualityConfig;
  const q = qualityConfig[qKey];
  const QualityIcon = qualityIcons[qKey];
  const f = freshnessConfig(freshness);

  const trendIcon = trend === null ? null :
    trend > 0 ? <TrendingUp className="w-4 h-4 text-success" /> :
    trend < 0 ? <TrendingDown className="w-4 h-4 text-critical" /> :
    <Minus className="w-4 h-4 text-text-muted" />;

  const trendText = trend === null ? null :
    trend > 0 ? `+${trend.toFixed(1)}%` :
    trend < 0 ? `${trend.toFixed(1)}%` : '—';

  return (
    <article className={cn("card p-4 transition-all duration-200 hover:shadow-card-hover", f.isStale && "opacity-75 border-warning/30")}>
      <div className="flex items-start justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          {icon && <span className="w-8 h-8 bg-info/10 rounded-lg flex items-center justify-center">{icon}</span>}
          <div>
            <p className="text-caption text-text-secondary font-medium">{label}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <QualityIcon className={cn('w-4 h-4', q.color)} />
              <span className={cn('text-caption font-medium', q.color)}>{q.label}</span>
              {f.isStale && (
                <span className="flex items-center gap-0.5 text-xs text-warning">
                  <AlertCircle className="w-3 h-3" />
                  Stale
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5 text-caption">
          <span className={cn('px-1.5 py-0.5 rounded flex items-center gap-0.5', f.color.replace('text-', 'bg-').replace('text-', 'bg-') + '/10', f.color)}>
            {f.isStale && <Clock className="w-3 h-3" />}
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
          {trendIcon && trendText && trend !== null && (
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