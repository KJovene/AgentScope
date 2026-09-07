import { PageHeader } from '@shared/components/PageHeader';
import { EmptyState, ErrorState, Spinner } from '@shared/ui';

import { useImportHistory } from '../hooks/use-import-history';
import { ImportHistoryTable } from './ImportHistoryTable';

export function ImportHistoryPage() {
  const { rows, isLoading, isError, error, refetch } = useImportHistory();

  return (
    <>
      <PageHeader
        title="Historique des imports"
        description="Chaque import affiche son bilan : importés, doublons, rejets, informations manquantes."
      />

      {isLoading && <Spinner />}
      {isError && <ErrorState error={error} onRetry={() => void refetch()} />}
      {!isLoading && !isError && rows.length === 0 && (
        <EmptyState title="Aucun import" description="Importez un fichier pour commencer." />
      )}
      {!isLoading && !isError && rows.length > 0 && <ImportHistoryTable rows={rows} />}
    </>
  );
}
