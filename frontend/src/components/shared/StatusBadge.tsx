import { cn } from '@/lib/utils';

type StatusType = 'healthy' | 'unhealthy' | 'timeout' | 'error' | 'unknown' | 'connected' | 'disconnected';

const statusConfig: Record<StatusType, { bg: string; text: string; label: string }> = {
  healthy: { bg: 'bg-success/15', text: 'text-success', label: 'Healthy' },
  connected: { bg: 'bg-success/15', text: 'text-success', label: 'Connected' },
  unhealthy: { bg: 'bg-warning/15', text: 'text-warning', label: 'Unhealthy' },
  timeout: { bg: 'bg-warning/15', text: 'text-warning', label: 'Timeout' },
  error: { bg: 'bg-destructive/15', text: 'text-destructive', label: 'Error' },
  disconnected: { bg: 'bg-destructive/15', text: 'text-destructive', label: 'Disconnected' },
  unknown: { bg: 'bg-muted', text: 'text-muted-foreground', label: 'Unknown' },
};

export function StatusBadge({ status }: { status: StatusType }) {
  const config = statusConfig[status] || statusConfig.unknown;
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium',
        config.bg,
        config.text
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', config.text.replace('text-', 'bg-'))} />
      {config.label}
    </span>
  );
}
