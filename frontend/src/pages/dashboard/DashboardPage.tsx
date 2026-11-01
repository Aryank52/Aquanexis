import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Droplet, Filter, Gauge, Waves, Mountain, Database, Zap, AlertTriangle, X, TrendingUp, TrendingDown, Minus, CheckCircle, AlertCircle, XCircle, MinusCircle, ExternalLink } from 'lucide-react';
import { AquaScoreGauge, MiniGauge } from '@components/charts/AquaScoreGauge';
import { SystemStateBadge } from '@components/dashboard/SystemStateBadge';
import { ActiveAlertBanner } from '@components/dashboard/ActiveAlertBanner';
import { SensorValueCard } from '@components/dashboard/SensorValueCard';
import { Card, CardContent } from '@components/ui/Card';
import { Button } from '@components/ui/Button';
import { Badge } from '@components/ui/Badge';
import { cn } from '@utils/cn';
import { Sparkline } from '@components/charts/Sparkline';

// Mock data for development
const mockDashboardData = {
  device: {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'Kitchen RO System',
    status: 'online' as const,
    lastSeen: new Date().toISOString(),
  },
  latestTelemetry: {
    timestamp: new Date().toISOString(),
    readings: {
      tds: 42.5,
      ec: 68.2,
      ph: 7.1,
      turbidity: 0.25,
      temperature: 23.4,
      flow: 1.18,
      pressure: 345,
      tankLevel: 82,
      leakDetected: false,
      pumpCurrent: 0.82,
    },
    quality: {
      overall: 'GOOD',
      flags: {
        tds: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        ph: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        turbidity: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        temperature: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        flow: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        pressure: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        tankLevel: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        leakDetected: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
        pumpCurrent: { range: 'OK', rate: 'OK', cross_sensor: 'OK' },
      },
    },
  },
  waterQuality: {
    aquascore: 94,
    parameterScores: [
      { parameter: 'TDS', score: 96 },
      { parameter: 'pH', score: 98 },
      { parameter: 'Turbidity', score: 99 },
      { parameter: 'Temperature', score: 92 },
    ],
    trends: {
      '1h': { direction: 'improving', magnitude: 1.2 },
      '24h': { direction: 'stable', magnitude: 0.3 },
      '7d': { direction: 'improving', magnitude: 4.5 },
    },
  },
  filterHealth: {
    fsi: 18.5,
    fhi: 92.3,
    rulDays: 245,
    rulConfidence: { lower: 210, upper: 280 },
  },
  diagnostics: {
    pressure: { status: 'normal', current: 345 },
    flow: { status: 'normal', current: 1.18 },
    leak: { status: 'dry', probability: 0.01 },
    tank: { status: 'normal', level: 82 },
    pump: { status: 'normal', current: 0.82 },
  },
  activeAlert: null,
  dataFreshness: 3,
};

const sensorConfigs = [
  { key: 'tds', label: 'TDS', unit: 'ppm', icon: Droplet, trend: -1.2 },
  { key: 'ec', label: 'EC', unit: 'µS/cm', icon: Zap, trend: -0.8 },
  { key: 'ph', label: 'pH', unit: '', icon: Filter, trend: 0.1 },
  { key: 'turbidity', label: 'Turbidity', unit: 'NTU', icon: Waves, trend: -0.5 },
  { key: 'temperature', label: 'Temp', unit: '°C', icon: Mountain, trend: 0.3 },
  { key: 'flow', label: 'Flow', unit: 'L/min', icon: Gauge, trend: -0.2 },
  { key: 'pressure', label: 'Pressure', unit: 'kPa', icon: Mountain, trend: 0.5 },
  { key: 'tankLevel', label: 'Tank', unit: '%', icon: Database, trend: null },
  { key: 'leakDetected', label: 'Leak', unit: '', icon: AlertTriangle, trend: null },
  { key: 'pumpCurrent', label: 'Pump I', unit: 'A', icon: Zap, trend: -0.1 },
];

