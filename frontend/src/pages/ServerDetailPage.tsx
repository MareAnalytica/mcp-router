import { useParams, Link } from 'react-router';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, Wrench, BookOpen, MessageSquare, Key } from 'lucide-react';
import { getServer } from '@/api/servers';
import { listKeys } from '@/api/keys';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { StatusBadge } from '@/components/shared/StatusBadge';

export function ServerDetailPage() {
  const { id } = useParams<{ id: string }>();

  const { data: server, isLoading } = useQuery({
    queryKey: ['servers', id],
    queryFn: () => getServer(id!),
    enabled: !!id,
  });

  const { data: keys } = useQuery({
    queryKey: ['keys', id],
    queryFn: () => listKeys(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return <LoadingSkeleton rows={6} />;
  }

  if (!server) {
    return <div className="text-muted-foreground">Server not found</div>;
  }

  return (
    <div>
      <Link
        to="/servers"
        className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground mb-4"
      >
        <ArrowLeft className="h-4 w-4" /> Back to Servers
      </Link>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">{server.name}</h1>
          {server.description && <p className="text-muted-foreground mt-1">{server.description}</p>}
        </div>
        <StatusBadge status={server.is_enabled ? 'connected' : 'disconnected'} />
      </div>

      {/* Config section */}
      <div className="grid gap-4 lg:grid-cols-2 mb-6">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-3">Configuration</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Transport</dt>
              <dd className="font-mono">{server.transport_type}</dd>
            </div>
            {server.url && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">URL</dt>
                <dd className="font-mono text-xs truncate max-w-[250px]">{server.url}</dd>
              </div>
            )}
            {server.command && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Command</dt>
                <dd className="font-mono text-xs">{server.command}</dd>
              </div>
            )}
            {server.args && server.args.length > 0 && (
              <div className="flex justify-between">
                <dt className="text-muted-foreground">Args</dt>
                <dd className="font-mono text-xs truncate max-w-[250px]">{server.args.join(' ')}</dd>
              </div>
            )}
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Source</dt>
              <dd>{server.is_catalog ? 'Catalog' : 'Custom'}</dd>
            </div>
          </dl>
        </div>

        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Key className="h-4 w-4" />
            API Keys
          </h3>
          {keys && keys.length > 0 ? (
            <ul className="space-y-2">
              {keys.map((k) => (
                <li key={k.key_name} className="flex items-center justify-between text-sm">
                  <span className="font-mono">{k.key_name}</span>
                  <span className="text-muted-foreground text-xs">configured</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-muted-foreground">
              No API keys configured.{' '}
              <Link to="/keys" className="text-primary hover:underline">
                Manage keys
              </Link>
            </p>
          )}
        </div>
      </div>

      {/* Capabilities placeholder */}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <Wrench className="h-4 w-4" /> Tools
          </h3>
          <p className="text-sm text-muted-foreground">
            Connect to this server to discover available tools. Tools will appear here once the server is active.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <BookOpen className="h-4 w-4" /> Resources
          </h3>
          <p className="text-sm text-muted-foreground">
            Resources provided by this server will be listed here once connected.
          </p>
        </div>

        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-3 flex items-center gap-2">
            <MessageSquare className="h-4 w-4" /> Prompts
          </h3>
          <p className="text-sm text-muted-foreground">
            Prompts provided by this server will be listed here once connected.
          </p>
        </div>
      </div>
    </div>
  );
}
