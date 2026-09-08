import { useState } from "react";

import { useMetricFilters } from "@shared/hooks/use-metric-filters";
import { ApiError } from "@shared/api/api-error";
import type { ProblemDetails } from "@shared/api/types";
import { Button, ChartFrame, StackedBarChart, TimeSeriesChart } from "@shared/ui";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import { FilterBar } from "@shared/components/filters";
import { IndicatorCard } from "./IndicatorCard";
import { useIndicatorsQuery, useTimeseriesQuery, useToolUsageQuery } from "../api/dashboard.queries";
import type { TimeseriesMetric } from "../api/dashboard.contracts";
import { METRIC_DEFINITIONS } from "../types";

const ACTIVITY_METRICS: { value: TimeseriesMetric; label: string }[] = [
  { value: "sessions", label: "Sessions" },
  { value: "tokens", label: "Tokens" },
];

function toProblemDetails(error: unknown, fallbackDetail: string): ProblemDetails {
  if (error instanceof ApiError && error.problem) {
    return {
      type: error.problem.type,
      title: error.problem.title,
      status: error.problem.status,
      detail: error.problem.detail,
      errors: error.problem.errors?.map((e) => ({ field: e.field ?? "", message: e.message })),
    };
  }
  return { title: "Erreur réseau", status: 500, detail: fallbackDetail };
}

export const DashboardScreen: React.FC = () => {
  const { filters } = useMetricFilters();
  const [activityMetric, setActivityMetric] = useState<TimeseriesMetric>("sessions");

  const indicators = useIndicatorsQuery(filters);
  const timeseries = useTimeseriesQuery(filters, activityMetric, "day");
  const toolUsage = useToolUsageQuery(filters);

  const points = timeseries.data?.points ?? [];
  const activeMetricLabel =
    ACTIVITY_METRICS.find((m) => m.value === activityMetric)?.label ?? activityMetric;

  const toolUsageData = (toolUsage.data ?? []).map((item) => ({
    category: item.tool_name,
    success: item.n_calls - item.n_errors,
    error: item.n_errors,
  }));

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tableau de bord</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Vue globale des indicateurs de performance et d'utilisation des agents.
        </p>
      </div>

      <FilterBar />

      <ApiErrorBanner
        error={
          indicators.error
            ? toProblemDetails(indicators.error, "Impossible de charger les métriques du tableau de bord.")
            : null
        }
      />

      {indicators.isLoading ? (
        <div className="p-8 text-center text-sm text-slate-500">Chargement des indicateurs...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <IndicatorCard
            definition={METRIC_DEFINITIONS.sessions!}
            value={indicators.data?.session_count ?? 0}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.tokens!}
            value={indicators.data?.total_tokens ?? null}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.cost!}
            value={indicators.data?.total_cost_usd ?? null}
            formatter={(v) => `$${v.toFixed(2)}`}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.errorRate!}
            value={indicators.data?.error_rate != null ? indicators.data.error_rate * 100 : null}
            formatter={(v) => `${v.toFixed(1)} %`}
          />
        </div>
      )}

      <ApiErrorBanner
        error={
          timeseries.error
            ? toProblemDetails(timeseries.error, "Impossible de charger l'activité.")
            : null
        }
      />

      <ChartFrame
        title="Activité"
        isEmpty={!timeseries.isLoading && points.length === 0}
        emptyDescription="Aucune session ne correspond aux filtres actifs."
        actions={
          <div className="flex gap-1">
            {ACTIVITY_METRICS.map((m) => (
              <Button
                key={m.value}
                type="button"
                size="sm"
                variant={activityMetric === m.value ? "primary" : "secondary"}
                onClick={() => setActivityMetric(m.value)}
                aria-pressed={activityMetric === m.value}
              >
                {m.label}
              </Button>
            ))}
          </div>
        }
      >
        {timeseries.isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Chargement de l'activité...</div>
        ) : (
          <TimeSeriesChart data={points} valueLabel={activeMetricLabel} />
        )}
      </ChartFrame>

      <ApiErrorBanner
        error={
          toolUsage.error
            ? toProblemDetails(toolUsage.error, "Impossible de charger la répartition des outils.")
            : null
        }
      />

      <ChartFrame
        title="Répartition des outils"
        isEmpty={!toolUsage.isLoading && toolUsageData.length === 0}
        emptyDescription="Aucun appel d'outil ne correspond aux filtres actifs."
      >
        {toolUsage.isLoading ? (
          <div className="p-8 text-center text-sm text-slate-500">Chargement des outils...</div>
        ) : (
          <StackedBarChart
            data={toolUsageData}
            series={[
              { key: "success", label: "Réussis" },
              { key: "error", label: "Erreurs", color: "hsl(var(--danger))" },
            ]}
          />
        )}
      </ChartFrame>
    </div>
  );
};

