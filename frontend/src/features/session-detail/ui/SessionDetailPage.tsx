import { Link } from '@tanstack/react-router';

import { useSessionDetailQuery } from '@shared/api/sessions.queries';
import type { TimelineEntry } from '@shared/api/sessions.contracts';
import { PageHeader } from '@shared/components/PageHeader';
import {
  formatDateTime,
  formatDuration,
  formatTokens,
  formatUsd,
  UNAVAILABLE,
} from '@shared/lib/format';
import { Card, EmptyState, ErrorState } from '@shared/ui';

interface SessionDetailPageProps {
  sessionId: string;
}

const KIND_LABEL: Record<string, string> = {
  model_call: 'Appel modèle',
  tool_call: 'Appel outil',
};

/** A failed entry gets the danger accent so errors are scannable down the rail. */
function isFailed(entry: TimelineEntry) {
  return entry.status !== 'success' || Boolean(entry.error_type);
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <Card className="min-w-[9rem]">
      <span className="block text-[10px] uppercase tracking-[0.16em] text-foreground-muted">
        {label}
      </span>
      <span className="mt-1 block text-lg font-semibold tabular-nums text-foreground">{value}</span>
    </Card>
  );
}

function TimelineRow({ entry }: { entry: TimelineEntry }) {
  const failed = isFailed(entry);

  return (
    <li className="relative pl-6">
      <span
        className={`absolute left-[-5px] top-3 h-2.5 w-2.5 rounded-full ${
          failed ? 'bg-danger' : entry.kind === 'model_call' ? 'bg-primary' : 'bg-success'
        }`}
      />
      <Card className={failed ? 'border-danger/40' : undefined}>
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <div>
            <span className="text-xs uppercase tracking-wider text-foreground-muted">
              #{entry.sequence} · {KIND_LABEL[entry.kind] ?? entry.kind}
            </span>
            <p className="font-medium text-foreground">{entry.name}</p>
          </div>
          <span className="text-xs text-foreground-muted">{formatDateTime(entry.started_at)}</span>
        </div>

        <dl className="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-xs text-foreground-muted">
          <div>
            <dt className="inline">Durée : </dt>
            <dd className="inline tabular-nums">{formatDuration(entry.duration_ms)}</dd>
          </div>
          <div>
            <dt className="inline">Tokens : </dt>
            <dd className="inline tabular-nums">{formatTokens(entry.total_tokens)}</dd>
          </div>
          <div>
            <dt className="inline">Coût : </dt>
            <dd className="inline tabular-nums">{formatUsd(entry.cost_usd)}</dd>
          </div>
          <div>
            <dt className="inline">Statut : </dt>
            <dd className={`inline ${failed ? 'text-danger' : ''}`}>
              {entry.error_type ? `${entry.status} (${entry.error_type})` : entry.status}
            </dd>
          </div>
        </dl>
      </Card>
    </li>
  );
}

/**
 * Session drill-down (I5.15): identity, totals and the chronological timeline of
 * model/tool calls served by `GET /sessions/{id}`.
 */
export function SessionDetailPage({ sessionId }: SessionDetailPageProps) {
  const session = useSessionDetailQuery(sessionId);

  if (session.isLoading) {
    return (
      <div className="p-8 text-center text-sm text-foreground-muted">Chargement de la session...</div>
    );
  }

  if (session.error || !session.data) {
    return <ErrorState error={session.error} onRetry={() => void session.refetch()} />;
  }

  const detail = session.data;
  const timeline = [...detail.timeline].sort((a, b) => a.sequence - b.sequence);

  return (
    <div className="stagger space-y-6">
      <PageHeader
        title={`Session #${detail.session_id}`}
        description={`${detail.source_name} · ${detail.agent_name ?? UNAVAILABLE} · ${detail.external_id}`}
        actions={
          <Link to="/sessions" className="text-sm text-primary hover:underline">
            ← Retour aux sessions
          </Link>
        }
      />

      <div className="flex flex-wrap gap-3">
        <Metric label="Démarrée" value={formatDateTime(detail.started_at)} />
        <Metric label="Durée" value={formatDuration(detail.duration_ms)} />
        <Metric label="Tokens" value={formatTokens(detail.total_tokens)} />
        <Metric label="Coût" value={formatUsd(detail.total_cost_usd)} />
        <Metric label="Erreurs" value={String(detail.error_count)} />
      </div>

      {timeline.length === 0 ? (
        <EmptyState
          title="Timeline vide"
          description="Aucun appel modèle ou outil n'a été enregistré pour cette session."
        />
      ) : (
        <ol className="ml-2 space-y-4 border-l border-border pl-2">
          {timeline.map((entry) => (
            <TimelineRow key={`${entry.kind}-${entry.sequence}`} entry={entry} />
          ))}
        </ol>
      )}
    </div>
  );
}
