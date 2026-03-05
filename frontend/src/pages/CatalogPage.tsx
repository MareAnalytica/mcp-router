import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, Store, Check, Plus } from 'lucide-react';
import { listCatalog, enableCatalogEntry } from '@/api/catalog';
import { LoadingSkeleton } from '@/components/shared/LoadingSkeleton';
import { EmptyState } from '@/components/shared/EmptyState';
import { cn } from '@/lib/utils';

const categories = [
  { value: '', label: 'All' },
  { value: 'developer-tools', label: 'Developer Tools' },
  { value: 'utilities', label: 'Utilities' },
  { value: 'search', label: 'Search' },
  { value: 'browser', label: 'Browser' },
  { value: 'communication', label: 'Communication' },
  { value: 'productivity', label: 'Productivity' },
  { value: 'databases', label: 'Databases' },
];

export function CatalogPage() {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const queryClient = useQueryClient();

  const { data: catalog, isLoading } = useQuery({
    queryKey: ['catalog', search, category],
    queryFn: () => listCatalog(search || undefined, category || undefined),
  });

  const enableMutation = useMutation({
    mutationFn: enableCatalogEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['catalog'] });
      queryClient.invalidateQueries({ queryKey: ['servers'] });
    },
  });

  if (isLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold mb-6">MCP Server Catalog</h1>
        <LoadingSkeleton rows={6} />
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold">MCP Server Catalog</h1>
        <p className="text-muted-foreground mt-1">Browse and enable popular MCP servers with one click.</p>
      </div>

      {/* Search + Filters */}
      <div className="mb-6 space-y-3">
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search servers..."
            className="w-full rounded-md border border-input bg-background pl-9 pr-3 py-2 text-sm focus:border-ring focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {categories.map((cat) => (
            <button
              key={cat.value}
              onClick={() => setCategory(cat.value)}
              className={cn(
                'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                category === cat.value
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground hover:bg-accent'
              )}
            >
              {cat.label}
            </button>
          ))}
        </div>
      </div>

      {/* Grid */}
      {!catalog || catalog.length === 0 ? (
        <EmptyState
          icon={Store}
          title="No servers found"
          description="Try a different search term or category filter."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {catalog.map((entry) => (
            <div
              key={entry.id}
              className="rounded-lg border border-border bg-card p-5 flex flex-col"
            >
              <div className="flex items-start gap-3 mb-3">
                <div className="h-10 w-10 rounded-md bg-primary/10 flex items-center justify-center text-primary font-bold text-lg shrink-0">
                  {entry.name.charAt(0)}
                </div>
                <div className="min-w-0">
                  <h3 className="font-semibold text-card-foreground">{entry.name}</h3>
                  {entry.category && (
                    <span className="text-xs text-muted-foreground">{entry.category}</span>
                  )}
                </div>
              </div>

              <p className="text-sm text-muted-foreground mb-4 flex-1">
                {entry.description || 'No description available.'}
              </p>

              <div className="flex items-center justify-between mt-auto">
                <span className="rounded bg-muted px-1.5 py-0.5 text-xs font-mono">
                  {entry.transport_type}
                </span>

                {entry.is_enabled_by_user ? (
                  <span className="inline-flex items-center gap-1 text-xs font-medium text-success">
                    <Check className="h-3.5 w-3.5" />
                    Enabled
                  </span>
                ) : (
                  <button
                    onClick={() => {
                      if (entry.catalog_slug) {
                        enableMutation.mutate(entry.catalog_slug);
                      }
                    }}
                    disabled={enableMutation.isPending}
                    className="inline-flex items-center gap-1 rounded-md bg-primary px-2.5 py-1 text-xs font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-colors"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    Add to Router
                  </button>
                )}
              </div>

              {entry.env_vars && Object.keys(entry.env_vars).length > 0 && (
                <div className="mt-3 pt-3 border-t border-border">
                  <p className="text-xs text-muted-foreground mb-1">Required API keys:</p>
                  <div className="flex flex-wrap gap-1">
                    {Object.keys(entry.env_vars).map((key) => (
                      <span key={key} className="rounded bg-warning/10 px-1.5 py-0.5 text-xs font-mono text-warning">
                        {key}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
