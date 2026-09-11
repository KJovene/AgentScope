import { ErrorState, EmptyState, Spinner } from '@shared/ui';

import { useImportHistory } from '../hooks/use-import-history';
import { ImportHistoryTable } from './ImportHistoryTable';

export function ImportHistoryPage() {
  const history = useImportHistory();

  if (history.isLoading) return <Spinner />;
  if (history.isError) return <ErrorState error={history.error} onRetry={() => void history.refetch()} />;
  if (history.rows.length === 0) {
    return <EmptyState title="Aucun import" description="Aucun import n'est disponible." />;
  }

  return <ImportHistoryTable rows={history.rows} />;
}
