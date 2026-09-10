import { useRef } from 'react';

import { PageHeader } from '@shared/components/PageHeader';
import { Button, EmptyState, ErrorState, Spinner } from '@shared/ui';

import { useAnalyzeMutation } from '../api/analyze.queries';
import { toFieldProfileSetView } from '../model/analyze.mappers';
import { useWorkbenchStore } from '../model/workbench-store';

import { FieldProfileTable } from './FieldProfileTable';
import { AgentChat } from './AgentChat';

/**
 * "Ajouter une source" — upload an unknown file, see its field profile, chat with
 * the agent, edit the proposed mapping, preview, then import.
 * I5.5 (this file) : upload -> profil affiché. I5.6 : la proposition rendue par
 * `/analyze` ouvre la conversation avec l'agent. Édition (I5.7) et
 * prévisualisation (I5.8) restent à construire par-dessus.
 */
export function AddSourcePage() {
  const inputRef = useRef<HTMLInputElement>(null);
  const analyze = useAnalyzeMutation();
  const startSession = useWorkbenchStore((s) => s.startSession);
  const hasFile = useWorkbenchStore((s) => s.fileRef !== null);

  const handleFileSelected = (file: File | undefined) => {
    if (!file) return;
    // The proposal is what the agent discusses — hand it straight to the
    // workbench store, which owns it for the rest of the conversation.
    analyze.mutate(
      { file },
      { onSuccess: (result) => startSession({ fileRef: file.name, proposal: result.proposal }) },
    );
  };

  return (
    <>
      <PageHeader
        title="Ajouter une source"
        description="L'agent profile un fichier inconnu et propose un mapping. Vous corrigez, prévisualisez, puis importez. L'IA ne modifie jamais la base."
      />

      <div className="space-y-4">
        <input
          ref={inputRef}
          type="file"
          accept=".jsonl,.csv,.parquet,.json"
          className="hidden"
          onChange={(e) => handleFileSelected(e.target.files?.[0])}
        />
        <Button
          onClick={() => inputRef.current?.click()}
          disabled={analyze.isPending}
          aria-label="Choisir un fichier à analyser"
        >
          {analyze.isPending ? <Spinner /> : null}
          {analyze.isPending ? 'Analyse en cours…' : 'Choisir un fichier'}
        </Button>

        {analyze.isError && <ErrorState error={analyze.error} onRetry={() => analyze.reset()} />}

        {analyze.isSuccess && (
          <FieldProfileTable profile={toFieldProfileSetView(analyze.data.profile)} />
        )}

        {hasFile && <AgentChat className="h-[32rem]" />}

        {analyze.isIdle && (
          <EmptyState
            title="Aucun fichier analysé"
            description="Choisissez un fichier pour voir apparaître le profil de ses champs."
          />
        )}
      </div>
    </>
  );
}
