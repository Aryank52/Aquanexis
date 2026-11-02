import { Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function SessionExpiredPage() {
  const navigate = useNavigate();
  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-sm text-center animate-fade-in">
        <div className="w-14 h-14 bg-warning/10 rounded-full flex items-center justify-center mx-auto mb-5">
          <Clock className="w-7 h-7 text-warning" />
        </div>
        <h1 className="text-h2 font-semibold text-text-primary mb-2">Session Expired</h1>
        <p className="text-body text-text-secondary mb-6">
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
