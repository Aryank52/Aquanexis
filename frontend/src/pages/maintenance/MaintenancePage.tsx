import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Button } from '@components/ui/Button';
import { Badge } from '@components/ui/Badge';
import { Filter, Gauge, RotateCcw, Plus, CheckCircle, Clock, AlertTriangle } from 'lucide-react';

const mockHistory = [
  { date: '2026-10-28', type: 'FILTER_REPLACEMENT', by: 'J. Smith', verified: true, pre: { fhi: 38, rul: 5 }, post: { fhi: 95, rul: 245 } },
  { date: '2026-10-15', type: 'CALIBRATION', by: 'M. Chen', verified: true, sensor: 'pH', pre: { ph: 7.8 }, post: { ph: 7.1 } },
  { date: '2026-10-01', type: 'VERIFICATION', by: 'System', verified: true, passed: true },
  { date: '2026-09-20', type: 'CALIBRATION', by: 'J. Smith', verified: true, sensor: 'TDS', pre: { tds: 52 }, post: { tds: 45 } },
  { date: '2026-09-01', type: 'FILTER_REPLACEMENT', by: 'A. Brown', verified: true, pre: { fhi: 22, rul: 2 }, post: { fhi: 98, rul: 365 } },
];

export function MaintenancePage() {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-h1 font-semibold text-text-primary">Maintenance</h1>
          <p className="text-body-sm text-text-secondary mt-1">Filter replacement, calibration, and verification workflows</p>
        </div>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <Button variant="primary" iconLeft={<Filter className="w-4 h-4" />}>
              Replace Filter
            </Button>
            <Button variant="secondary" iconLeft={<Gauge className="w-4 h-4" />}>
              Calibrate Sensor
            </Button>
            <Button variant="secondary" iconLeft={<RotateCcw className="w-4 h-4" />}>
              Verify System
            </Button>
            <Button variant="ghost" iconLeft={<Plus className="w-4 h-4" />}>
              Custom Maintenance
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upcoming Maintenance */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Upcoming Maintenance</CardTitle>
            <Badge variant="warning">2 Due</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-warning/5 rounded-button border border-warning/20">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-warning" />
                <div>
                  <p className="font-medium text-text-primary">pH Sensor Calibration</p>
                  <p className="text-caption text-text-secondary">Overdue by 3 days • Last: 2026-09-20</p>
                </div>
              </div>
              <Button variant="secondary" size="sm">Calibrate Now</Button>
            </div>
            <div className="flex items-center justify-between p-3 bg-info/5 rounded-button border border-info/20">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-info" />
                <div>
                  <p className="font-medium text-text-primary">Annual System Verification</p>
                  <p className="text-caption text-text-secondary">Due in 12 days • Last: 2026-10-01</p>
                </div>
              </div>
              <Button variant="ghost" size="sm">Schedule</Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Maintenance History */}
      <Card>
        <CardHeader>
          <CardTitle>Maintenance History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Performed By</th>
                  <th>Verified</th>
                  <th>Details</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {mockHistory.map((item, index) => (
                  <tr key={index}>
                    <td className="text-body-sm text-text-primary">{item.date}</td>
                    <td>
                      <Badge variant={item.type === 'FILTER_REPLACEMENT' ? 'success' : item.type === 'CALIBRATION' ? 'info' : 'default'}>
                        {item.type.replace('_', ' ')}
                      </Badge>
                    </td>
                    <td className="text-body-sm text-text-primary">{item.by}</td>
                    <td>
                      {item.verified ? (
                        <Badge variant="success"><CheckCircle className="w-3 h-3 mr-1" /> Verified</Badge>
                      ) : (
                        <Badge variant="warning"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>
                      )}
                    </td>
                    <td className="text-body-sm text-text-secondary">
                      {item.sensor && <span>Sensor: {item.sensor}</span>}
                      {item.pre && item.post && (
                        <span className="ml-2">Pre: {JSON.stringify(item.pre)} → Post: {JSON.stringify(item.post)}</span>
                      )}
                    </td>
                    <td>
                      <Button variant="ghost" size="sm">View</Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}