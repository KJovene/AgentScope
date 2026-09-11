import { PageHeader } from '@shared/components/PageHeader';
import { EmptyState, ErrorState, Spinner } from '@shared/ui';

import { useImportHistory } from '../hooks/use-import-history';
import { ImportHistoryTable } from './ImportHistoryTable';

export function ImportHistoryScreen() {
  const { rows, isLoading, isError, error, refetch } = useImportHistory();

  return (
    <>
      <PageHeader
        title="Historique des imports"
        description="Consultez l'ensemble des lots téléversés et le détail des rejets d'importation."
      />
      {isLoading ? (
        <Spinner />
      ) : isError ? (
        <ErrorState error={error} onRetry={() => void refetch()} />
      ) : rows.length === 0 ? (
        <EmptyState title="Aucun import" description="Aucun lot n'a encore été importé." />
      ) : (
        <ImportHistoryTable rows={rows} />
      )}
    </>
  );
}
