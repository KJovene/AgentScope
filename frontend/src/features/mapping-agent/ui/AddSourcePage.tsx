import { PageHeader } from '@shared/components/PageHeader';
import { EmptyState } from '@shared/ui';

/**
 * "Ajouter une source" — upload an unknown file, see its field profile, chat with
 * the agent, edit the proposed mapping, preview, then import.
 * Layers to build: api/ (analyze, chat, mappings, preview), model/, ui/ — issues I5.5–I5.8.
 */
export function AddSourcePage() {
  return (
    <>
      <PageHeader
        title="Ajouter une source"
        description="L'agent profile un fichier inconnu et propose un mapping. Vous corrigez, prévisualisez, puis importez. L'IA ne modifie jamais la base."
      />
      <EmptyState
        title="Assistant d'import à venir"
        description="Upload + profil des champs (I5.5), chat agent (I5.6), édition de mapping (I5.7), prévisualisation (I5.8)."
      />
    </>
  );
}
