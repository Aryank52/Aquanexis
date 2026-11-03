import { Link } from 'react-router-dom';
import { Lock, Home, User, AlertTriangle } from 'lucide-react';
import { Button } from '@components/ui/Button';
import { cn } from '@utils/cn';

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-base p-6">
      <div className="w-full max-w-md text-center">
        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-warning/10">
          <Lock className="h-8 w-8 text-warning" />
        </div>
        <h1 className="text-text-primary mb-2 text-h1 font-semibold">Access Denied</h1>
        <p className="mb-6 text-body text-text-secondary">
          You don't have permission to access this page. Please contact your administrator if you
          believe this is an error.
        </p>
        <div className="flex flex-col gap-3">
          <Link to="/dashboard">
            <Button variant="primary" className="flex items-center justify-center gap-2">
              <Home className="h-4 w-4" /> Go to Dashboard
            </Button>
          </Link>
          <Link to="/login">
            <Button variant="secondary" className="flex items-center justify-center gap-2">
              <User className="h-4 w-4" /> Sign In
            </Button>
          </Link>
        </div>
        <div className="border-subtle mt-6 rounded-card border bg-surface p-4">
          <AlertTriangle className="mx-auto mb-2 h-5 w-5 text-warning" />
          <p className="text-caption text-text-muted">
            Your role may not have access to this feature. Required roles are configured by your
            system administrator.
          </p>
        </div>
      </div>
    </div>
  );
}
