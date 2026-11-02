import { Link } from 'react-router-dom';
import { Lock, Home, User, AlertTriangle } from 'lucide-react';
import { Button } from '@components/ui/Button';
import { cn } from '@utils/cn';

export function UnauthorizedPage() {
  return (
    <div className="min-h-screen bg-base flex items-center justify-center p-6">
      <div className="w-full max-w-md text-center">
        <div className="w-16 h-16 bg-warning/10 rounded-full flex items-center justify-center mx-auto mb-6">
          <Lock className="w-8 h-8 text-warning" />
        </div>
        <h1 className="text-h1 font-semibold text-text-primary mb-2">Access Denied</h1>
        <p className="text-body text-text-secondary mb-6">
          You don't have permission to access this page. Please contact your administrator if you believe this is an error.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/dashboard">
            <Button variant="primary" className="flex items-center justify-center gap-2">
              <Home className="w-4 h-4" /> Go to Dashboard
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" className="flex items-center justify-center gap-2">
              <User className="w-4 h-4" /> Sign In
            </Button>
          </Link>
        </div>
        <div className="mt-6 p-4 bg-surface rounded-card border border-subtle">
          <AlertTriangle className="w-5 h-5 text-warning mx-auto mb-2" />
          <p className="text-caption text-text-muted">
            Your role may not have access to this feature. Required roles are configured by your system administrator.
          </p>
        </div>
      </div>
    </div>
  );
}