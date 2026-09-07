import { PageHeader } from '@shared/components/PageHeader';
import { MetricCard } from '@shared/components/MetricCard';
import { EmptyState } from '@shared/ui';
import { useMetricFilters } from '@shared/hooks/use-metric-filters';
import { hasActiveFilters } from '@shared/lib/metric-filters';

/**
 * Home route. Wires the URL-synced filters; the KPI values, charts and drill-down
 * come from `dashboard/api` + `dashboard/model` (issues I5.9–I5.14).
 */
export function DashboardPage() {
  const { filters, reset } = useMetricFilters();

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Activité, tokens, outils et erreurs sur les données réellement importées."
        actions={
          hasActiveFilters(filters) ? (
            <button type="button" onClick={reset} className="text-sm text-primary hover:underline">
              Réinitialiser les filtres
            </button>
          ) : undefined
        }
      />

      {/* <FilterBar /> — I5.13 */}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Sessions" value="—" definitionId="sessions" />
        <MetricCard label="Tokens" value="—" definitionId="tokens-consommes" />
        <MetricCard label="Coût estimé" value="—" definitionId="cout-estime" />
        <MetricCard label="Taux d'erreur" value="—" definitionId="taux-d-erreur" />
      </div>

      <div className="mt-4">
        <EmptyState
          title="Visualisations à venir"
          description="Série temporelle, répartition des outils, distribution des durées (I5.10–I5.12)."
        />
      </div>
    </>
  );
}
