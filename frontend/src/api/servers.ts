import { api } from './client';
import type { McpServer, ServerCreate, ServerUpdate } from '@/types/server';

export async function listServers(): Promise<McpServer[]> {
  const response = await api.get<McpServer[]>('/servers');
  return response.data;
}

export async function getServer(id: string): Promise<McpServer> {
  const response = await api.get<McpServer>(`/servers/${id}`);
  return response.data;
}

export async function createServer(data: ServerCreate): Promise<McpServer> {
  const response = await api.post<McpServer>('/servers', data);
  return response.data;
}

export async function updateServer(id: string, data: ServerUpdate): Promise<McpServer> {
  const response = await api.patch<McpServer>(`/servers/${id}`, data);
  return response.data;
}

export async function deleteServer(id: string): Promise<void> {
  await api.delete(`/servers/${id}`);
}

export async function toggleServer(id: string): Promise<{ is_enabled: boolean }> {
  const response = await api.post<{ is_enabled: boolean }>(`/servers/${id}/toggle`);
  return response.data;
}

export interface TestConnectionResult {
  status: 'ok' | 'error';
  server_name: string;
  transport_type: string;
  response_time_ms: number;
  tools_count: number;
  tools: string[];
  error?: string;
}

export async function testConnection(id: string): Promise<TestConnectionResult> {
  const response = await api.post<TestConnectionResult>(`/servers/${id}/test`);
  return response.data;
}
