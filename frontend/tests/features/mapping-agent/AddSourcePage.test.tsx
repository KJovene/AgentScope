import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const mutationState = {
  mutate: vi.fn(),
  reset: vi.fn(),
  isPending: false,
  isError: false,
  isSuccess: false,
  isIdle: true,
  data: undefined as unknown,
  error: null as unknown,
};

vi.mock('@features/mapping-agent/api/analyze.queries', () => ({
  useAnalyzeMutation: () => mutationState,
}));

import { AddSourcePage } from '@features/mapping-agent/ui/AddSourcePage';

function resetMutationState() {
  mutationState.isPending = false;
  mutationState.isError = false;
  mutationState.isSuccess = false;
  mutationState.isIdle = true;
  mutationState.data = undefined;
  mutationState.error = null;
  mutationState.mutate.mockClear();
}

describe('AddSourcePage (I5.5)', () => {
  it('affiche un état vide tant qu\'aucun fichier n\'a été analysé', () => {
    resetMutationState();
    render(<AddSourcePage />);

    expect(screen.getByText('Aucun fichier analysé')).toBeDefined();
  });

  it('déclenche l\'analyse quand un fichier est choisi', () => {
    resetMutationState();
    render(<AddSourcePage />);

    const file = new File(['{"session_id":"s1"}'], 'trace.jsonl');
    const input = document.querySelector('input[type="file"]') as HTMLInputElement;
    fireEvent.change(input, { target: { files: [file] } });

    expect(mutationState.mutate).toHaveBeenCalledWith({ file });
  });

  it('affiche le profil des champs après une analyse réussie', () => {
    resetMutationState();
    mutationState.isIdle = false;
    mutationState.isSuccess = true;
    mutationState.data = {
      profile: {
        record_count: 500,
        fields: [
          {
            path: 'usage.input_tokens',
            inferred_type: 'int',
            null_ratio: 0.04,
            distinct_count: 87,
            sample_values: [120, 340],
          },
        ],
      },
      proposal: { definition: {}, explanations: [], ambiguities: [], unmapped_fields: [] },
    };

    render(<AddSourcePage />);

    expect(screen.getByText('usage.input_tokens')).toBeDefined();
    expect(screen.getByText(/500 enregistrement/)).toBeDefined();
  });

  it("affiche l'erreur si l'analyse échoue", () => {
    resetMutationState();
    mutationState.isIdle = false;
    mutationState.isError = true;
    mutationState.error = Object.assign(new Error('Fichier illisible'), { name: 'ApiError' });

    render(<AddSourcePage />);

    expect(screen.getByText('Fichier illisible')).toBeDefined();
  });
});
