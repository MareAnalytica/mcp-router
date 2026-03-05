import { api } from './client';
import type { HealthCheck } from '@/types/health';

export async function listServerHealth(): Promise<HealthCheck[]> {
  const response = await api.get<HealthCheck[]>('/health/servers');
  return response.data;
}
