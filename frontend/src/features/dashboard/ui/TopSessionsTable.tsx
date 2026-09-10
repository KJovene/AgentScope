import { Link } from '@tanstack/react-router';

import type { SessionItem } from '@shared/api/sessions.contracts';
import {
  formatDateTime,
  formatDuration,
  formatTokens,
  formatUsd,
  UNAVAILABLE,
} from '@shared/lib/format';

/**
 * The costliest sessions of the current slice, as a drill-down shortcut: each
 * row links to the session detail. Built from the session page the duration
 * distribution already fetches, so it costs no extra request.
 */
export function TopSessionsTable({ sessions }: { sessions: SessionItem[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs">
        <caption className="sr-only">Sessions les plus coûteuses du périmètre filtré</caption>
        <thead className="text-left uppercase tracking-wider text-foreground-muted">
          <tr className="border-b border-border">
            <th scope="col" className="py-2 pr-3 font-medium">Session</th>
            <th scope="col" className="py-2 px-3 font-medium">Agent</th>
            <th scope="col" className="py-2 px-3 text-right font-medium">Durée</th>
            <th scope="col" className="py-2 px-3 text-right font-medium">Tokens</th>
            <th scope="col" className="py-2 pl-3 text-right font-medium">Coût</th>
          </tr>
        </thead>
        <tbody>
          {sessions.map((session) => (
            <tr key={session.session_id} className="border-b border-border/60 last:border-0">
              <td className="py-1.5 pr-3">
                <Link
                  to="/sessions/$sessionId"
                  params={{ sessionId: String(session.session_id) }}
                  className="text-primary hover:underline"
                >
                  {formatDateTime(session.started_at)}
                </Link>
              </td>
              <td className="py-1.5 px-3 text-foreground-muted">
                {session.agent_name ?? UNAVAILABLE}
              </td>
              <td className="py-1.5 px-3 text-right tabular-nums text-foreground-muted">
                {formatDuration(session.duration_ms)}
              </td>
              <td className="py-1.5 px-3 text-right tabular-nums text-foreground-muted">
                {formatTokens(session.total_tokens)}
              </td>
              <td className="py-1.5 pl-3 text-right font-semibold tabular-nums text-foreground">
                {formatUsd(session.total_cost_usd)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
