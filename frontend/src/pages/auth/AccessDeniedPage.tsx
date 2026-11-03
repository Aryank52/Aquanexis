import { ShieldOff } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/state/auth';

export function AccessDeniedPage() {
  const navigate = useNavigate();
  const { logout } = useAuth();
  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-sm animate-fade-in text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-critical/10">
          <ShieldOff className="h-7 w-7 text-critical" />
        </div>
        <h1 className="text-text-primary mb-2 text-h2 font-semibold">Access Denied</h1>
        <p className="mb-2 text-body text-text-secondary">
          You don't have permission to access this resource.
        </p>
        <p className="mb-6 text-body-sm text-text-muted">
          Contact your administrator if you believe this is an error.
        </p>
        <div className="flex flex-col gap-3">
          <button
            className="btn btn-primary"
            onClick={() => navigate('/dashboard', { replace: true })}
          >
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
