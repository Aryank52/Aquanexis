// ============================================================================
// PageSkeleton — Loading placeholder for lazy-loaded routes
// ============================================================================
import { cn } from '@/utils/cn';

export function PageSkeleton() {
  return (
    <div className="flex min-h-screen bg-base">
      {/* Sidebar skeleton */}
      <aside className="border-subtle hidden w-72 border-r bg-surface lg:block">
        <div className="border-subtle flex h-16 items-center gap-3 border-b px-4">
          <div className="skeleton h-8 w-8 rounded-lg" />
          <div className="skeleton h-5 w-24 rounded" />
        </div>
        <div className="space-y-2 p-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="skeleton h-10 w-full rounded-button" />
          ))}
        </div>
      </aside>

      {/* Main content skeleton */}
      <div className="flex-1">
        {/* Header skeleton */}
        <header className="border-subtle flex h-16 items-center justify-between border-b bg-elevated px-6">
          <div className="skeleton h-8 w-32 rounded" />
          <div className="flex items-center gap-3">
            <div className="skeleton h-8 w-8 rounded-full" />
            <div className="skeleton h-8 w-8 rounded-full" />
          </div>
        </header>

        {/* Content skeleton */}
        <main className="space-y-6 p-6 lg:p-8">
          {/* Title */}
          <div className="space-y-2">
            <div className="skeleton h-8 w-48 rounded" />
            <div className="skeleton h-4 w-80 rounded" />
          </div>

          {/* Cards grid */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="border-subtle space-y-4 rounded-card border bg-surface p-6">
                <div className="skeleton h-6 w-32 rounded" />
                <div className="skeleton h-40 w-full rounded" />
                <div className="skeleton h-4 w-48 rounded" />
              </div>
            ))}
          </div>

          {/* Sensor grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {Array.from({ length: 10 }).map((_, i) => (
              <div key={i} className="border-subtle space-y-2 rounded-card border bg-surface p-4">
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
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('skeleton rounded', className)} aria-hidden="true" {...props} />;
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
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-critical/10">
        <svg
          className="h-6 w-6 text-critical"
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
      <p className="text-text-primary mb-1 text-body">{message}</p>
      <p className="mb-4 text-caption text-text-muted">Check your connection and try again.</p>
      {onRetry && (
        <button onClick={onRetry} className="btn btn-secondary btn-sm">
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
        <div className="border-subtle mb-4 flex h-12 w-12 items-center justify-center rounded-full border bg-surface">
          {icon}
        </div>
      )}
      <p className="text-text-primary mb-1 text-body font-medium">{title}</p>
      {description && <p className="max-w-sm text-caption text-text-muted">{description}</p>}
    </div>
  );
}
