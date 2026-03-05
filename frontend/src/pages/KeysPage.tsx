import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Key, Plus, Trash2 } from 'lucide-react';
import { listServers } from '@/api/servers';
import { listKeys, setKeys, deleteKey } from '@/api/keys';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';

export function KeysPage() {
  const [selectedServer, setSelectedServer] = useState<string | null>(null);
  const [newKeyName, setNewKeyName] = useState('');
  const [newKeyValue, setNewKeyValue] = useState('');
  const queryClient = useQueryClient();

  const { data: servers, isLoading: serversLoading } = useQuery({
    queryKey: ['servers'],
    queryFn: listServers,
  });

  const { data: keys, isLoading: keysLoading } = useQuery({
    queryKey: ['keys', selectedServer],
    queryFn: () => listKeys(selectedServer!),
    enabled: !!selectedServer,
  });

  const addKeyMutation = useMutation({
    mutationFn: () =>
      setKeys(selectedServer!, { keys: [{ key_name: newKeyName, value: newKeyValue }] }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keys', selectedServer] });
      setNewKeyName('');
      setNewKeyValue('');
    },
  });

  const deleteKeyMutation = useMutation({
    mutationFn: (keyName: string) => deleteKey(selectedServer!, keyName),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['keys', selectedServer] }),
  });

  if (serversLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">API Key Vault</h1>
        <LoadingSkeleton rows={4} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">API Key Vault</h1>
        <p className="text-muted-foreground mt-1">
          Manage API keys for your upstream MCP servers. Keys are encrypted at rest.
        </p>
      </div>

      {!servers || servers.length === 0 ? (
        <EmptyState
          icon={Key}
          title="No servers to configure"
          description="Add MCP servers first, then configure their API keys here."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          {/* Server list */}
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-4 py-3">
              <h3 className="font-semibold text-sm">Select Server</h3>
            </div>
            <div className="divide-y divide-border">
              {servers.map((s) => (
                <button
                  key={s.id}
                  onClick={() => setSelectedServer(s.id)}
                  className={`w-full px-4 py-3 text-left text-sm transition-colors ${
                    selectedServer === s.id
                      ? 'bg-primary/10 text-primary font-medium'
                      : 'text-foreground hover:bg-accent'
                  }`}
                >
                  {s.name}
                </button>
              ))}
            </div>
          </div>

          {/* Keys panel */}
          <div className="lg:col-span-2">
            {!selectedServer ? (
              <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
                Select a server to manage its API keys
              </div>
            ) : (
              <div className="rounded-lg border border-border bg-card">
                <div className="border-b border-border px-4 py-3">
                  <h3 className="font-semibold text-sm">
                    Keys for {servers.find((s) => s.id === selectedServer)?.name}
                  </h3>
                </div>

                {/* Existing keys */}
                <div className="p-4">
                  {keysLoading ? (
                    <LoadingSkeleton rows={2} />
                  ) : keys && keys.length > 0 ? (
                    <div className="space-y-2 mb-4">
                      {keys.map((k) => (
                        <div
                          key={k.key_name}
                          className="flex items-center justify-between rounded-md border border-border px-3 py-2"
                        >
                          <div>
                            <span className="font-mono text-sm">{k.key_name}</span>
                            <span className="ml-2 text-xs text-muted-foreground">
                              ••••••••
                            </span>
                          </div>
                          <button
                            onClick={() => deleteKeyMutation.mutate(k.key_name)}
                            className="rounded-md p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive transition-colors"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground mb-4">No keys configured yet.</p>
                  )}

                  {/* Add key form */}
                  <div className="border-t border-border pt-4">
                    <h4 className="text-sm font-medium mb-3 flex items-center gap-1.5">
                      <Plus className="h-4 w-4" /> Add Key
                    </h4>
                    <div className="flex gap-2">
                      <input
                        value={newKeyName}
                        onChange={(e) => setNewKeyName(e.target.value)}
                        placeholder="Key name (e.g. GITHUB_TOKEN)"
                        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm font-mono focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
                      />
                      <input
                        value={newKeyValue}
                        onChange={(e) => setNewKeyValue(e.target.value)}
                        placeholder="Value"
                        type="password"
                        className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
                      />
                      <button
                        onClick={() => addKeyMutation.mutate()}
                        disabled={!newKeyName || !newKeyValue || addKeyMutation.isPending}
                        className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                      >
                        Save
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
