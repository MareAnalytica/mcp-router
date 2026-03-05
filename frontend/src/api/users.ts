import { api } from './client';
import type { User } from '@/types/auth';

export async function listUsers(): Promise<User[]> {
  const response = await api.get<User[]>('/users');
  return response.data;
}

export async function updateUser(id: string, data: { role?: string; is_active?: boolean }): Promise<User> {
  const params = new URLSearchParams();
  if (data.role !== undefined) params.set('role', data.role);
  if (data.is_active !== undefined) params.set('is_active', String(data.is_active));
  const response = await api.patch<User>(`/users/${id}?${params.toString()}`);
  return response.data;
}

export async function deleteUser(id: string): Promise<void> {
  await api.delete(`/users/${id}`);
}
