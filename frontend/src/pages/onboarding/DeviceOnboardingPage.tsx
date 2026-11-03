import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  CheckCircle,
  Circle,
  Loader2,
  ChevronRight,
  Wifi,
  Cpu,
  Sliders,
  CheckCircle2,
} from 'lucide-react';
import { cn } from '@/utils/cn';

const STEPS = [
  { id: 'connect', title: 'Connect Device', desc: 'Enter your device serial number' },
  { id: 'verify', title: 'Verify Connection', desc: 'Confirming device telemetry' },
  { id: 'sensors', title: 'Confirm Sensors', desc: 'Detected sensor configuration' },
  { id: 'thresholds', title: 'Set Thresholds', desc: 'Alert thresholds for your system' },
  { id: 'complete', title: 'Complete', desc: 'Your device is ready' },
] as const;

type StepId = (typeof STEPS)[number]['id'];

export function DeviceOnboardingPage() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState<StepId>('connect');
  const [serial, setSerial] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [verified, setVerified] = useState(false);

  const stepIndex = STEPS.findIndex(s => s.id === currentStep);

  const handleVerify = () => {
    if (!serial.trim()) return;
    setVerifying(true);
    // Simulate verification — will be replaced by real polling
    setTimeout(() => {
      setVerifying(false);
      setVerified(true);
      setCurrentStep('sensors');
    }, 1500);
  };

  const MOCK_SENSORS = [
    { name: 'TDS / EC', status: 'detected' },
    { name: 'pH', status: 'detected' },
    { name: 'Turbidity', status: 'detected' },
    { name: 'Temperature', status: 'detected' },
    { name: 'Flow', status: 'detected' },
    { name: 'Pressure', status: 'detected' },
    { name: 'Tank Level', status: 'detected' },
    { name: 'Leak Sensor', status: 'detected' },
    { name: 'Pump Current', status: 'detected' },
  ];

  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-lg animate-fade-in">
        <div className="mb-8 text-center">
          <h1 className="text-text-primary text-h1 font-semibold">Device Onboarding</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Set up your AquaNexis purification monitor
          </p>
        </div>

        {/* Progress */}
        <div className="mb-8 flex items-center">
          {STEPS.map((step, i) => {
            const done = i < stepIndex;
            const active = i === stepIndex;
            return (
              <div key={step.id} className="flex flex-1 items-center">
                <div
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full text-caption font-semibold transition-colors',
                    done
                      ? 'bg-success text-white'
                      : active
                        ? 'bg-info text-white'
                        : 'border-subtle border-2 bg-surface text-text-muted'
                  )}
                >
                  {done ? <CheckCircle2 className="h-4 w-4" /> : i + 1}
                </div>
                {i < STEPS.length - 1 && (
                  <div className={cn('mx-1 h-0.5 flex-1', done ? 'bg-success' : 'bg-subtle')} />
                )}
              </div>
            );
          })}
        </div>

        {/* Step content */}
        <div className="border-subtle rounded-card border bg-surface p-6 shadow-card">
          <h2 className="text-text-primary mb-1 text-h3 font-semibold">{STEPS[stepIndex].title}</h2>
          <p className="mb-5 text-body-sm text-text-secondary">{STEPS[stepIndex].desc}</p>

          {currentStep === 'connect' && (
            <div className="space-y-4">
              <div>
                <label className="label" htmlFor="serial">
                  Device Serial Number
                </label>
                <input
                  id="serial"
                  className="input font-mono"
                  placeholder="AQN-XXXX-XXXX"
                  value={serial}
                  onChange={e => setSerial(e.target.value)}
                  autoFocus
                />
              </div>
              <button
                className="btn btn-primary w-full"
                onClick={() => setCurrentStep('verify')}
                disabled={!serial.trim()}
              >
                Continue <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {currentStep === 'verify' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 rounded-button border border-info/20 bg-info/5 p-4">
                <Wifi className="h-5 w-5 flex-shrink-0 text-info" />
                <div>
                  <p className="text-text-primary text-body-sm font-medium">Serial: {serial}</p>
                  <p className="text-caption text-text-secondary">
                    Waiting for first telemetry ping…
                  </p>
                </div>
              </div>
              <button
                className="btn btn-primary w-full"
                onClick={handleVerify}
                disabled={verifying}
              >
                {verifying ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" /> Verifying…
                  </>
                ) : (
                  'Verify Connection'
                )}
              </button>
            </div>
          )}

          {currentStep === 'sensors' && (
            <div className="space-y-4">
              <div className="space-y-2">
                {MOCK_SENSORS.map(s => (
                  <div
                    key={s.name}
                    className="border-subtle flex items-center justify-between rounded-button border bg-base p-2.5"
                  >
                    <div className="flex items-center gap-2">
                      <Cpu className="h-4 w-4 text-text-muted" />
                      <span className="text-text-primary text-body-sm">{s.name}</span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-caption text-success">
                      <CheckCircle className="h-3 w-3" /> Detected
                    </span>
                  </div>
                ))}
              </div>
              <button
                className="btn btn-primary w-full"
                onClick={() => setCurrentStep('thresholds')}
              >
                Confirm Sensors <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {currentStep === 'thresholds' && (
            <div className="space-y-4">
              <div className="rounded-button border border-info/20 bg-info/5 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <Sliders className="h-4 w-4 text-info" />
                  <p className="text-text-primary text-body-sm font-medium">
                    Default thresholds applied
                  </p>
                </div>
                <p className="text-caption text-text-secondary">
                  WHO/EPA guidelines: AquaScore warn &lt;70, FSI warn &gt;70, FHI critical &lt;20,
                  RUL warn &lt;30 days. Customise these later in Device Settings.
                </p>
              </div>
              <button className="btn btn-primary w-full" onClick={() => setCurrentStep('complete')}>
                Apply Defaults &amp; Continue <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="space-y-5 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success/10">
                <CheckCircle className="h-9 w-9 text-success" />
              </div>
              <div>
                <h3 className="text-text-primary text-h3 font-semibold">Device Ready</h3>
                <p className="mt-1 text-body-sm text-text-secondary">
                  Your AquaNexis system is configured and monitoring.
                </p>
              </div>
              <button className="btn btn-primary w-full" onClick={() => navigate('/dashboard')}>
                Go to Dashboard
              </button>
            </div>
          )}
        </div>

        {/* Step label */}
        <p className="mt-4 text-center text-caption text-text-muted">
          Step {stepIndex + 1} of {STEPS.length} — {STEPS[stepIndex].title}
        </p>
      </div>
    </div>
  );
}
