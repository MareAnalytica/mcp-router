import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router';
import { Plus, Server, Trash2 } from 'lucide-react';
import { listServers, createServer, deleteServer, toggleServer } from '@/api/servers';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { StatusBadge } from '@/components/shared/StatusBadge';
import type { ServerCreate, TransportType } from '@/types/server';

function AddServerDialog({
  open,
  onClose,
}: {
  open: boolean;
  onClose: () => void;
}) {
  const queryClient = useQueryClient();
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [transportType, setTransportType] = useState<TransportType>('stdio');
  const [url, setUrl] = useState('');
  const [command, setCommand] = useState('');
  const [args, setArgs] = useState('');
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: createServer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['servers'] });
      onClose();
      setName('');
      setDescription('');
      setUrl('');
      setCommand('');
      setArgs('');
      setError('');
    },
    onError: () => setError('Failed to add server'),
  });

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: ServerCreate = {
      name,
      description: description || undefined,
      transport_type: transportType,
    };
    if (transportType === 'stdio') {
      data.command = command;
      data.args = args ? args.split(' ').filter(Boolean) : undefined;
    } else {
      data.url = url;
    }
    mutation.mutate(data);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div
        className="w-full max-w-lg rounded-lg border border-border bg-card p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4">Add MCP Server</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</div>
          )}

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="My MCP Server"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Description</label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
              placeholder="Optional description"
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Transport</label>
            <select
              value={transportType}
              onChange={(e) => setTransportType(e.target.value as TransportType)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
            >
              <option value="stdio">STDIO</option>
              <option value="sse">SSE</option>
              <option value="streamable_http">Streamable HTTP</option>
            </select>
          </div>

          {transportType === 'stdio' ? (
            <>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Command</label>
                <input
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="npx"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Arguments</label>
                <input
                  value={args}
                  onChange={(e) => setArgs(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
                  placeholder="-y @modelcontextprotocol/server-memory"
                />
              </div>
            </>
          ) : (
            <div className="space-y-1.5">
              <label className="text-sm font-medium">URL</label>
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                required
                type="url"
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
                placeholder="https://mcp-server.example.com/sse"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-border px-4 py-2 text-sm font-medium hover:bg-accent transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {mutation.isPending ? 'Adding...' : 'Add Server'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function ServersPage() {
  const [showAdd, setShowAdd] = useState(false);
  const queryClient = useQueryClient();

  const { data: servers, isLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: listServers,
  });

  const toggleMutation = useMutation({
    mutationFn: toggleServer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['servers'] }),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteServer,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['servers'] }),
  });

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">MCP Servers</h1>
        <LoadingSkeleton rows={5} />
      </div>
    );
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">MCP Servers</h1>
        <button
          onClick={() => setShowAdd(true)}
          className="inline-flex items-center gap-1.5 rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Add Server
        </button>
      </div>

      {!servers || servers.length === 0 ? (
        <EmptyState
          icon={Server}
          title="No servers configured"
          description="Add an MCP server manually or browse the catalog to get started."
          action={
            <div className="flex gap-2">
              <button
                onClick={() => setShowAdd(true)}
                className="rounded-md bg-primary px-3 py-1.5 text-sm font-medium text-primary-foreground hover:bg-primary/90 transition-colors"
              >
                Add Server
              </button>
              <Link
                to="/catalog"
                className="rounded-md border border-border px-3 py-1.5 text-sm font-medium hover:bg-accent transition-colors"
              >
                Browse Catalog
              </Link>
            </div>
          }
        />
      ) : (
        <div className="rounded-lg border border-border bg-card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Transport</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Source</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {servers.map((server) => (
                  <tr key={server.id} className="hover:bg-accent/50 transition-colors">
                    <td className="px-4 py-3">
                      <Link to={`/servers/${server.id}`} className="font-medium text-foreground hover:text-primary">
                        {server.name}
                      </Link>
                      {server.description && (
                        <p className="text-xs text-muted-foreground mt-0.5 truncate max-w-xs">
                          {server.description}
                        </p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">
                        {server.transport_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={server.is_enabled ? 'connected' : 'disconnected'} />
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {server.is_catalog ? 'Catalog' : 'Custom'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => toggleMutation.mutate(server.id)}
                          className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                            server.is_enabled
                              ? 'bg-success/15 text-success hover:bg-success/25'
                              : 'bg-muted text-muted-foreground hover:bg-muted/80'
                          }`}
                        >
                          {server.is_enabled ? 'Enabled' : 'Disabled'}
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Delete server "${server.name}"?`)) {
                              deleteMutation.mutate(server.id);
                            }
                          }}
                          className="rounded-md p-1.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                          title="Delete"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <AddServerDialog open={showAdd} onClose={() => setShowAdd(false)} />
    </div>
  );
}
