import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle, Circle, Loader2, ChevronRight, Wifi, Cpu, Sliders, CheckCircle2 } from 'lucide-react';
import { cn } from '@/utils/cn';

const STEPS = [
  { id: 'connect', title: 'Connect Device', desc: 'Enter your device serial number' },
  { id: 'verify', title: 'Verify Connection', desc: 'Confirming device telemetry' },
  { id: 'sensors', title: 'Confirm Sensors', desc: 'Detected sensor configuration' },
  { id: 'thresholds', title: 'Set Thresholds', desc: 'Alert thresholds for your system' },
  { id: 'complete', title: 'Complete', desc: 'Your device is ready' },
] as const;

type StepId = typeof STEPS[number]['id'];

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
    setTimeout(() => { setVerifying(false); setVerified(true); setCurrentStep('sensors'); }, 1500);
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
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-lg animate-fade-in">
        <div className="text-center mb-8">
          <h1 className="text-h1 font-semibold text-text-primary">Device Onboarding</h1>
          <p className="text-body-sm text-text-secondary mt-1">Set up your AquaNexis purification monitor</p>
        </div>

        {/* Progress */}
        <div className="flex items-center mb-8">
          {STEPS.map((step, i) => {
            const done = i < stepIndex;
            const active = i === stepIndex;
            return (
              <div key={step.id} className="flex items-center flex-1">
                <div className={cn(
                  'w-8 h-8 rounded-full flex items-center justify-center text-caption font-semibold transition-colors',
                  done ? 'bg-success text-white' : active ? 'bg-info text-white' : 'bg-surface border-2 border-subtle text-text-muted'
                )}>
                  {done ? <CheckCircle2 className="w-4 h-4" /> : i + 1}
                </div>
                {i < STEPS.length - 1 && (
                  <div className={cn('flex-1 h-0.5 mx-1', done ? 'bg-success' : 'bg-subtle')} />
                )}
              </div>
            );
          })}
        </div>

        {/* Step content */}
        <div className="bg-surface border border-subtle rounded-card p-6 shadow-card">
          <h2 className="text-h3 font-semibold text-text-primary mb-1">{STEPS[stepIndex].title}</h2>
          <p className="text-body-sm text-text-secondary mb-5">{STEPS[stepIndex].desc}</p>

          {currentStep === 'connect' && (
            <div className="space-y-4">
              <div>
                <label className="label" htmlFor="serial">Device Serial Number</label>
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
                Continue <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {currentStep === 'verify' && (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-4 bg-info/5 border border-info/20 rounded-button">
                <Wifi className="w-5 h-5 text-info flex-shrink-0" />
                <div>
                  <p className="text-body-sm font-medium text-text-primary">Serial: {serial}</p>
                  <p className="text-caption text-text-secondary">Waiting for first telemetry ping…</p>
                </div>
              </div>
              <button className="btn btn-primary w-full" onClick={handleVerify} disabled={verifying}>
                {verifying ? <><Loader2 className="w-4 h-4 animate-spin" /> Verifying…</> : 'Verify Connection'}
              </button>
            </div>
          )}

          {currentStep === 'sensors' && (
            <div className="space-y-4">
              <div className="space-y-2">
                {MOCK_SENSORS.map(s => (
                  <div key={s.name} className="flex items-center justify-between p-2.5 bg-base border border-subtle rounded-button">
                    <div className="flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-text-muted" />
                      <span className="text-body-sm text-text-primary">{s.name}</span>
                    </div>
                    <span className="inline-flex items-center gap-1 text-caption text-success">
                      <CheckCircle className="w-3 h-3" /> Detected
                    </span>
                  </div>
                ))}
              </div>
              <button className="btn btn-primary w-full" onClick={() => setCurrentStep('thresholds')}>
                Confirm Sensors <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {currentStep === 'thresholds' && (
            <div className="space-y-4">
              <div className="p-3 bg-info/5 border border-info/20 rounded-button">
                <div className="flex items-center gap-2 mb-1">
                  <Sliders className="w-4 h-4 text-info" />
                  <p className="text-body-sm font-medium text-text-primary">Default thresholds applied</p>
                </div>
                <p className="text-caption text-text-secondary">
                  WHO/EPA guidelines: AquaScore warn &lt;70, FSI warn &gt;70, FHI critical &lt;20, RUL warn &lt;30 days.
                  Customise these later in Device Settings.
                </p>
              </div>
              <button className="btn btn-primary w-full" onClick={() => setCurrentStep('complete')}>
                Apply Defaults &amp; Continue <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}

          {currentStep === 'complete' && (
            <div className="text-center space-y-5">
              <div className="w-16 h-16 bg-success/10 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle className="w-9 h-9 text-success" />
              </div>
              <div>
                <h3 className="text-h3 font-semibold text-text-primary">Device Ready</h3>
                <p className="text-body-sm text-text-secondary mt-1">
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
        <p className="text-caption text-text-muted text-center mt-4">
          Step {stepIndex + 1} of {STEPS.length} — {STEPS[stepIndex].title}
        </p>
      </div>
    </div>
  );
}
