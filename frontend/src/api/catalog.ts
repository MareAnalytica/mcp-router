import { api } from './client';
import type { CatalogEntry } from '@/types/catalog';

export async function listCatalog(search?: string, category?: string): Promise<CatalogEntry[]> {
  const params = new URLSearchParams();
  if (search) params.set('search', search);
  if (category) params.set('category', category);
  const response = await api.get<CatalogEntry[]>(`/catalog?${params.toString()}`);
  return response.data;
}

export async function getCatalogEntry(slug: string): Promise<CatalogEntry> {
  const response = await api.get<CatalogEntry>(`/catalog/${slug}`);
  return response.data;
}

export async function enableCatalogEntry(slug: string): Promise<{
  server_id: string;
  required_env_vars: Record<string, string>;
  message: string;
}> {
  const response = await api.post(`/catalog/${slug}/enable`);
  return response.data;
}
