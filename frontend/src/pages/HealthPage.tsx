import { useQuery } from '@tanstack/react-query';
import { Activity, RefreshCw } from 'lucide-react';
import { listServerHealth } from '@/api/health';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { cn } from '@/lib/utils';

export function HealthPage() {
  const { data: health, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['health'],
    queryFn: listServerHealth,
    refetchInterval: 30000,
  });

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Health Monitoring</h1>
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Health Monitoring</h1>
          <p className="text-muted-foreground mt-1">Real-time health status of your connected MCP servers.</p>
        </div>
        <button
          onClick={() => refetch()}
          disabled={isFetching}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors disabled:opacity-50"
        >
          <RefreshCw className={cn('h-4 w-4', isFetching && 'animate-spin')} />
          Refresh
        </button>
      </div>

      {!health || health.length === 0 ? (
        <EmptyState
          icon={Activity}
          title="No health data"
          description="Health checks will appear here once you have enabled MCP servers."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {health.map((h) => (
            <div key={h.server_id} className="rounded-lg border border-border bg-card p-5">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold">{h.server_name}</h3>
                <StatusBadge status={h.status} />
              </div>

              <dl className="space-y-1.5 text-sm">
                {h.response_time_ms !== null && (
                  <div className="flex justify-between">
                    <dt className="text-muted-foreground">Response time</dt>
                    <dd className="font-mono">{h.response_time_ms}ms</dd>
                  </div>
                )}
                <div className="flex justify-between">
                  <dt className="text-muted-foreground">Last checked</dt>
                  <dd className="text-xs">{new Date(h.checked_at).toLocaleString()}</dd>
                </div>
              </dl>

              {h.error_message && (
                <div className="mt-3 rounded-md bg-destructive/10 px-3 py-2 text-xs text-destructive">
                  {h.error_message}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
