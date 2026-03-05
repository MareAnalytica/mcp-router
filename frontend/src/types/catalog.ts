export interface CatalogEntry {
  id: string;
  name: string;
  description: string | null;
  transport_type: string;
  catalog_slug: string | null;
  icon_url: string | null;
  category: string | null;
  env_vars: Record<string, string> | null;
  is_enabled_by_user: boolean;
}
