import { ShieldOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/state/auth';

export function AccessDeniedPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-sm text-center animate-fade-in">
        <div className="w-14 h-14 bg-critical/10 rounded-full flex items-center justify-center mx-auto mb-5">
          <ShieldOff className="w-7 h-7 text-critical" />
        </div>
        <h1 className="text-h2 font-semibold text-text-primary mb-2">Access Denied</h1>
        <p className="text-body text-text-secondary mb-2">
          You don't have permission to access this resource.
        </p>
        <p className="text-body-sm text-text-muted mb-6">
          Contact your administrator if you believe this is an error.
        </p>
        <div className="flex flex-col gap-3">
          <button className="btn btn-primary" onClick={() => navigate('/dashboard', { replace: true })}>
            Return to Dashboard
          </button>
          <button className="btn btn-ghost text-text-muted" onClick={() => logout()}>
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
