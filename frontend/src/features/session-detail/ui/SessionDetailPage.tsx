import { PageHeader } from '@shared/components/PageHeader';
import { EmptyState } from '@shared/ui';

/**
 * Detailed view of one session: timeline of model_call + tool_call, tokens, cost,
 * errors, link to the raw record (provenance). Issue I5.15.
 */
export function SessionDetailPage({ sessionId }: { sessionId: string }) {
  return (
    <>
      <PageHeader title="Session" description={`#${sessionId}`} />
      <EmptyState
        title="Vue détaillée à venir"
        description="Timeline des appels modèle et outils, tokens, coût, erreurs, lien vers l'enregistrement d'origine."
      />
    </>
  );
}
