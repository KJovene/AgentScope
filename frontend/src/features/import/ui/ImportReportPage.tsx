import { PageHeader } from '@shared/components/PageHeader';
import { MetricCard } from '@shared/components/MetricCard';
import { ErrorState, Spinner } from '@shared/ui';

import { useImportQuery } from '../api/import.queries';
import { toImportRow } from '../model/import.mappers';

export function ImportReportPage({ importId }: { importId: string }) {
  const { data, isLoading, isError, error, refetch } = useImportQuery(importId);

  if (isLoading) return <Spinner />;
  if (isError || !data) return <ErrorState error={error} onRetry={() => void refetch()} />;

  const row = toImportRow(data);

  return (
    <>
      <PageHeader
        title={`Lot ${row.id}`}
        description={`Mapping : ${row.mappingId} · ${row.importedAt}`}
      />
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <MetricCard label="Importés" value={row.imported} />
        <MetricCard label="Doublons" value={row.duplicates} />
        <MetricCard label="Rejets" value={row.rejected} />
        <MetricCard label="Infos manquantes" value={row.missingInfo} />
      </div>
      {/* Rejects table (consultable + expliqués) — issue I5.4. */}
    </>
  );
}
