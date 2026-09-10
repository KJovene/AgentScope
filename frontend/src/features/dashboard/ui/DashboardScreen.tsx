import { useState } from "react";
import { useNavigate } from "@tanstack/react-router";

import { useMetricFilters } from "@shared/hooks/use-metric-filters";
import { ApiError } from "@shared/api/api-error";
import type { ProblemDetails } from "@shared/api/types";
import {
  BreakdownBarChart,
  Button,
  CHART_COLORS,
  CHART_SERIES_COLORS,
  ChartFrame,
  ChartSkeleton,
  CyberScope,
  DistributionChart,
  ProportionBar,
  Skeleton,
  TimeSeriesChart,
} from "@shared/ui";
import { ApiErrorBanner } from "@shared/components/ApiErrorBanner";
import { FilterBar } from "@shared/components/filters";
import { useSessionsQuery } from "@shared/api/sessions.queries";
import { formatDuration, formatNumber, formatPercent, formatTokens, formatUsd } from "@shared/lib/format";
import { DataQualityPanel } from "@features/data-quality";
import { IndicatorCard } from "./IndicatorCard";
import { ToolUsagePanel } from "./ToolUsagePanel";
import { TopSessionsTable } from "./TopSessionsTable";
import {
  useIndicatorsQuery,
  usePreviousIndicatorsQuery,
  useTimeseriesQuery,
  useToolUsageQuery,
} from "../api/dashboard.queries";
import type { TimeseriesMetric } from "../api/dashboard.contracts";
import type { TimeSeriesPoint } from "@shared/ui";
import { dayDrillDownFilters } from "../model/drilldown";
import { breakdownBy, topSessionsByCost } from "../model/breakdown";
import {
  previousPeriod,
  relativeDelta,
  resolveCurrentPeriod,
} from "../model/period-comparison";
import { METRIC_DEFINITIONS } from "../types";

const ACTIVITY_METRICS: { value: TimeseriesMetric; label: string }[] = [
  { value: "sessions", label: "Sessions" },
  { value: "tokens", label: "Tokens" },
  { value: "model_calls", label: "Appels modèles" },
  { value: "tool_calls", label: "Appels outils" },
  { value: "cost", label: "Coût" },
  { value: "errors", label: "Erreurs" },
];

const SESSION_PAGE_SIZE = 200;

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

