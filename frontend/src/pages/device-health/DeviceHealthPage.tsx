import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Wifi, Cpu, HardDrive, RefreshCw, AlertTriangle, CheckCircle, XCircle, HelpCircle, Settings, Download, Upload } from 'lucide-react';

const sensors = [
  { name: 'TDS', value: '45.2 ppm', quality: 'GOOD', lastCal: '2026-10-15', icon: 'Droplet' },
  { name: 'pH', value: '7.1', quality: 'SUSPECT', lastCal: '2026-09-20', icon: 'Filter' },
  { name: 'Turbidity', value: '0.3 NTU', quality: 'GOOD', lastCal: '2026-10-10', icon: 'Waves' },
  { name: 'Temperature', value: '23.5°C', quality: 'GOOD', lastCal: 'Factory', icon: 'Thermometer' },
  { name: 'Flow', value: '1.2 L/min', quality: 'GOOD', lastCal: '2026-10-01', icon: 'Gauge' },
  { name: 'Pressure', value: '350 kPa', quality: 'GOOD', lastCal: '2026-10-01', icon: 'Mountain' },
  { name: 'Tank Level', value: '78%', quality: 'GOOD', lastCal: '2026-10-01', icon: 'Database' },
  { name: 'Leak', value: 'Dry', quality: 'GOOD', lastCal: 'N/A', icon: 'AlertTriangle' },
  { name: 'Pump Current', value: '0.85 A', quality: 'GOOD', lastCal: '2026-10-01', icon: 'Zap' },
];

const qualityConfig = {
  GOOD: { icon: CheckCircle, color: 'text-success', bg: 'bg-success/10', label: 'Good' },
  SUSPECT: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/10', label: 'Suspect' },
  BAD: { icon: XCircle, color: 'text-critical', bg: 'bg-critical/10', label: 'Bad' },
};

export function DeviceHealthPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Device Health</h1>
          <p className="text-body-sm text-text-secondary mt-1">Sensor status, firmware, and connectivity</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="secondary" iconLeft={<Download className="w-4 h-4" />}>
            Export Diagnostics
          </Button>
          <Button variant="ghost" iconLeft={<Settings className="w-4 h-4" />}>
            Configure
          </Button>
        </div>
      </div>

      {/* Sensor Health Grid */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Sensor Health</CardTitle>
            <div className="flex items-center gap-2 text-caption text-success">
              <CheckCircle className="w-4 h-4" />
              <span>8/9 Healthy</span>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sensor</th>
                  <th>Current Value</th>
                  <th>Quality</th>
                  <th>Last Calibration</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {sensors.map((sensor, index) => {
                  const q = qualityConfig[sensor.quality];
                  const Icon = q.icon;
                  const isDue = sensor.lastCal !== 'Factory' && sensor.lastCal !== 'N/A' && 
                    new Date(sensor.lastCal) < new Date(Date.now() - 90 * 24 * 60 * 60 * 1000);
                  
                  return (
                    <tr key={index}>
                      <td className="flex items-center gap-2">
                        <span className="w-8 h-8 bg-info/10 rounded-lg flex items-center justify-center">
                          {sensor.icon === 'Droplet' && <span className="text-info">💧</span>}
                          {sensor.icon === 'Filter' && <span>🔬</span>}
                          {sensor.icon === 'Waves' && <span>🌊</span>}
                          {sensor.icon === 'Thermometer' && <span>🌡️</span>}
                          {sensor.icon === 'Gauge' && <span>📊</span>}
                          {sensor.icon === 'Mountain' && <span>⛰️</span>}
                          {sensor.icon === 'Database' && <span>🗄️</span>}
                          {sensor.icon === 'AlertTriangle' && <span>⚠️</span>}
                          {sensor.icon === 'Zap' && <span>⚡</span>}
                        </span>
                        <span className="font-medium text-text-primary">{sensor.name}</span>
                      </td>
                      <td className="font-mono text-data text-text-primary">{sensor.value}</td>
                      <td>
                        <Badge variant={sensor.quality.toLowerCase() as any}>
                          <Icon className="w-3 h-3 mr-1" />
                          {q.label}
                        </Badge>
                      </td>
                      <td className="text-body-sm text-text-secondary">
                        {sensor.lastCal}
                        {isDue && <span className="ml-2 text-warning">⚠ Due</span>}
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-success" />
                          <span className="text-caption text-success">Online</span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-1">
                          {isDue && (
                            <Button variant="secondary" size="sm" className="h-8 px-2">
                              Calibrate
                            </Button>
                          )}
                          <Button variant="ghost" size="sm" className="h-8 p-2">
                            <HelpCircle className="w-4 h-4" />
                          </Button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Firmware & Connectivity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Firmware</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium text-text-primary">Current Version</div>
                <div className="text-body-sm text-text-secondary">2.1.4</div>
              </div>
              <div className="text-right">
                <div className="font-medium text-text-primary">Latest Available</div>
                <div className="text-body-sm text-warning">2.1.5</div>
              </div>
            </div>
            <div className="p-3 bg-warning/5 rounded-button border border-warning/20">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-warning" />
                  <div>
                    <p className="font-medium text-text-primary">Firmware Update Available</p>
                    <p className="text-caption text-text-secondary">Version 2.1.5 includes sensor calibration improvements and security patches</p>
                  </div>
                </div>
                <Button variant="secondary" size="sm">Update Now</Button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4 text-center">
              <div className="p-3 bg-surface rounded-button border border-subtle">
                <div className="text-data font-bold text-text-primary">14d 6h</div>
                <div className="text-caption text-text-secondary">Uptime</div>
              </div>
              <div className="p-3 bg-surface rounded-button border border-subtle">
                <div className="text-data font-bold text-text-primary">99.9%</div>
                <div className="text-caption text-text-secondary">Availability (30d)</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Connectivity</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-success/5 rounded-button border border-success/20">
              <div className="flex items-center gap-3">
                <Wifi className="w-6 h-6 text-success" />
                <div>
                  <p className="font-medium text-text-primary">WiFi Connected</p>
                  <p className="text-caption text-text-secondary">-42 dBm • Excellent</p>
                </div>
              </div>
              <Badge variant="success">Online</Badge>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-surface rounded-button border border-subtle">
                <div className="text-caption text-text-secondary">Last Ping</div>
                <div className="text-data font-bold text-text-primary">3s ago</div>
              </div>
              <div className="p-3 bg-surface rounded-button border border-subtle">
                <div className="text-caption text-text-secondary">IP Address</div>
                <div className="text-body-sm font-mono text-text-primary">192.168.1.142</div>
              </div>
            </div>
            <div className="p-3 bg-surface rounded-button border border-subtle">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-text-primary">MQTT Connection</p>
                  <p className="text-caption text-text-secondary">Connected to broker.aquanexis.local:8883</p>
                </div>
                <Badge variant="success">Connected</Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}