export function DashboardPage() {
  const [activeAlert, setActiveAlert] = useState<Alert | null>(null);

  const handleAcknowledge = (id: string) => {
    if (activeAlert?.id === id) {
      setActiveAlert(prev => prev ? { ...prev, acknowledged: true } : null);
    }
  };

  const handleDismiss = () => {
    setActiveAlert(null);
  };

  // Simulate alert for demo
  const demoAlert: Alert = {
    id: 'alert-1',
    type: 'filter_health_critical',
    severity: 'WARNING',
    message: 'Filter Health Index dropped below 40. Replacement recommended within 7 days.',
    triggerValue: 38,
    thresholdValue: 40,
    createdAt: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
    acknowledged: false,
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Dashboard</h1>
          <p className="text-body-sm text-text-secondary mt-1">
            Real-time monitoring for {mockDashboardData.device.name}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className={cn(
            'px-2 py-1 rounded-button text-caption font-medium',
            mockDashboardData.device.status === 'online' 
              ? 'bg-success/10 text-success' 
              : 'bg-text-muted/10 text-text-muted'
          )}>
            {mockDashboardData.device.status === 'online' ? '● Online' : '● Offline'}
          </span>
          <Button variant="ghost" size="sm" iconRight={<ExternalLink className="w-4 h-4" />} asChild>
            <Link to="/water-quality">Water Quality</Link>
          </Button>
          <Button variant="ghost" size="sm" iconRight={<ExternalLink className="w-4 h-4" />} asChild>
            <Link to="/filter-health">Filter Health</Link>
          </Button>
        </div>
      </div>

      {/* Active Alert Banner */}
      <ActiveAlertBanner
        alert={activeAlert}
        onAcknowledge={handleAcknowledge}
        onDismiss={handleDismiss}
      />

      {/* Top Row: AquaScore + Filter Health + System State + Key Trend */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* AquaScore Gauge */}
        <div className="lg:col-span-5 xl:col-span-4">
          <Card className="h-full">
            <CardContent className="flex flex-col items-center justify-center h-full p-6">
              <AquaScoreGauge
                value={mockDashboardData.waterQuality.aquascore}
                size={240}
                strokeWidth={18}
                label="AquaScore"
                animate={true}
              />
              <div className="mt-4 flex items-center justify-center gap-6 text-caption">
                <span className="flex items-center gap-1 text-success">
                  <CheckCircle className="w-3 h-3" />
                  4/4 Parameters Good
                </span>
                <span className="flex items-center gap-1 text-text-secondary">
                  <TrendingUp className="w-3 h-3" />
                  +2.1% vs 24h ago
                </span>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filter Health Card */}
        <div className="lg:col-span-7 xl:col-span-4">
          <Card className="h-full">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Filter Health</CardTitle>
                <Badge variant="success">GOOD</Badge>
              </div>
              <CardSubtitle>Last updated {mockDashboardData.dataFreshness}s ago</CardSubtitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="grid grid-cols-3 gap-0 p-4">
                <div className="border-r border-subtle flex flex-col items-center p-4">
                  <MiniGauge value={mockDashboardData.filterHealth.fsi} size={70} strokeWidth={6} />
                  <p className="text-caption text-text-secondary mt-2">FSI</p>
                  <p className="text-body-sm font-medium text-text-primary">Stress Index</p>
                </div>
                <div className="border-r border-subtle flex flex-col items-center p-4">
                  <MiniGauge value={mockDashboardData.filterHealth.fhi} size={70} strokeWidth={6} />
                  <p className="text-caption text-text-secondary mt-2">FHI</p>
                  <p className="text-body-sm font-medium text-text-primary">Health Index</p>
                </div>
                <div className="flex flex-col items-center p-4">
                  <div className="text-data-lg font-bold text-text-primary mb-1">{mockDashboardData.filterHealth.rulDays}</div>
                  <p className="text-caption text-text-secondary">days RUL</p>
                  <p className="text-caption text-text-muted">[{mockDashboardData.filterHealth.rulConfidence.lower}–{mockDashboardData.filterHealth.rulConfidence.upper}]</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* System State + Key Trend */}
        <div className="lg:col-span-12 xl:col-span-4 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>System State</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <SystemStateBadge state="healthy" size="lg" />
                <div className="grid grid-cols-2 gap-3 text-center">
                  <div className="p-3 bg-surface rounded-button border border-subtle">
                    <div className="text-data font-bold text-text-primary">99.9%</div>
                    <div className="text-caption text-text-secondary">Uptime (30d)</div>
                  </div>
                  <div className="p-3 bg-surface rounded-button border border-subtle">
                    <div className="text-data font-bold text-text-primary">0</div>
                    <div className="text-caption text-text-secondary">Safety Events (30d)</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Key Trend (24h)</CardTitle>
            </CardHeader>
            <CardContent>
              <Sparkline
                data={generateTrendData()}
                color="var(--chart-1)"
                height={80}
                showArea
              />
              <div className="mt-3 flex items-center justify-between text-caption">
                <span className="text-text-secondary">AquaScore</span>
                <span className="flex items-center gap-1 text-success">
                  <TrendingUp className="w-3 h-3" />
                  +2.1%
                </span>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Sensor Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-h2 font-semibold text-text-primary">Current Sensor Values</h2>
          <div className="flex items-center gap-2 text-caption text-text-secondary">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-success" />
              Live
            </span>
            <span className="text-text-muted">Updated {mockDashboardData.dataFreshness}s ago</span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
          {sensorConfigs.map((config) => {
            const reading = mockDashboardData.latestTelemetry.readings[config.key as keyof typeof mockDashboardData.latestTelemetry.readings];
            const quality = mockDashboardData.latestTelemetry.quality.flags[config.key as keyof typeof mockDashboardData.latestTelemetry.quality.flags]?.range as 'GOOD' | 'SUSPECT' | 'BAD' | undefined;
            
            let displayValue: number | string | null = reading ?? null;
            let displayUnit = config.unit;
            
            if (config.key === 'leakDetected') {
              displayValue = reading ? 'Detected' : 'Dry';
              displayUnit = '';
            }

            return (
              <SensorValueCard
                key={config.key}
                label={config.label}
                value={displayValue}
                unit={displayUnit}
                quality={quality || 'GOOD'}
                trend={config.trend}
                freshness={mockDashboardData.dataFreshness}
                icon={<config.icon className="w-4 h-4 text-info" />}
              />
            );
          })}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="pt-4 border-t border-subtle">
        <h2 className="text-h2 font-semibold text-text-primary mb-4">Quick Actions</h2>
        <div className="flex flex-wrap gap-3">
          <Button variant="secondary" iconLeft={<Filter className="w-4 h-4" />} asChild>
            <Link to="/maintenance">Replace Filter</Link>
          </Button>
          <Button variant="ghost" iconLeft={<Gauge className="w-4 h-4" />} asChild>
            <Link to="/water-quality">View Water Quality</Link>
          </Button>
          <Button variant="ghost" iconLeft={<Waves className="w-4 h-4" />} asChild>
            <Link to="/diagnostics">View Diagnostics</Link>
          </Button>
          <Button variant="ghost" iconLeft={<AlertTriangle className="w-4 h-4" />} asChild>
            <Link to="/alerts">View Alerts</Link>
          </Button>
        </div>
      </div>

      {/* Demo alert trigger */}
      <div className="pt-4 border-t border-subtle">
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={() => setActiveAlert(demoAlert)}
          className="text-text-muted hover:text-warning"
        >
          Demo: Trigger Warning Alert
        </Button>
      </div>
    </div>
  );
}

// Helper types and functions
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

function generateTrendData() {
  const now = Date.now();
  const data = [];
  for (let i = 23; i >= 0; i--) {
    const base = 90;
    const variation = Math.sin(i * 0.3) * 3 + (Math.random() - 0.5) * 2;
    data.push({
      t: new Date(now - i * 3600 * 1000).toISOString(),
      y: Math.max(70, Math.min(100, base + variation + i * 0.1)),
    });
  }
  return data;
}