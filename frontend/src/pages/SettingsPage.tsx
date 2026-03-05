import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, updateUser, deleteUser } from '@/api/users';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { Copy, Check, Key } from 'lucide-react';
import { api } from '@/api/client';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="absolute top-3 right-3 rounded-md p-1.5 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
      title="Copy to clipboard"
    >
      {copied ? <Check className="h-4 w-4 text-success" /> : <Copy className="h-4 w-4" />}
    </button>
  );
}

export function SettingsPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const baseUrl = window.location.origin;

  // MCP Token state
  const [mcpToken, setMcpToken] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);

  // Generate MCP token mutation
  const generateTokenMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post('/api/auth/mcp-token');
      return response.data.access_token;
    },
    onSuccess: (token) => {
      setMcpToken(token);
      setShowToken(true);
    },
  });

  const handleGenerateToken = () => {
    generateTokenMutation.mutate();
  };

  const tokenCurlCmd = `curl -s -X POST ${baseUrl}/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{"email":"YOUR_EMAIL","password":"YOUR_PASSWORD"}' \\
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])"`;

  const sseJson = JSON.stringify(
    {
      mcpServers: {
        "mcp-router": {
          url: `${baseUrl}/api/mcp/sse`,
          headers: {
            Authorization: `Bearer ${mcpToken || 'YOUR_JWT_TOKEN'}`,
          },
        },
      },
    },
    null,
    2
  );

  const stdioJson = JSON.stringify(
    {
      mcpServers: {
        "mcp-router": {
          command: "npx",
          args: ["-y", "mcp-remote", `${baseUrl}/api/mcp/sse`],
          env: {
            MCP_HEADERS: JSON.stringify({
              Authorization: `Bearer ${mcpToken || 'YOUR_JWT_TOKEN'}`,
            }),
          },
        },
      },
    },
    null,
    2
  );

  const httpJson = JSON.stringify(
    {
      mcpServers: {
        "mcp-router": {
          type: "streamable-http",
          url: `${baseUrl}/api/mcp`,
          headers: {
            Authorization: `Bearer ${mcpToken || 'YOUR_JWT_TOKEN'}`,
          },
        },
      },
    },
    null,
    2
  );

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      <div className="space-y-6 max-w-2xl">
        {/* Profile */}
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-4">Profile</h3>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Username</dt>
              <dd className="font-medium">{user?.username}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Email</dt>
              <dd>{user?.email}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-muted-foreground">Role</dt>
              <dd className="capitalize">{user?.role}</dd>
            </div>
          </dl>
        </div>

        {/* Connection Info */}
        <div className="rounded-lg border border-border bg-card p-5">
          <h3 className="font-semibold mb-2">MCP Router Endpoint</h3>
          <p className="text-sm text-muted-foreground mb-4">
            Point your AI agent to this endpoint. Use the non-expiring token below for your MCP configuration.
          </p>

          <div className="space-y-4">
            {/* MCP Token Generator */}
            <div>
              <h4 className="text-sm font-medium mb-1.5 flex items-center gap-2">
                <Key className="h-4 w-4" />
                Generate Non-Expiring MCP Token
              </h4>
              <p className="text-xs text-muted-foreground mb-2">
                This token does not expire and can be used in your mcp.json configuration. You can generate a new token at any time.
              </p>
              
              {!mcpToken || !showToken ? (
                <button
                  onClick={handleGenerateToken}
                  disabled={generateTokenMutation.isPending}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {generateTokenMutation.isPending ? 'Generating...' : 'Generate MCP Token'}
                </button>
              ) : (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">Your MCP Access Token:</p>
                    <button
                      onClick={() => setShowToken(!showToken)}
                      className="text-xs text-muted-foreground hover:text-foreground underline"
                    >
                      Hide Token
                    </button>
                  </div>
                  <div className="relative">
                    <pre className="rounded-md bg-muted px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre break-all">
                      {mcpToken}
                    </pre>
                    <CopyButton text={mcpToken} />
                  </div>
                  <p className="text-xs text-muted-foreground">
                    ⚠️ Store this token securely. It won't be shown again unless you generate a new one.
                  </p>
                </div>
              )}
            </div>

            <hr className="border-border" />

            {/* Token retrieval command */}
            <div>
              <h4 className="text-sm font-medium mb-1.5">Alternative: Get temporary JWT token (expires in 15 minutes)</h4>
              <p className="text-xs text-muted-foreground mb-1.5">
                Run this command to get your access token (replace email and password with your credentials):
              </p>
              <div className="relative">
                <pre className="rounded-md bg-muted px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre">
                  {tokenCurlCmd}
                </pre>
                <CopyButton text={tokenCurlCmd} />
              </div>
              <p className="text-xs text-muted-foreground mt-1.5">
                Or use the login API directly: <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">POST {baseUrl}/api/auth/login</code> with
                body <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">{`{"email":"...","password":"..."}`}</code> — the response contains <code className="rounded bg-muted px-1 py-0.5 text-xs font-mono">access_token</code>.
              </p>
            </div>

            <hr className="border-border" />

            <h4 className="text-sm font-medium">2. Configure your MCP client</h4>
            <p className="text-xs text-muted-foreground mb-2">
              Paste one of the following JSON blocks into your MCP client config file. The token field will be automatically filled with your generated non-expiring token above.
            </p>

            {/* SSE config */}
            <div>
              <h4 className="text-sm font-medium mb-1.5">SSE Transport <span className="text-xs text-muted-foreground font-normal">(Claude Desktop, Cursor, Windsurf)</span></h4>
              <div className="relative">
                <pre className="rounded-md bg-muted px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre">
                  {sseJson}
                </pre>
                <CopyButton text={sseJson} />
              </div>
            </div>

            {/* STDIO via mcp-remote */}
            <div>
              <h4 className="text-sm font-medium mb-1.5">STDIO via mcp-remote <span className="text-xs text-muted-foreground font-normal">(clients that only support stdio)</span></h4>
              <div className="relative">
                <pre className="rounded-md bg-muted px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre">
                  {stdioJson}
                </pre>
                <CopyButton text={stdioJson} />
              </div>
            </div>

            {/* Streamable HTTP */}
            <div>
              <h4 className="text-sm font-medium mb-1.5">Streamable HTTP <span className="text-xs text-muted-foreground font-normal">(newer clients with HTTP transport)</span></h4>
              <div className="relative">
                <pre className="rounded-md bg-muted px-4 py-3 text-xs font-mono overflow-x-auto whitespace-pre">
                  {httpJson}
                </pre>
                <CopyButton text={httpJson} />
              </div>
            </div>
          </div>
        </div>

        {/* Admin Panel */}
        {isAdmin && <AdminPanel />}
      </div>
    </div>
  );
}

