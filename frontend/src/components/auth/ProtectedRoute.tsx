import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/state/auth';
import { Loader2 } from 'lucide-react';
import { cn } from '@utils/cn';

interface ProtectedRouteProps {
  allowedRoles?: string[];
  fallbackPath?: string;
}

export function ProtectedRoute({ allowedRoles, fallbackPath = '/login' }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className={cn('fixed inset-0 flex items-center justify-center', 'bg-background')}>
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="text-primary h-10 w-10 animate-spin" />
          <p className="text-body-sm text-text-secondary">Verifying session…</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={fallbackPath} state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}

interface PublicRouteProps {
  children: React.ReactNode;
  redirectTo?: string;
}

export function PublicRoute({ children, redirectTo = '/' }: PublicRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className={cn('fixed inset-0 flex items-center justify-center', 'bg-background')}>
        <Loader2 className="text-primary h-10 w-10 animate-spin" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  return <>{children}</>;
}

export function RoleGuard({ children, roles }: { children: React.ReactNode; roles: string[] }) {
  const { user, isAuthenticated } = useAuth();

  if (!isAuthenticated || !user || !roles.includes(user.role)) {
    return null;
  }

  return <>{children}</>;
}
