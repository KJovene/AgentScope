import { useMetricFilters } from '@shared/hooks/use-metric-filters';
import { hasActiveFilters, type MetricFilters } from '@shared/lib/metric-filters';
import { Button, Card } from '@shared/ui';

import { AgentFilter } from './AgentFilter';
import { DateRangeFilter } from './DateRangeFilter';
import { ModelFilter } from './ModelFilter';
import { SourceFilter } from './SourceFilter';

function activeFilterCount(filters: MetricFilters): number {
  return (
    filters.sources.length +
    filters.agents.length +
    filters.models.length +
    (filters.from ? 1 : 0) +
    (filters.to ? 1 : 0)
  );
}

/**
 * Layout wrapper for the dashboard's global filters. Reads/writes
 * `useMetricFilters()` directly — every filter control here is a pure
 * presentational component with no local copy of the filter state, so a
 * change here immediately re-fetches indicators + every chart (I5.13).
 */
export function FilterBar() {
  const { filters, setFilters, reset } = useMetricFilters();
  const count = activeFilterCount(filters);

  return (
    <Card className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <h2 className="cyber-title text-neon-cyan">Filtres{count > 0 ? ` (${count})` : ''}</h2>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={reset}
          disabled={!hasActiveFilters(filters)}
        >
          Réinitialiser
        </Button>
      </div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <div className="min-w-0">
          <SourceFilter values={filters.sources} onChange={(sources) => setFilters({ sources })} />
        </div>
        <div className="min-w-0">
          <AgentFilter values={filters.agents} onChange={(agents) => setFilters({ agents })} />
        </div>
        <div className="min-w-0">
          <ModelFilter values={filters.models} onChange={(models) => setFilters({ models })} />
        </div>
        <div className="min-w-0">
          <DateRangeFilter
            from={filters.from}
            to={filters.to}
            onChange={(range) => setFilters(range)}
          />
        </div>
      </div>
    </Card>
  );
}
