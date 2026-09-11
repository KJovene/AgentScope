import { Link } from '@tanstack/react-router';

import { type ImportRow } from '../model/import.mappers';

/** Presentational: receives already-formatted rows, renders nothing it computes itself. */
export function ImportHistoryTable({ rows }: { rows: ImportRow[] }) {
  return (
    <div className="overflow-x-auto rounded-card border border-border">
      <table className="w-full text-sm">
        <thead className="bg-surface-muted text-left text-xs uppercase text-foreground-muted">
          <tr>
            <th className="px-3 py-2">Lot</th>
            <th className="px-3 py-2">Mapping</th>
            <th className="px-3 py-2">Statut</th>
            <th className="px-3 py-2 text-right">Importés</th>
            <th className="px-3 py-2 text-right">Doublons</th>
            <th className="px-3 py-2 text-right">Rejets</th>
            <th className="px-3 py-2 text-right">Infos manquantes</th>
            <th className="px-3 py-2">Date</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-t border-border hover:bg-surface-muted/50">
              <td className="px-3 py-2">
                <Link
                  to="/imports/$importId"
                  params={{ importId: row.id }}
                  className="font-mono text-primary hover:underline"
                >
                  {row.id}
                </Link>
              </td>
              <td className="px-3 py-2">{row.mappingId}</td>
              <td className="px-3 py-2">{row.statusLabel}</td>
              <td className="px-3 py-2 text-right tabular-nums">{row.imported}</td>
              <td className="px-3 py-2 text-right tabular-nums">{row.duplicates}</td>
              <td className="px-3 py-2 text-right tabular-nums">{row.rejected}</td>
              <td className="px-3 py-2 text-right tabular-nums">{row.missingInfo}</td>
              <td className="px-3 py-2 text-foreground-muted">{row.importedAt}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
