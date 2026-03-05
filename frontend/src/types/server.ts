export type TransportType = 'sse' | 'streamable_http' | 'stdio';

export interface McpServer {
  id: string;
  name: string;
  description: string | null;
  transport_type: TransportType;
  url: string | null;
  command: string | null;
  args: string[] | null;
  env_vars: Record<string, string> | null;
  headers: Record<string, string> | null;
  is_catalog: boolean;
  catalog_slug: string | null;
  icon_url: string | null;
  category: string | null;
  is_enabled: boolean | null;
  created_at: string;
}

export interface ServerCreate {
  name: string;
  description?: string;
  transport_type: TransportType;
  url?: string;
  command?: string;
  args?: string[];
  env_vars?: Record<string, string>;
  headers?: Record<string, string>;
}

export interface ServerUpdate {
  name?: string;
  description?: string;
  transport_type?: TransportType;
  url?: string;
  command?: string;
  args?: string[];
  env_vars?: Record<string, string>;
  headers?: Record<string, string>;
}
