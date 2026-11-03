import { Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function SessionExpiredPage() {
  const navigate = useNavigate();
  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-sm animate-fade-in text-center">
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-full bg-warning/10">
          <Clock className="h-7 w-7 text-warning" />
        </div>
        <h1 className="text-text-primary mb-2 text-h2 font-semibold">Session Expired</h1>
        <p className="mb-6 text-body text-text-secondary">
          Your session has expired. Please sign in again to continue monitoring your water system.
        </p>
        <button
          className="btn btn-primary w-full"
          onClick={() => navigate('/login', { replace: true })}
        >
          Sign In Again
        </button>
      </div>
    </div>
  );
}
