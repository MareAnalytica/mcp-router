import { useQuery } from '@tanstack/react-query';
import { Server, Wrench, Activity, BookOpen, Plus, Store } from 'lucide-react';
import { Link } from 'react-router';
import { listServers } from '@/api/servers';
import { listServerHealth } from '@/api/health';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { StatusBadge } from '@/components/shared/StatusBadge';

function StatCard({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string | number;
  color: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <div className="flex items-center gap-3">
        <div className={`rounded-md p-2 ${color}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-card-foreground">{value}</p>
          <p className="text-sm text-muted-foreground">{label}</p>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data: servers, isLoading: serversLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: listServers,
  });

  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: listServerHealth,
  });

  if (serversLoading || healthLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  const totalServers = servers?.length || 0;
  const enabledServers = servers?.filter((s) => s.is_enabled).length || 0;
  const healthyCount = health?.filter((h) => h.status === 'healthy').length || 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <div className="flex gap-2">
          <Link
            to="/servers"
            className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Add Server
          </Link>
          <Link
            to="/catalog"
            className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-foreground hover:bg-accent transition-colors"
          >
            <Store className="h-4 w-4" />
            Browse Catalog
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatCard icon={Server} label="Total Servers" value={totalServers} color="bg-primary/10 text-primary" />
        <StatCard icon={Activity} label="Active Servers" value={enabledServers} color="bg-success/10 text-success" />
        <StatCard icon={Wrench} label="Healthy" value={healthyCount} color="bg-success/10 text-success" />
        <StatCard
          icon={BookOpen}
          label="Unhealthy"
          value={totalServers - healthyCount}
          color="bg-warning/10 text-warning"
        />
      </div>

      {/* Server Health Summary */}
      <div className="rounded-lg border border-border bg-card">
        <div className="border-b border-border px-5 py-3">
          <h2 className="font-semibold">Server Status</h2>
        </div>
        {!health || health.length === 0 ? (
          <div className="px-5 py-8 text-center text-sm text-muted-foreground">
            No servers configured yet. Add a server or browse the catalog to get started.
          </div>
        ) : (
          <div className="divide-y divide-border">
            {health.map((h) => (
              <div key={h.server_id} className="flex items-center justify-between px-5 py-3">
                <div>
                  <p className="font-medium text-sm">{h.server_name}</p>
                  {h.response_time_ms !== null && (
                    <p className="text-xs text-muted-foreground">{h.response_time_ms}ms</p>
                  )}
                </div>
                <StatusBadge status={h.status} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