/** Safe ratio: null unless both operands are present and the denominator is non-zero. */
function ratio(numerator: number | null | undefined, denominator: number | null | undefined) {
  if (numerator == null || denominator == null || denominator === 0) return null;
  return numerator / denominator;
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

  // Period comparison (lot 3): an explicit date filter wins, otherwise the window
  // is inferred from the span the activity series covers.
  const currentPeriod = resolveCurrentPeriod(filters, points);
  const comparisonPeriod = currentPeriod ? previousPeriod(currentPeriod) : null;
  const previousIndicators = usePreviousIndicatorsQuery(filters, comparisonPeriod);

  const current = indicators.data;
  const previous = previousIndicators.data;
  const delta = (pick: (d: NonNullable<typeof current>) => number | null | undefined) =>
    current && previous ? relativeDelta(pick(current), pick(previous)) : null;
  // An empty preceding window is a valid answer, not a baseline — say so rather
  // than claiming variations that no card can show.
  const hasComparisonData = (previous?.session_count ?? 0) > 0;

  const totalCalls = (current?.model_call_count ?? 0) + (current?.tool_call_count ?? 0);

  const toolUsageItems = toolUsage.data ?? [];

  const sessions = useSessionsQuery({ ...filters, limit: SESSION_PAGE_SIZE, offset: 0 });
  const sessionItems = sessions.data?.items ?? [];
  const durations = sessionItems
    .map((s) => s.duration_ms)
    .filter((d): d is number => d != null);
  const missingTimingCount = sessionItems.length - durations.length;

  // Breakdowns and the top-cost table reuse the page fetched for the duration
  // distribution — no extra request.
  const sessionsByAgent = breakdownBy(sessionItems, "agent_name");
  const costBySource = breakdownBy(sessionItems, "source_name", (s) => s.total_cost_usd);
  const topSessions = topSessionsByCost(sessionItems);
  const isPartialPage = sessions.data != null && sessions.data.total > sessionItems.length;

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
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-[132px]" />
          ))}
        </div>
      ) : (
        <>
          <div className="stagger relative z-20 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <IndicatorCard
              definition={METRIC_DEFINITIONS.sessions!}
              value={current?.session_count ?? null}
              accent="cyan"
              caption={
                current?.session_count
                  ? `${formatNumber(Math.round(totalCalls / current.session_count))} appels / session`
                  : undefined
              }
              delta={delta((d) => d.session_count)}
            />
            <IndicatorCard
              definition={METRIC_DEFINITIONS.tokens!}
              value={current?.total_tokens ?? null}
              formatter={formatTokens}
              accent="violet"
              caption={
                ratio(current?.total_tokens, current?.session_count) != null
                  ? `${formatTokens(Math.round(ratio(current?.total_tokens, current?.session_count)!))} / session`
                  : undefined
              }
              delta={delta((d) => d.total_tokens)}
            >
              {current?.prompt_tokens != null && current?.completion_tokens != null && (
                <ProportionBar
                  segments={[
                    { key: "prompt", label: "Prompt", value: current.prompt_tokens },
                    { key: "completion", label: "Complétion", value: current.completion_tokens },
                  ]}
                />
              )}
            </IndicatorCard>
            <IndicatorCard
              definition={METRIC_DEFINITIONS.cost!}
              value={current?.total_cost_usd ?? null}
              formatter={formatUsd}
              accent="cyan"
              badge={current?.cost_is_estimated ? "Estimé" : undefined}
              caption={
                ratio(current?.total_cost_usd, current?.session_count) != null
                  ? `${formatUsd(ratio(current?.total_cost_usd, current?.session_count))} / session`
                  : undefined
              }
              delta={delta((d) => d.total_cost_usd)}
              higherIsBetter={false}
            />
            <IndicatorCard
              definition={METRIC_DEFINITIONS.errorRate!}
              value={current?.error_rate != null ? current.error_rate * 100 : null}
              formatter={(v) => `${v.toFixed(1)} %`}
              accent="violet"
              caption={
                current
                  ? `${formatNumber(current.error_count)} erreurs sur ${formatNumber(totalCalls)} appels`
                  : undefined
              }
              delta={delta((d) => d.error_rate)}
              higherIsBetter={false}
            />

            <IndicatorCard
              definition={METRIC_DEFINITIONS.modelCalls!}
              value={current?.model_call_count ?? null}
              formatter={formatNumber}
              accent="cyan"
              caption={
                totalCalls > 0
                  ? `${formatPercent(ratio(current?.model_call_count, totalCalls))} des appels`
                  : undefined
              }
              delta={delta((d) => d.model_call_count)}
            />
            <IndicatorCard
              definition={METRIC_DEFINITIONS.toolCalls!}
              value={current?.tool_call_count ?? null}
              formatter={formatNumber}
              accent="violet"
              caption={
                totalCalls > 0
                  ? `${formatPercent(ratio(current?.tool_call_count, totalCalls))} des appels`
                  : undefined
              }
              delta={delta((d) => d.tool_call_count)}
            />
            <IndicatorCard
              definition={METRIC_DEFINITIONS.medianDuration!}
              value={current?.median_session_duration_ms ?? null}
              formatter={formatDuration}
              accent="cyan"
              caption={
                missingTimingCount > 0
                  ? `${formatNumber(missingTimingCount)} session(s) sans horodatage`
                  : undefined
              }
              delta={delta((d) => d.median_session_duration_ms)}
              higherIsBetter={false}
            />
            <IndicatorCard
              definition={METRIC_DEFINITIONS.cacheHit!}
              value={current?.cache_hit_ratio != null ? current.cache_hit_ratio * 100 : null}
              formatter={(v) => `${v.toFixed(1)} %`}
              accent="violet"
              caption={
                current?.cached_tokens != null
                  ? `${formatTokens(current.cached_tokens)} tokens en cache`
                  : undefined
              }
              delta={delta((d) => d.cache_hit_ratio)}
              higherIsBetter
            />
          </div>

          {comparisonPeriod && previousIndicators.isSuccess && (
            <p className="text-[11px] text-foreground-muted">
              {hasComparisonData
                ? "Variations calculées face à la période précédente de même durée, du "
                : "Aucune donnée sur la période précédente de même durée, du "}
              {new Date(comparisonPeriod.from).toLocaleDateString("fr-FR")} au{" "}
              {new Date(comparisonPeriod.to).toLocaleDateString("fr-FR")}
              {hasComparisonData ? "." : " : les variations ne sont pas affichées."}
            </p>
          )}
        </>
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
              <div className="flex flex-wrap justify-end gap-1">
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
                color={activityMetric === "errors" ? CHART_COLORS.danger : CHART_COLORS.primary}
                onPointClick={handleActivityPointClick}
              />
            )}
          </ChartFrame>
        </div>

        <ChartFrame
          title="Répartition des outils"
          isEmpty={!toolUsage.isLoading && toolUsageItems.length === 0}
          emptyDescription="Aucun appel d'outil ne correspond aux filtres actifs."
        >
          <ToolUsagePanel items={toolUsageItems} isLoading={toolUsage.isLoading} />
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

        <ChartFrame
          title="Sessions par agent"
          isEmpty={!sessions.isLoading && sessionsByAgent.length === 0}
          emptyDescription="Aucune session ne correspond aux filtres actifs."
        >
          {sessions.isLoading ? (
            <ChartSkeleton />
          ) : (
            <>
              <BreakdownBarChart
                data={sessionsByAgent}
                valueLabel="Sessions"
                valueFormatter={formatNumber}
              />
              {isPartialPage && (
                <p className="mt-2 text-[11px] text-foreground-muted">
                  Calculé sur les {SESSION_PAGE_SIZE} sessions les plus récentes du périmètre.
                </p>
              )}
            </>
          )}
        </ChartFrame>

        <ChartFrame
          title="Coût par source"
          isEmpty={!sessions.isLoading && costBySource.length === 0}
          emptyDescription="Aucun coût n'est disponible pour les filtres actifs."
        >
          {sessions.isLoading ? (
            <ChartSkeleton />
          ) : (
            <BreakdownBarChart
              data={costBySource}
              valueLabel="Coût"
              valueFormatter={formatUsd}
              color={CHART_SERIES_COLORS[1]}
            />
          )}
        </ChartFrame>

        <ChartFrame
          title="Sessions les plus coûteuses"
          isEmpty={!sessions.isLoading && topSessions.length === 0}
          emptyDescription="Aucune session avec un coût connu ne correspond aux filtres actifs."
        >
          {sessions.isLoading ? <ChartSkeleton /> : <TopSessionsTable sessions={topSessions} />}
        </ChartFrame>

        <ChartFrame title="Qualité des données" isEmpty={false}>
          <DataQualityPanel />
        </ChartFrame>
      </div>
    </div>
  );
};
