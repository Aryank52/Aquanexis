import { useState } from 'react';
import { Calendar, AlertTriangle, CheckCircle, XCircle, Plus, Edit, Trash2 } from 'lucide-react';
import { format, isPast, addDays } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import {
  useCalibrationDue,
  useCalibrationRecords,
  useRecordCalibration,
} from '@/hooks/useMaintenance';
import type {
  CalibrationDueResponse,
  CalibrationRecordResponse,
  CalibrationState,
  CalibrationRecordCreate,
} from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const stateVariant: Record<
  CalibrationState,
  'success' | 'warning' | 'critical' | 'info' | 'default'
> = {
  PENDING: 'info',
  VALID: 'success',
  EXPIRED: 'warning',
  OUT_OF_TOLERANCE: 'critical',
  FAILED: 'critical',
};

function getDueStatus(due: CalibrationDueResponse): {
  label: string;
  variant: 'success' | 'warning' | 'critical' | 'info';
} {
  if (!due.next_due) return { label: 'No schedule', variant: 'info' };

  const dueDate = new Date(due.next_due);
  const now = new Date();
  const daysUntil = Math.ceil((dueDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (due.days_overdue && due.days_overdue > 0) {
    return { label: `${due.days_overdue} days overdue`, variant: 'critical' };
  }
  if (daysUntil <= 0) {
    return { label: 'Due today', variant: 'critical' };
  }
  if (daysUntil <= 7) {
    return { label: `${daysUntil} days left`, variant: 'warning' };
  }
  if (daysUntil <= 30) {
    return { label: `${daysUntil} days left`, variant: 'info' };
  }
  return { label: `${daysUntil} days left`, variant: 'success' };
}

export function CalibrationPage() {
  const [showRecordForm, setShowRecordForm] = useState<CalibrationDueResponse | null>(null);
  const [formData, setFormData] = useState<Partial<CalibrationRecordCreate>>({});

  const due = useCalibrationDue(DEVICE_ID);
  const records = useCalibrationRecords(DEVICE_ID);
  const recordCalibration = useRecordCalibration();

  if (due.isError) {
    return (
      <QueryError
        message={(due.error as Error)?.message ?? 'Failed to load calibration due'}
        onRetry={due.refetch}
      />
    );
  }

  const overdueCount = due.data?.filter(d => d.days_overdue && d.days_overdue > 0).length ?? 0;
  const dueSoonCount =
    due.data?.filter(d => {
      if (!d.next_due) return false;
      const daysUntil = Math.ceil(
        (new Date(d.next_due).getTime() - Date.now()) / (1000 * 60 * 60 * 24)
      );
      return daysUntil > 0 && daysUntil <= 7;
    }).length ?? 0;

  const handleRecordSubmit = (sensorId: string, sensorType: string) => {
    if (
      !formData.reference_value ||
      !formData.measured_value ||
      !formData.tolerance ||
      !formData.reference_standard ||
      !formData.calibration_method
    ) {
      alert('Please fill all required fields');
      return;
    }

    recordCalibration.mutate(
      {
        device_id: DEVICE_ID,
        sensor_id: sensorId,
        sensor_type: sensorType,
        calibration_method: formData.calibration_method!,
        reference_standard: formData.reference_standard!,
        reference_value: formData.reference_value!,
        measured_value: formData.measured_value!,
        tolerance: formData.tolerance!,
        technician: formData.technician,
        notes: formData.notes,
      },
      {
        onSuccess: () => {
          setShowRecordForm(null);
          setFormData({});
          due.refetch();
          records.refetch();
        },
      }
    );
  };

  const handleInputChange = (field: string, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Calibration Management</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Sensor calibration schedules, records, and verification
          </p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="ghost"
            onClick={() => {
              due.refetch();
              records.refetch();
            }}
            className="flex items-center gap-2"
          >
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card className={cn(overdueCount > 0 && 'border-critical bg-critical/5')}>
          <CardContent className="p-4 text-center">
            <AlertTriangle
              className={cn(
                'mx-auto mb-1 h-6 w-6',
                overdueCount > 0 ? 'text-critical' : 'text-text-muted'
              )}
            />
            <div className="text-text-primary text-data-xl font-bold">{overdueCount}</div>
            <div className="text-caption text-text-secondary">Overdue</div>
          </CardContent>
        </Card>
        <Card className={cn(dueSoonCount > 0 && 'border-warning bg-warning/5')}>
          <CardContent className="p-4 text-center">
            <Calendar
              className={cn(
                'mx-auto mb-1 h-6 w-6',
                dueSoonCount > 0 ? 'text-warning' : 'text-text-muted'
              )}
            />
            <div className="text-text-primary text-data-xl font-bold">{dueSoonCount}</div>
            <div className="text-caption text-text-secondary">Due within 7 days</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <CheckCircle className="mx-auto mb-1 h-6 w-6 text-success" />
            <div className="text-text-primary text-data-xl font-bold">
              {due.data?.filter(d => getDueStatus(d).variant === 'success').length ?? 0}
            </div>
            <div className="text-caption text-text-secondary">Current</div>
          </CardContent>
        </Card>
      </div>

      {/* Calibration Due */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Calibration Schedule</span>
            {due.isLoading ? (
              <Skeleton className="h-4 w-16" />
            ) : (
              <span className="text-caption text-text-muted">{due.data?.length ?? 0} sensors</span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {due.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded" />
              ))}
            </div>
          ) : !due.data || due.data.length === 0 ? (
            <EmptyState
              title="No calibration schedule"
              description="No sensors configured for calibration tracking"
            />
          ) : (
            <div className="space-y-3">
              {due.data.map(item => {
                const status = getDueStatus(item);
                return (
                  <div
                    key={`${item.sensor_type}-${item.sensor_id}`}
                    className="border-subtle flex items-center justify-between rounded-card border bg-surface p-4"
                  >
                    <div className="flex items-center gap-4">
                      <div
                        className={cn(
                          'h-2 w-2 rounded-full',
                          status.variant === 'critical'
                            ? 'bg-critical'
                            : status.variant === 'warning'
                              ? 'bg-warning'
                              : status.variant === 'success'
                                ? 'bg-success'
                                : 'bg-info'
                        )}
                      />
                      <div>
                        <div className="text-text-primary text-body-sm font-medium">
                          {item.sensor_type}{' '}
                          <span className="text-text-muted">({item.sensor_id})</span>
                        </div>
                        <div className="text-caption text-text-muted">
                          {item.last_calibration
                            ? `Last: ${format(new Date(item.last_calibration), 'dd MMM yyyy')}`
                            : 'Never calibrated'}
                          {item.next_due && (
                            <span className="ml-2">
                              • Due: {format(new Date(item.next_due), 'dd MMM yyyy')}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge variant={status.variant}>{status.label}</Badge>
                      {item.status !== 'VALID' && (
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => {
                            setShowRecordForm(item);
                            setFormData({
                              sensor_id: item.sensor_id,
                              sensor_type: item.sensor_type,
                            });
                          }}
                        >
                          Record Calibration
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Calibration Records */}
      <Card>
        <CardHeader>
          <CardTitle>Calibration History</CardTitle>
        </CardHeader>
        <CardContent>
          {records.isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-16 w-full rounded" />
              ))}
            </div>
          ) : !records.data || records.data.length === 0 ? (
            <EmptyState
              title="No calibration records"
              description="No calibration events have been recorded"
            />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-body-sm">
                <thead>
                  <tr className="border-subtle border-b text-left text-text-secondary">
                    <th className="px-3 py-2 font-medium">Date</th>
                    <th className="px-3 py-2 font-medium">Sensor</th>
                    <th className="px-3 py-2 font-medium">Method</th>
                    <th className="px-3 py-2 font-medium">Reference</th>
                    <th className="px-3 py-2 font-medium">Measured</th>
                    <th className="px-3 py-2 font-medium">Offset</th>
                    <th className="px-3 py-2 font-medium">Result</th>
                    <th className="px-3 py-2 font-medium">Technician</th>
                    <th className="px-3 py-2 font-medium">Next Due</th>
                  </tr>
                </thead>
                <tbody className="divide-subtle divide-y">
                  {records.data.map(record => (
                    <tr key={record.id} className="transition-colors hover:bg-hover">
                      <td className="whitespace-nowrap px-3 py-2">
                        {format(new Date(record.calibration_date), 'dd MMM yyyy HH:mm')}
                      </td>
                      <td className="px-3 py-2">
                        {record.sensor_type}{' '}
                        <span className="text-text-muted">({record.sensor_id})</span>
                      </td>
                      <td className="px-3 py-2 text-text-secondary">{record.calibration_method}</td>
                      <td className="px-3 py-2 font-mono">
                        {record.reference_value.toFixed(2)} {record.reference_standard}
                      </td>
                      <td className="px-3 py-2 font-mono">{record.measured_value.toFixed(2)}</td>
                      <td className="px-3 py-2 font-mono">
                        {record.correction_offset >= 0 ? '+' : ''}
                        {record.correction_offset.toFixed(2)}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant={stateVariant[record.calibration_state]}>
                          {record.calibration_state}
                        </Badge>
                      </td>
                      <td className="px-3 py-2 text-text-secondary">{record.technician ?? '—'}</td>
                      <td className="px-3 py-2 text-text-muted">
                        {record.next_calibration_due
                          ? format(new Date(record.next_calibration_due), 'dd MMM yyyy')
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Record Calibration Modal */}
      {showRecordForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-card bg-elevated p-6 shadow-elevated">
            <h2 className="mb-4 text-h2 font-semibold">Record Calibration</h2>
            <p className="mb-4 text-body-sm text-text-secondary">
              {showRecordForm.sensor_type} ({showRecordForm.sensor_id})
            </p>

            <div className="space-y-4">
              <div>
                <label className="label">Calibration Method</label>
                <input
                  type="text"
                  className="input"
                  value={formData.calibration_method ?? ''}
                  onChange={e => handleInputChange('calibration_method', e.target.value)}
                  placeholder="e.g., Two-point, Single-point, Factory"
                  required
                />
              </div>
              <div>
                <label className="label">Reference Standard</label>
                <input
                  type="text"
                  className="input"
                  value={formData.reference_standard ?? ''}
                  onChange={e => handleInputChange('reference_standard', e.target.value)}
                  placeholder="e.g., NIST buffer pH 7.00"
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Reference Value</label>
                  <input
                    type="number"
                    step="any"
                    className="input"
                    value={formData.reference_value ?? ''}
                    onChange={e => handleInputChange('reference_value', parseFloat(e.target.value))}
                    required
                  />
                </div>
                <div>
                  <label className="label">Measured Value</label>
                  <input
                    type="number"
                    step="any"
                    className="input"
                    value={formData.measured_value ?? ''}
                    onChange={e => handleInputChange('measured_value', parseFloat(e.target.value))}
                    required
                  />
                </div>
              </div>
              <div>
                <label className="label">Tolerance (±)</label>
                <input
                  type="number"
                  step="any"
                  className="input"
                  value={formData.tolerance ?? ''}
                  onChange={e => handleInputChange('tolerance', parseFloat(e.target.value))}
                  required
                />
              </div>
              <div>
                <label className="label">Technician (optional)</label>
                <input
                  type="text"
                  className="input"
                  value={formData.technician ?? ''}
                  onChange={e => handleInputChange('technician', e.target.value)}
                  placeholder="Operator name"
                />
              </div>
              <div>
                <label className="label">Notes (optional)</label>
                <textarea
                  className="input"
                  rows={2}
                  value={formData.notes ?? ''}
                  onChange={e => handleInputChange('notes', e.target.value)}
                  placeholder="Additional notes..."
                />
              </div>

              {recordCalibration.isError && (
                <div className="rounded-button border border-critical/30 bg-critical/10 px-3 py-2 text-body-sm text-critical">
                  Error:{' '}
                  {(recordCalibration.error as Error)?.message ?? 'Failed to record calibration'}
                </div>
              )}

              <div className="flex gap-2 pt-2">
                <Button
                  variant="primary"
                  className="flex-1"
                  onClick={() =>
                    handleRecordSubmit(showRecordForm.sensor_id, showRecordForm.sensor_type)
                  }
                  disabled={recordCalibration.isPending}
                >
                  {recordCalibration.isPending ? 'Recording…' : 'Save Calibration'}
                </Button>
                <Button
                  variant="ghost"
                  className="flex-1"
                  onClick={() => {
                    setShowRecordForm(null);
                    setFormData({});
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
