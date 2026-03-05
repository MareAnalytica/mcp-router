import { api } from './client';
import type { ApiKey, ApiKeySet } from '@/types/keys';

export async function listKeys(serverId: string): Promise<ApiKey[]> {
  const response = await api.get<ApiKey[]>(`/servers/${serverId}/keys`);
  return response.data;
}

export async function setKeys(serverId: string, data: ApiKeySet): Promise<void> {
  await api.put(`/servers/${serverId}/keys`, data);
}

export async function deleteKey(serverId: string, keyName: string): Promise<void> {
  await api.delete(`/servers/${serverId}/keys/${keyName}`);
}
