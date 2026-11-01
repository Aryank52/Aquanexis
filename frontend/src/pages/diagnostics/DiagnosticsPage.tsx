import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Gauge, Waves, Mountain, Database, Zap, AlertTriangle, CheckCircle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';

export function DiagnosticsPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">System Diagnostics</h1>
          <p className="text-body-sm text-text-secondary mt-1">Pressure, flow, leak, tank, and pump energy diagnostics</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Pressure Panel */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Pressure</CardTitle>
            <Badge variant="success">Normal</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-text-secondary">Current</div>
                <div className="text-data font-bold text-text-primary">345 kPa</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">1h Trend</div>
                <div className="flex items-center gap-1 text-success">
                  <TrendingUp className="w-3 h-3" /> +5 kPa
                </div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">24h Trend</div>
                <div className="flex items-center gap-1 text-success">
                  <TrendingUp className="w-3 h-3" /> +12 kPa
                </div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Fouling Index</div>
                <div className="text-data font-bold text-success">0.12</div>
              </div>
            </div>
            <div className="h-32 flex items-center justify-center text-text-muted border border-dashed border-subtle rounded-button">
              Pressure Chart (24h)
            </div>
          </CardContent>
        </Card>

        {/* Flow Panel */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Flow</CardTitle>
            <Badge variant="success">Normal</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-text-secondary">Current</div>
                <div className="text-data font-bold text-text-primary">1.18 L/min</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Recovery</div>
                <div className="text-data font-bold text-info">83%</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Permeate</div>
                <div className="text-data font-bold text-text-primary">1.0 L/min</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Reject</div>
                <div className="text-data font-bold text-text-primary">0.18 L/min</div>
              </div>
            </div>
            <div className="h-32 flex items-center justify-center text-text-muted border border-dashed border-subtle rounded-button">
              Flow Chart (24h)
            </div>
          </CardContent>
        </Card>

        {/* Leak Panel */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Leak Detection</CardTitle>
            <Badge variant="success">Dry</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-text-secondary">Probability</div>
                <div className="text-data font-bold text-success">1%</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Sensor</div>
                <div className="flex items-center gap-1 text-success">
                  <CheckCircle className="w-4 h-4" /> OK
                </div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Flow Delta</div>
                <div className="text-data font-bold text-text-primary">0.02 L/min</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Pressure Drop</div>
                <div className="text-data font-bold text-text-primary">1.2 kPa</div>
              </div>
            </div>
            <div className="h-32 flex items-center justify-center text-text-muted border border-dashed border-subtle rounded-button">
              Leak Probability Chart (24h)
            </div>
          </CardContent>
        </Card>

        {/* Tank Panel */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Tank State</CardTitle>
            <Badge variant="success">Normal</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-text-secondary">Level</div>
                <div className="text-data font-bold text-text-primary">82%</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Fill Rate</div>
                <div className="text-data font-bold text-info">1.15 L/min</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Empty Rate</div>
                <div className="text-data font-bold text-text-primary">0.95 L/min</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Stagnation</div>
                <div className="text-data font-bold text-success">1.2 hrs</div>
              </div>
            </div>
            <div className="h-32 flex items-center justify-center text-text-muted border border-dashed border-subtle rounded-button">
              Tank Level Chart (24h)
            </div>
          </CardContent>
        </Card>

        {/* Pump Panel */}
        <Card>
          <CardHeader className="flex items-center justify-between">
            <CardTitle>Pump Energy</CardTitle>
            <Badge variant="success">Normal</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-caption text-text-secondary">Current</div>
                <div className="text-data font-bold text-text-primary">0.82 A</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Power</div>
                <div className="text-data font-bold text-text-primary">188 W</div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Efficiency (7d)</div>
                <div className="flex items-center gap-1 text-warning">
                  <TrendingDown className="w-3 h-3" /> -2.1%
                </div>
              </div>
              <div>
                <div className="text-caption text-text-secondary">Runtime</div>
                <div className="text-data font-bold text-text-primary">2,847 hrs</div>
              </div>
            </div>
            <div className="h-32 flex items-center justify-center text-text-muted border border-dashed border-subtle rounded-button">
              Pump Current Chart (7d)
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}