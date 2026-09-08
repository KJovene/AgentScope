import { Link } from '@tanstack/react-router';
import { useEffect, useState } from 'react';

import { ApiError } from '@shared/api/api-error';
import type { ProblemDetails } from '@shared/api/types';
import { useSessionsQuery } from '@shared/api/sessions.queries';
import { ApiErrorBanner } from '@shared/components/ApiErrorBanner';
import { FilterBar } from '@shared/components/filters';
import { PageHeader } from '@shared/components/PageHeader';
import { useMetricFilters } from '@shared/hooks/use-metric-filters';
import { formatDateTime, formatDuration, formatTokens, formatUsd, UNAVAILABLE } from '@shared/lib/format';
import { Button, EmptyState } from '@shared/ui';

const PAGE_SIZE = 50;

function toProblemDetails(error: unknown, fallbackDetail: string): ProblemDetails {
  if (error instanceof ApiError && error.problem) {
    return {
      type: error.problem.type,
      title: error.problem.title,
      status: error.problem.status,
      detail: error.problem.detail,
      errors: error.problem.errors?.map((e) => ({ field: e.field ?? '', message: e.message })),
    };
  }
  return { title: 'Erreur réseau', status: 500, detail: fallbackDetail };
}

/**
 * Filtered, paginated session list (I5.14) — the drill-down target from every
 * dashboard chart. Filters are the same shared URL state (`useMetricFilters`)
 * used by the dashboard, so a filtered link is shareable end to end.
 */
export function SessionListPage() {
  const { filters } = useMetricFilters();
  const [offset, setOffset] = useState(0);

  // A filter change makes the current page stale — start back at the top.
  const filtersKey = JSON.stringify(filters);
  useEffect(() => {
    setOffset(0);
  }, [filtersKey]);

  const sessions = useSessionsQuery({ ...filters, limit: PAGE_SIZE, offset });
  const items = sessions.data?.items ?? [];
  const total = sessions.data?.total ?? 0;

  return (
    <>
      <PageHeader title="Sessions" description="Liste des sessions correspondant aux filtres actifs." />

      <FilterBar />

      <ApiErrorBanner
        error={
          sessions.error
            ? toProblemDetails(sessions.error, 'Impossible de charger les sessions.')
            : null
        }
      />

      {sessions.isLoading ? (
        <div className="p-8 text-center text-sm text-slate-500">Chargement des sessions...</div>
      ) : items.length === 0 ? (
        <EmptyState
          title="Aucune session"
          description="Aucune session ne correspond aux filtres actifs."
        />
      ) : (
        <>
          <div className="overflow-x-auto rounded-card border border-border">
            <table className="w-full text-sm">
              <thead className="bg-surface-muted text-left text-xs uppercase text-foreground-muted">
                <tr>
                  <th className="px-3 py-2">Source</th>
                  <th className="px-3 py-2">Agent</th>
                  <th className="px-3 py-2">Démarrée</th>
                  <th className="px-3 py-2 text-right">Durée</th>
                  <th className="px-3 py-2 text-right">Tokens</th>
                  <th className="px-3 py-2 text-right">Coût</th>
                  <th className="px-3 py-2 text-right">Erreurs</th>
                </tr>
              </thead>
              <tbody>
                {items.map((session) => (
                  <tr
                    key={session.session_id}
                    className="border-t border-border hover:bg-surface-muted/50"
                  >
                    <td className="px-3 py-2">{session.source_name}</td>
                    <td className="px-3 py-2">{session.agent_name ?? UNAVAILABLE}</td>
                    <td className="px-3 py-2">
                      <Link
                        to="/sessions/$sessionId"
                        params={{ sessionId: String(session.session_id) }}
                        className="text-primary hover:underline"
                      >
                        {formatDateTime(session.started_at)}
                      </Link>
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {formatDuration(session.duration_ms)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {formatTokens(session.total_tokens)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">
                      {formatUsd(session.total_cost_usd)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{session.error_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-3 flex items-center justify-between text-sm text-foreground-muted">
            <span>
              {offset + 1}–{Math.min(offset + PAGE_SIZE, total)} sur {total}
            </span>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={offset === 0}
                onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
              >
                Précédent
              </Button>
              <Button
                type="button"
                variant="secondary"
                size="sm"
                disabled={offset + PAGE_SIZE >= total}
                onClick={() => setOffset((o) => o + PAGE_SIZE)}
              >
                Suivant
              </Button>
            </div>
          </div>
        </>
      )}
    </>
  );
}
