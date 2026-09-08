import React, { useEffect, useState } from "react";
import { apiClient } from "../../../shared/api/client";
import { ApiError } from "../../../shared/api/types";
import type { ProblemDetails } from "../../../shared/api/types";
import { ApiErrorBanner } from "../../../shared/components/ApiErrorBanner";
import { IndicatorCard } from "./IndicatorCard";
import type { IndicatorsResponse } from "../types";
import { METRIC_DEFINITIONS } from "../types"

export const DashboardScreen: React.FC = () => {
  const [indicators, setIndicators] = useState<IndicatorsResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<ProblemDetails | null>(null);

  useEffect(() => {
    fetchIndicators();
  }, []);

  const fetchIndicators = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.get<IndicatorsResponse>("/metrics/indicators");
      setIndicators(data);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.problem);
      } else {
        setError({
          title: "Erreur réseau",
          status: 500,
          detail: "Impossible de charger les métriques du tableau de bord.",
        });
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Tableau de bord</h1>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
          Vue globale des indicateurs de performance et d'utilisation des agents.
        </p>
      </div>

      <ApiErrorBanner error={error} onDismiss={() => setError(null)} />

      {loading ? (
        <div className="p-8 text-center text-sm text-slate-500">Chargement des indicateurs...</div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <IndicatorCard
            definition={METRIC_DEFINITIONS.sessions!}
            value={indicators?.session_count ?? 0}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.tokens!}
            value={indicators?.total_tokens ?? null}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.cost!}
            value={indicators?.total_cost_usd ?? null}
            formatter={(v) => `$${v.toFixed(2)}`}
          />
          <IndicatorCard
            definition={METRIC_DEFINITIONS.errorRate!}
            value={indicators?.error_rate !== undefined && indicators.error_rate !== null ? indicators.error_rate * 100 : null}
            formatter={(v) => `${v.toFixed(1)} %`}
          />
        </div>
      )}
    </div>
  );
};
