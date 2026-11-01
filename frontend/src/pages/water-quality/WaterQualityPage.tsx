import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Droplet, Filter, Gauge, Waves, Mountain, Database, Zap, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';

export function WaterQualityPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Water Quality</h1>
          <p className="text-body-sm text-text-secondary mt-1">Parameter scores, trends, and anomaly detection</p>
        </div>
      </div>

      {/* Parameter Scores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'TDS', score: 96, value: '42.5 ppm', unit: 'ppm', icon: Droplet, trend: -1.2 },
          { label: 'pH', score: 98, value: '7.1', unit: '', icon: Filter, trend: 0.1 },
          { label: 'Turbidity', score: 99, value: '0.25 NTU', unit: 'NTU', icon: Waves, trend: -0.5 },
          { label: 'Temperature', score: 92, value: '23.4°C', unit: '°C', icon: Mountain, trend: 0.3 },
        ].map((param) => (
          <Card key={param.label}>
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <param.icon className="w-5 h-5 text-info" />
                  <span className="text-body-sm font-medium text-text-secondary">{param.label}</span>
                </div>
                <Badge variant="success">{param.score}/100</Badge>
              </div>
              <div className="flex items-baseline justify-between">
                <div className="flex items-baseline gap-1">
                  <span className="text-data-xl font-bold text-text-primary">{param.value}</span>
                </div>
                <span className={cn('text-caption font-medium', param.trend! > 0 ? 'text-success' : param.trend! < 0 ? 'text-critical' : 'text-text-muted')}>
                  {param.trend! > 0 ? '▲' : param.trend! < 0 ? '▼' : '●'} {param.trend! > 0 ? '+' : ''}{param.trend!.toFixed(1)}%
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Trend Chart Placeholder */}
      <Card>
        <CardHeader>
          <CardTitle>Trend Analysis (24h)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-text-muted">
            Trend Chart Component - uPlot integration pending
          </div>
        </CardContent>
      </Card>

      {/* Anomaly Timeline */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Anomalies</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 p-3 bg-warning/5 rounded-button border border-warning/20">
              <AlertTriangle className="w-5 h-5 text-warning" />
              <div>
                <p className="text-body-sm font-medium text-text-primary">TDS Spike Detected</p>
                <p className="text-caption text-text-secondary">z-score 3.2 at 10:15 AM — Returned to normal within 15 min</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 bg-info/5 rounded-button border border-info/20">
              <TrendingUp className="w-5 h-5 text-info" />
              <div>
                <p className="text-body-sm font-medium text-text-primary">pH Drift</p>
                <p className="text-caption text-text-secondary">Rate of change 0.15/hr at 10:30 PM — Auto-resolved</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}