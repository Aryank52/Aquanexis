import { useState, useMemo } from 'react';
import { RefreshCw, Send, RotateCcw, X, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
import { Card, CardContent, CardHeader, CardTitle } from '@components/ui/Card';
import { Badge } from '@components/ui/Badge';
import { Button } from '@components/ui/Button';
import { Skeleton, QueryError, EmptyState } from '@components/ui/PageSkeleton';
import { cn } from '@utils/cn';
import {
  useNotifications,
  useRetryNotification,
  useCancelNotification,
  useNotificationStats,
} from '@/hooks/useNotifications';
import type {
  NotificationOutboxResponse,
  NotificationStatus,
  NotificationChannel,
} from '@/types/api';

const DEVICE_ID = import.meta.env.VITE_DEVICE_ID ?? '00000000-0000-0000-0000-000000000001';

const statusVariant: Record<
  NotificationStatus,
  'success' | 'warning' | 'critical' | 'info' | 'default'
> = {
  pending: 'info',
  processing: 'info',
  sent: 'success',
  retry: 'warning',
  dead_letter: 'critical',
  failed: 'critical',
};

const channelIcon: Record<NotificationChannel, typeof Send> = {
  email: Send,
  sms: Send,
  webhook: Send,
  push: Send,
};

function statusColor(status: NotificationStatus): string {
  switch (status) {
    case 'sent':
      return 'text-success';
    case 'pending':
    case 'processing':
      return 'text-info';
    case 'retry':
      return 'text-warning';
    case 'dead_letter':
    case 'failed':
      return 'text-critical';
    default:
      return 'text-text-muted';
  }
}

export function NotificationsPage() {
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterChannel, setFilterChannel] = useState<string>('all');
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const stats = useNotificationStats(DEVICE_ID);
  const { data, isLoading, isError, error, refetch } = useNotifications({
    device_id: DEVICE_ID,
    status: filterStatus === 'all' ? undefined : filterStatus,
    channel: filterChannel === 'all' ? undefined : filterChannel,
    limit: 50,
  });

  const retry = useRetryNotification();
  const cancel = useCancelNotification();

  const notifications = useMemo(() => data ?? [], [data]);

  const statusCounts = useMemo(() => {
    return notifications.reduce(
      (acc, n) => {
        acc[n.status] = (acc[n.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>
    );
  }, [notifications]);

  if (isError) {
    return (
      <QueryError
        message={(error as Error)?.message ?? 'Failed to load notifications'}
        onRetry={refetch}
      />
    );
  }

  return (
    <div className="animate-fade-in space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-text-primary text-h1 font-semibold">Notifications</h1>
          <p className="mt-1 text-body-sm text-text-secondary">
            Delivery status, retry management, and notification history
          </p>
        </div>
        <div className="flex gap-3">
          <Button variant="ghost" onClick={() => refetch()} className="flex items-center gap-2">
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4 lg:grid-cols-6">
        <StatCard
          label="Total"
          value={notifications.length}
          icon={Send}
          color="text-text-primary"
        />
        <StatCard label="Sent" value={statusCounts.sent ?? 0} icon={Send} color="text-success" />
        <StatCard
          label="Pending"
          value={statusCounts.pending ?? 0}
          icon={RotateCcw}
          color="text-info"
        />
        <StatCard
          label="Retry"
          value={statusCounts.retry ?? 0}
          icon={RotateCcw}
          color="text-warning"
        />
        <StatCard label="Failed" value={statusCounts.failed ?? 0} icon={X} color="text-critical" />
        <StatCard
          label="Dead Letter"
          value={statusCounts.dead_letter ?? 0}
          icon={X}
          color="text-critical"
        />
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-2">
              <label htmlFor="filter-status" className="text-caption text-text-secondary">
                Status:
              </label>
              <select
                id="filter-status"
                className="input w-40 text-body-sm"
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                aria-label="Filter by status"
              >
                <option value="all">All Statuses</option>
                <option value="pending">Pending</option>
                <option value="processing">Processing</option>
                <option value="sent">Sent</option>
                <option value="retry">Retry</option>
                <option value="dead_letter">Dead Letter</option>
                <option value="failed">Failed</option>
              </select>
            </div>
            <div className="flex items-center gap-2">
              <label htmlFor="filter-channel" className="text-caption text-text-secondary">
                Channel:
              </label>
              <select
                id="filter-channel"
                className="input w-40 text-body-sm"
                value={filterChannel}
                onChange={e => setFilterChannel(e.target.value)}
                aria-label="Filter by channel"
              >
                <option value="all">All Channels</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="webhook">Webhook</option>
                <option value="push">Push</option>
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications List */}
      <Card>
        <CardHeader>
          <CardTitle>Notification History ({isLoading ? '…' : notifications.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full rounded" />
              ))}
            </div>
          ) : notifications.length === 0 ? (
            <EmptyState
              title="No notifications"
              description="No notifications match the current filters"
            />
          ) : (
            <div className="divide-subtle divide-y">
              {notifications.map(notification => (
                <NotificationRow
                  key={notification.id}
                  notification={notification}
                  isExpanded={expandedId === notification.id}
                  onToggle={() =>
                    setExpandedId(expandedId === notification.id ? null : notification.id)
                  }
                  onRetry={retry.mutate}
                  onCancel={cancel.mutate}
                  retryPending={retry.isPending && retry.variables === notification.id}
                  cancelPending={cancel.isPending && cancel.variables === notification.id}
                />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon: Icon,
  color,
}: {
  label: string;
  value: number;
  icon: typeof Send;
  color: string;
}) {
  return (
    <Card>
      <CardContent className="p-4 text-center">
        <Icon className={cn('mx-auto mb-1 h-5 w-5', color)} />
        <div className="text-text-primary text-data-lg font-bold">{value}</div>
        <div className="text-caption text-text-secondary">{label}</div>
      </CardContent>
    </Card>
  );
}

interface NotificationRowProps {
  notification: NotificationOutboxResponse;
  isExpanded: boolean;
  onToggle: () => void;
  onRetry: (id: string) => void;
  onCancel: (id: string) => void;
  retryPending: boolean;
  cancelPending: boolean;
}

function NotificationRow({
  notification,
  isExpanded,
  onToggle,
  onRetry,
  onCancel,
  retryPending,
  cancelPending,
}: NotificationRowProps) {
  const ChannelIcon = channelIcon[notification.channel] || Send;
  const variant = statusVariant[notification.status];

  return (
    <div className="bg-surface/50">
      <button
        onClick={onToggle}
        className="flex w-full items-center gap-4 p-4 text-left transition-colors hover:bg-hover"
        aria-expanded={isExpanded}
      >
        <ChannelIcon className={cn('h-5 w-5 flex-shrink-0', statusColor(notification.status))} />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-text-primary truncate text-body-sm font-medium">
              {notification.template_name ?? 'Notification'}
            </span>
            <Badge variant={variant}>{notification.status.replace('_', ' ').toUpperCase()}</Badge>
            <Badge variant="default">{notification.channel.toUpperCase()}</Badge>
          </div>
          <div className="mt-1 flex items-center gap-3 text-caption text-text-muted">
            <span>To: {notification.recipient}</span>
            <span>Provider: {notification.provider}</span>
            <span>
              {formatDistanceToNow(new Date(notification.created_at), { addSuffix: true })}
            </span>
            {notification.sent_at && (
              <span className="text-success">
                Sent {formatDistanceToNow(new Date(notification.sent_at), { addSuffix: true })}
              </span>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {notification.status === 'dead_letter' || notification.status === 'failed' ? (
            <>
              <Button
                variant="secondary"
                size="sm"
                onClick={e => {
                  e.stopPropagation();
                  onRetry(notification.id);
                }}
                disabled={retryPending}
                className="flex items-center gap-1"
              >
                <RotateCcw className="h-3 w-3" />
                Retry
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={e => {
                  e.stopPropagation();
                  onCancel(notification.id);
                }}
                disabled={cancelPending}
                className="flex items-center gap-1"
              >
                <X className="h-3 w-3" />
                Cancel
              </Button>
            </>
          ) : notification.status === 'retry' ? (
            <Button
              variant="ghost"
              size="sm"
              onClick={e => {
                e.stopPropagation();
                onCancel(notification.id);
              }}
              disabled={cancelPending}
            >
              Cancel
            </Button>
          ) : null}
          <span className={cn('text-caption', isExpanded ? 'text-success' : 'text-text-muted')}>
            {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className="border-subtle space-y-3 border-t bg-surface p-4">
          <div className="grid grid-cols-2 gap-4 text-body-sm">
            <div>
              <span className="text-text-secondary">ID:</span>{' '}
              <span className="text-text-primary ml-2 font-mono">{notification.id}</span>
            </div>
            <div>
              <span className="text-text-secondary">Alert ID:</span>{' '}
              <span className="text-text-primary ml-2 font-mono">{notification.alert_id}</span>
            </div>
            <div>
              <span className="text-text-secondary">Device:</span>{' '}
              <span className="text-text-primary ml-2 font-mono">{notification.device_id}</span>
            </div>
            <div>
              <span className="text-text-secondary">Dedupe Key:</span>{' '}
              <span className="text-text-primary ml-2 font-mono">{notification.dedupe_key}</span>
            </div>
            <div>
              <span className="text-text-secondary">Attempts:</span>{' '}
              <span className="ml-2">
                {notification.attempt_count} / {notification.max_attempts}
              </span>
            </div>
            {notification.next_attempt_at && (
              <div>
                <span className="text-text-secondary">Next Retry:</span>{' '}
                <span className="ml-2">
                  {format(new Date(notification.next_attempt_at), 'dd MMM yyyy HH:mm')}
                </span>
              </div>
            )}
          </div>
          {notification.subject && (
            <div className="bg-background border-subtle rounded-button border p-3">
              <div className="mb-1 text-caption text-text-secondary">Subject</div>
              <div className="text-text-primary text-body-sm">{notification.subject}</div>
            </div>
          )}
          <div className="bg-background border-subtle rounded-button border p-3">
            <div className="mb-1 text-caption text-text-secondary">Body</div>
            <div className="text-text-primary whitespace-pre-wrap text-body-sm">
              {notification.body}
            </div>
          </div>
          {notification.template_data && Object.keys(notification.template_data).length > 0 && (
            <div className="bg-background border-subtle rounded-button border p-3">
              <div className="mb-1 text-caption text-text-secondary">Template Data</div>
              <pre className="text-text-primary max-h-40 overflow-auto text-caption">
                {JSON.stringify(notification.template_data, null, 2)}
              </pre>
            </div>
          )}
          {notification.last_error && (
            <div className="rounded-button border border-critical/30 bg-critical/10 p-3">
              <div className="mb-1 flex items-center gap-1 text-caption text-critical">
                <X className="h-3 w-3" /> Last Error
              </div>
              <div className="text-text-primary text-body-sm">{notification.last_error}</div>
              {notification.error_category && (
                <div className="mt-1 text-caption text-text-muted">
                  Category: {notification.error_category}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
