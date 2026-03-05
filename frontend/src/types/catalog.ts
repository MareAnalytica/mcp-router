export interface CatalogEntry {
  id: string;
  name: string;
  description: string | null;
  transport_type: string;
  catalog_slug: string | null;
  icon_url: string | null;
  category: string | null;
  env_vars: Record<string, string> | null;
  trust_level: 'official' | 'verified' | 'community' | 'unverified' | null;
  source: string | null;
  repo_url: string | null;
  is_enabled_by_user: boolean;
}
