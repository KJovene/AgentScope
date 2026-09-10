import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";

import { useMetricFilters } from "@shared/hooks/use-metric-filters";
import { ApiError } from "@shared/api/api-error";
import type { ProblemDetails } from "@shared/api/types";
import {
  Button,
  ChartFrame,
  ChartSkeleton,
  CyberScope,
  DistributionChart,
  Skeleton,
  StackedBarChart,
  TimeSeriesChart,
} from "@shared/ui";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import { FilterBar } from "@shared/components/filters";
import { useSessionsQuery } from "@shared/api/sessions.queries";
import { IndicatorCard } from "./IndicatorCard";
import { useIndicatorsQuery, useTimeseriesQuery, useToolUsageQuery } from "../api/dashboard.queries";
import type { TimeseriesMetric } from "../api/dashboard.contracts";
import type { TimeSeriesPoint } from "@shared/ui";
import { dayDrillDownFilters } from "../model/drilldown";
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
  const navigate = useNavigate();
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

  const sessions = useSessionsQuery({ ...filters, limit: 200, offset: 0 });
  const sessionItems = sessions.data?.items ?? [];
  const durations = sessionItems
    .map((s) => s.duration_ms)
    .filter((d): d is number => d != null);
  const missingTimingCount = sessionItems.length - durations.length;

  const status = indicators.isError
    ? { label: "Hors ligne", tone: "text-danger", dot: "bg-danger" }
    : indicators.isLoading
      ? { label: "Synchronisation", tone: "text-warning", dot: "bg-warning animate-pulse-neon" }
      : { label: "En ligne", tone: "text-neon-green", dot: "bg-neon-green animate-pulse-neon" };

  // Drill-down (I5.14) : un point du graphe d'activité -> sessions de ce jour,
  // filtres actifs conservés.
  function handleActivityPointClick(point: TimeSeriesPoint) {
    void navigate({
      to: "/sessions",
      search: dayDrillDownFilters(filters, point),
    });
  }

  return (
    <div className="stagger space-y-6">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <header className="hero-cyber relative flex flex-wrap items-end justify-between gap-4 overflow-hidden p-6">
        <CyberScope className="pointer-events-none absolute -right-8 -top-10 h-48 w-48 opacity-40 sm:opacity-60" />
        <div className="relative">
          <p className="text-xs uppercase tracking-[0.3em] text-foreground-muted">AgentScope // Métriques</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight text-gradient">Tableau de bord</h1>
          <p className="mt-2 max-w-xl text-sm text-foreground-muted">
            Vue globale des indicateurs de performance et d'utilisation des agents.
          </p>
        </div>
        <div className="relative border border-neon-violet/40 bg-surface/70 px-4 py-2 backdrop-blur-sm">
          <p className="text-[10px] uppercase tracking-widest text-foreground-muted">État du flux</p>
          <p className={`mt-1 flex items-center gap-2 text-sm font-bold uppercase tracking-wider ${status.tone}`}>
            <span aria-hidden="true" className={`inline-block h-2 w-2 ${status.dot}`} />
            {status.label}
          </p>
        </div>
      </header>

      <div className="sticky top-3 z-10">
        <FilterBar />
      </div>

      <ApiErrorBanner
        error={
          indicators.error
            ? toProblemDetails(indicators.error, "Impossible de charger les métriques du tableau de bord.")
            : null
        }
      />

      {indicators.isLoading ? (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[104px]" />
          ))}
        </div>
      ) : (
        <div className="stagger grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <IndicatorCard
            definition={METRIC_DEFINITIONS.sessions!}
            value={indicators.data?.session_count ?? null}
            accent="cyan"
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.tokens!}
            value={indicators.data?.total_tokens ?? null}
            accent="violet"
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.cost!}
            value={indicators.data?.total_cost_usd ?? null}
            formatter={(v) => `$${v.toFixed(2)}`}
            accent="cyan"
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.errorRate!}
            value={indicators.data?.error_rate != null ? indicators.data.error_rate * 100 : null}
            formatter={(v) => `${v.toFixed(1)} %`}
            accent="violet"
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
      <ApiErrorBanner
        error={
          toolUsage.error
            ? toProblemDetails(toolUsage.error, "Impossible de charger la répartition des outils.")
            : null
        }
      />
      <ApiErrorBanner
        error={
          sessions.error
            ? toProblemDetails(sessions.error, "Impossible de charger la durée des sessions.")
            : null
        }
      />

      <div className="grid gap-5 xl:grid-cols-2">
        <div className="xl:col-span-2">
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
              <ChartSkeleton />
            ) : (
              <TimeSeriesChart
                data={points}
                valueLabel={activeMetricLabel}
                onPointClick={handleActivityPointClick}
              />
            )}
          </ChartFrame>
        </div>

        <ChartFrame
          title="Répartition des outils"
          isEmpty={!toolUsage.isLoading && toolUsageData.length === 0}
          emptyDescription="Aucun appel d'outil ne correspond aux filtres actifs."
        >
          {toolUsage.isLoading ? (
            <ChartSkeleton />
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

        <ChartFrame
          title="Distribution de la durée des sessions"
          isEmpty={!sessions.isLoading && durations.length === 0}
          emptyDescription="Aucune session avec horodatage ne correspond aux filtres actifs."
        >
          {sessions.isLoading ? (
            <ChartSkeleton />
          ) : (
            <>
              {missingTimingCount > 0 && (
                <p className="mb-2 text-xs text-foreground-muted">
                  {missingTimingCount} session(s) sans horodatage, exclue(s) de la distribution.
                </p>
              )}
              <DistributionChart values={durations} />
            </>
          )}
        </ChartFrame>
      </div>
    </div>
  );
};
