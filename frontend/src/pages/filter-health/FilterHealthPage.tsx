import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Filter, Gauge, TrendingUp, TrendingDown, Minus, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

export function FilterHealthPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Filter Intelligence</h1>
          <p className="text-body-sm text-text-secondary mt-1">Filter Stress Index, Health Index, and Remaining Useful Life</p>
        </div>
      </div>

      {/* FSI, FHI, RUL Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-caption text-text-secondary mb-2">Filter Stress Index</div>
              <div className="relative w-48 h-48 mx-auto mb-4">
                <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-90">
                  <circle cx="80" cy="80" r="70" fill="none" stroke="currentColor" strokeWidth="12" className="text-border" opacity="0.15" />
                  <circle cx="80" cy="80" r="70" fill="none" stroke="var(--gauge-good)" strokeWidth="12" strokeDasharray="439.8" strokeDashoffset="360" strokeLinecap="round" className="gauge-path" style={{ transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
                </svg>
              </div>
              <div className="text-data-xl font-bold text-success">18.5</div>
              <div className="text-caption text-text-secondary mt-1">LOW STRESS</div>
              <Badge variant="success" className="mt-2">Good</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-caption text-text-secondary mb-2">Filter Health Index</div>
              <div className="relative w-48 h-48 mx-auto mb-4">
                <svg viewBox="0 0 160 160" className="w-full h-full transform -rotate-90">
                  <circle cx="80" cy="80" r="70" fill="none" stroke="currentColor" strokeWidth="12" className="text-border" opacity="0.15" />
                  <circle cx="80" cy="80" r="70" fill="none" stroke="var(--gauge-good)" strokeWidth="12" strokeDasharray="439.8" strokeDashoffset="32" strokeLinecap="round" className="gauge-path" style={{ transform: 'rotate(-90deg)', transformOrigin: 'center' }} />
                </svg>
              </div>
              <div className="text-data-xl font-bold text-success">92.3</div>
              <div className="text-caption text-text-secondary mt-1">EXCELLENT HEALTH</div>
              <Badge variant="success" className="mt-2">Good</Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="text-center">
              <div className="text-caption text-text-secondary mb-2">Remaining Useful Life</div>
              <div className="text-data-xl font-bold text-text-primary mb-1">245</div>
              <div className="text-caption text-text-secondary">days</div>
              <div className="text-caption text-text-muted mt-1">[210 – 280] 95% CI</div>
              <div className="mt-4 p-3 bg-surface rounded-button border border-subtle">
                <div className="flex items-center justify-center gap-2 text-caption text-text-secondary">
                  <Filter className="w-4 h-4" />
                  <span>Model: baseline_v1 | MAE: 11 days</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Explanation Panel */}
      <Card>
        <CardHeader>
          <CardTitle>Prediction Explanation</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-3 bg-surface rounded-button border border-subtle">
              <div className="flex items-center justify-between mb-2">
                <span className="text-body-sm font-medium text-text-primary">Top Contributing Factors</span>
                <Badge variant="info">Coefficients</Badge>
              </div>
              <div className="space-y-2 text-caption">
                <div className="flex items-center gap-2">
                  <span className="w-24 text-text-secondary">Feed TDS</span>
                  <div className="flex-1 h-2 bg-success/20 rounded-full overflow-hidden">
                    <div className="h-full bg-success rounded-full" style={{ width: '35%' }} />
                  </div>
                  <span className="text-success font-medium w-10 text-right">+35%</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-24 text-text-secondary">Pressure</span>
                  <div className="flex-1 h-2 bg-warning/20 rounded-full overflow-hidden">
                    <div className="h-full bg-warning rounded-full" style={{ width: '12%' }} />
                  </div>
                  <span className="text-warning font-medium w-10 text-right">+12%</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-24 text-text-secondary">Runtime</span>
                  <div className="flex-1 h-2 bg-info/20 rounded-full overflow-hidden">
                    <div className="h-full bg-info rounded-full" style={{ width: '20%' }} />
                  </div>
                  <span className="text-info font-medium w-10 text-right">+20%</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="w-24 text-text-secondary">Cleanings</span>
                  <div className="flex-1 h-2 bg-text-muted/20 rounded-full overflow-hidden">
                    <div className="h-full bg-text-muted rounded-full" style={{ width: '8%' }} />
                  </div>
                  <span className="text-text-muted font-medium w-10 text-right">-8%</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* RUL History Chart */}
      <Card>
        <CardHeader>
          <CardTitle>RUL History (30 Days)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-64 flex items-center justify-center text-text-muted">
            RUL Chart Component - uPlot with confidence ribbon pending
          </div>
        </CardContent>
      </Card>
    </div>
  );
}