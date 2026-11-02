// ============================================================================
// PageSkeleton — Loading placeholder for lazy-loaded routes
// ============================================================================
import { cn } from '@/utils/cn';

export function PageSkeleton() {
  return (
    <div className="min-h-screen bg-base flex">
      {/* Sidebar skeleton */}
      <aside className="hidden lg:block w-72 bg-surface border-r border-subtle">
        <div className="h-16 px-4 flex items-center gap-3 border-b border-subtle">
          <div className="skeleton w-8 h-8 rounded-lg" />
          <div className="skeleton h-5 w-24 rounded" />
        </div>
        <div className="p-4 space-y-2">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="skeleton h-10 w-full rounded-button" />
          ))}
        </div>
      </aside>

      {/* Main content skeleton */}
      <div className="flex-1">
        {/* Header skeleton */}
        <header className="h-16 bg-elevated border-b border-subtle flex items-center justify-between px-6">
          <div className="skeleton h-8 w-32 rounded" />
          <div className="flex items-center gap-3">
            <div className="skeleton w-8 h-8 rounded-full" />
            <div className="skeleton w-8 h-8 rounded-full" />
          </div>
        </header>

        {/* Content skeleton */}
        <main className="p-6 lg:p-8 space-y-6">
          {/* Title */}
          <div className="space-y-2">
            <div className="skeleton h-8 w-48 rounded" />
            <div className="skeleton h-4 w-80 rounded" />
          </div>

          {/* Cards grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="bg-surface border border-subtle rounded-card p-6 space-y-4"
              >
                <div className="skeleton h-6 w-32 rounded" />
                <div className="skeleton h-40 w-full rounded" />
                <div className="skeleton h-4 w-48 rounded" />
              </div>
            ))}
          </div>

          {/* Sensor grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4">
            {Array.from({ length: 10 }).map((_, i) => (
              <div
                key={i}
                className="bg-surface border border-subtle rounded-card p-4 space-y-2"
              >
                <div className="skeleton h-4 w-16 rounded" />
                <div className="skeleton h-8 w-20 rounded" />
                <div className="skeleton h-3 w-12 rounded" />
              </div>
            ))}
          </div>
        </main>
      </div>
    </div>
  );
}

/**
 * Inline skeleton placeholder for use inside pages (cards, values, etc.)
 */
export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('skeleton rounded', className)}
      aria-hidden="true"
      {...props}
    />
  );
}

/**
 * Error state for failed data fetches.
 */
export function QueryError({
  message = 'Failed to load data.',
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 rounded-full bg-critical/10 flex items-center justify-center mb-4">
        <svg
          className="w-6 h-6 text-critical"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
          />
        </svg>
      </div>
      <p className="text-body text-text-primary mb-1">{message}</p>
      <p className="text-caption text-text-muted mb-4">
        Check your connection and try again.
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="btn btn-secondary btn-sm"
        >
          Retry
        </button>
      )}
    </div>
  );
}

/**
 * Empty state for when there's no data.
 */
export function EmptyState({
  title = 'No data available',
  description,
  icon,
}: {
  title?: string;
  description?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {icon && (
        <div className="w-12 h-12 rounded-full bg-surface flex items-center justify-center mb-4 border border-subtle">
          {icon}
        </div>
      )}
      <p className="text-body font-medium text-text-primary mb-1">{title}</p>
      {description && (
        <p className="text-caption text-text-muted max-w-sm">{description}</p>
      )}
    </div>
  );
}