function AdminPanel() {
  const queryClient = useQueryClient();

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: string }) => updateUser(id, { role }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const deactivateMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  return (
    <div className="rounded-lg border border-border bg-card p-5">
      <h3 className="font-semibold mb-4">User Management (Admin)</h3>

      {isLoading ? (
        <LoadingSkeleton rows={3} />
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Username</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Email</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Role</th>
                <th className="px-3 py-2 text-left font-medium text-muted-foreground">Active</th>
                <th className="px-3 py-2 text-right font-medium text-muted-foreground">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {users?.map((u) => (
                <tr key={u.id}>
                  <td className="px-3 py-2 font-medium">{u.username}</td>
                  <td className="px-3 py-2 text-muted-foreground">{u.email}</td>
                  <td className="px-3 py-2">
                    <select
                      value={u.role}
                      onChange={(e) => roleMutation.mutate({ id: u.id, role: e.target.value })}
                      className="rounded-md border border-input bg-background px-2 py-1 text-xs"
                    >
                      <option value="user">user</option>
                      <option value="admin">admin</option>
                    </select>
                  </td>
                  <td className="px-3 py-2">
                    <span className={u.is_active ? 'text-success' : 'text-destructive'}>
                      {u.is_active ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => {
                        if (confirm(`Deactivate ${u.username}?`)) {
                          deactivateMutation.mutate(u.id);
                        }
                      }}
                      className="text-xs text-destructive hover:underline"
                    >
                      Deactivate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
