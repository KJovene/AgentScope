import { EmptyState } from '@shared/ui';
import { formatDateTime, formatNumber, formatPercent } from '@shared/lib/format';

import { useDataQualityQuery } from '../api/data-quality.queries';
import type { DataQualityBatch } from '../api/data-quality.contracts';

/**
 * Data-quality panel embedded in the dashboard: completeness, duplicates and
 * rejects per import batch. Issue I5.16. Consumes `GET /data-quality`.
 */

/** Completeness is a state, not an identity — hence a status color, with the value beside it. */
function completenessTone(rate: number | null | undefined): string {
  if (rate == null) return 'text-foreground-muted';
  if (rate >= 0.9) return 'text-success';
  if (rate >= 0.75) return 'text-warning';
  return 'text-danger';
}

function totalRows(batch: DataQualityBatch): number {
  return batch.imported_count + batch.duplicate_count + batch.rejected_count;
}

export function DataQualityPanel() {
  const quality = useDataQualityQuery();
  const batches = quality.data?.batches ?? [];

  if (quality.isLoading) {
    return <p className="p-4 text-xs text-foreground-muted">Chargement de la qualité des données...</p>;
  }

  if (quality.isError || batches.length === 0) {
    return (
      <EmptyState
        title="Aucun bilan d'import"
        description="La complétude, les doublons et les rejets s'affichent après le premier import."
      />
    );
  }

  const imported = batches.reduce((sum, b) => sum + b.imported_count, 0);
  const rejected = batches.reduce((sum, b) => sum + b.rejected_count, 0);
  const duplicates = batches.reduce((sum, b) => sum + b.duplicate_count, 0);
  const rows = batches.reduce((sum, b) => sum + totalRows(b), 0);

  return (
    <div>
      <dl className="mb-3 grid grid-cols-3 gap-3 text-xs">
        <div>
          <dt className="text-foreground-muted">Lignes importées</dt>
          <dd className="mt-0.5 font-semibold tabular-nums text-foreground">
            {formatNumber(imported)}
          </dd>
        </div>
        <div>
          <dt className="text-foreground-muted">Taux de rejet</dt>
          <dd
            className={`mt-0.5 font-semibold tabular-nums ${
              rejected > 0 ? 'text-danger' : 'text-foreground'
            }`}
          >
            {rows > 0 ? formatPercent(rejected / rows) : '—'}
          </dd>
        </div>
        <div>
          <dt className="text-foreground-muted">Doublons</dt>
          <dd className="mt-0.5 font-semibold tabular-nums text-foreground">
            {rows > 0 ? formatPercent(duplicates / rows) : '—'}
          </dd>
        </div>
      </dl>

      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <caption className="sr-only">Complétude et rejets par lot d'import</caption>
          <thead className="text-left uppercase tracking-wider text-foreground-muted">
            <tr className="border-b border-border">
              <th scope="col" className="py-2 pr-3 font-medium">Source</th>
              <th scope="col" className="py-2 px-3 font-medium">Importé le</th>
              <th scope="col" className="py-2 px-3 text-right font-medium">Lignes</th>
              <th scope="col" className="py-2 px-3 text-right font-medium">Rejets</th>
              <th scope="col" className="py-2 pl-3 text-right font-medium">Complétude</th>
            </tr>
          </thead>
          <tbody>
            {batches.map((batch) => (
              <tr key={batch.import_batch_id} className="border-b border-border/60 last:border-0">
                <td className="py-1.5 pr-3 text-foreground">{batch.source_name}</td>
                <td className="py-1.5 px-3 text-foreground-muted">
                  {formatDateTime(batch.imported_at)}
                </td>
                <td className="py-1.5 px-3 text-right tabular-nums text-foreground-muted">
                  {formatNumber(batch.imported_count)}
                </td>
                <td
                  className={`py-1.5 px-3 text-right tabular-nums ${
                    batch.rejected_count > 0 ? 'text-danger' : 'text-foreground-muted'
                  }`}
                >
                  {formatNumber(batch.rejected_count)}
                </td>
                <td
                  className={`py-1.5 pl-3 text-right font-semibold tabular-nums ${completenessTone(
                    batch.completeness_rate,
                  )}`}
                >
                  {formatPercent(batch.completeness_rate)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
