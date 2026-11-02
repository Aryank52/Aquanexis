import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '@/state/auth';

/**
 * Guards all protected routes.
 *
 * Dev bypass: set VITE_AUTH_DISABLED=true in .env to allow unauthenticated
 * access during development when the backend auth endpoints are not yet
 * available.  NEVER set this in production builds.
 */
export function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // ── Dev bypass ──────────────────────────────────────────────────────────────
  if (import.meta.env.VITE_AUTH_DISABLED === 'true') {
    return <Outlet />;
  }
  // ────────────────────────────────────────────────────────────────────────────

  if (isLoading) {
    return (
      <div
        className="flex min-h-screen items-center justify-center bg-surface"
        role="status"
        aria-label="Checking authentication"
      >
        <div className="space-y-4 text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-info border-t-transparent" />
          <p className="text-body-sm text-text-secondary">Verifying session&hellip;</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Navigate
        to="/login"
        state={{ from: location.pathname + location.search }}
        replace
      />
    );
  }

  return <Outlet />;
}
