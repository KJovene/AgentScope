import type { ComponentProps } from 'react';

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ImportScreen } from '@/features/import/ui/ImportScreen';
import { apiClient } from '@shared/api/client';
import { ApiError } from '@shared/api/types';

vi.mock('@shared/api/client', () => ({
  apiClient: { get: vi.fn(), post: vi.fn() },
}));

const get = vi.mocked(apiClient.get);
const post = vi.mocked(apiClient.post);

const oneMapping = {
  items: [
    { mapping_id: 'tracelab-jsonl', name: 'tracelab-jsonl', source_name: 'TraceLab', source_format: 'jsonl', is_active: true },
  ],
  total: 1,
  limit: 200,
  offset: 0,
};

function selectFile(name = 'trace.jsonl', size = 20) {
  const input = screen.getByLabelText(/fichiers sources/i) as HTMLInputElement;
  const file = new File(['x'.repeat(size)], name, { type: 'application/json' });
  fireEvent.change(input, { target: { files: [file] } });
  return file;
}

/** Renders and waits for the mapping dropdown to finish loading its default option. */
async function renderReady(props: ComponentProps<typeof ImportScreen> = {}) {
  render(<ImportScreen {...props} />);
  await screen.findByRole('option', { name: /tracelab-jsonl/ });
}

describe('ImportScreen UI (I5.2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    get.mockResolvedValue(oneMapping);
  });

  it("désactive le bouton tant qu'aucun fichier n'est sélectionné", async () => {
    await renderReady();
    expect(screen.getByText('Importer des traces')).toBeInTheDocument();
    expect(
      (screen.getByRole('button', { name: "Lancer l'import" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("permet de sélectionner un fichier, l'afficher et activer l'envoi", async () => {
    await renderReady();
    selectFile();
    expect(screen.getByText('trace.jsonl')).toBeInTheDocument();
    expect(screen.getByText(/Fichiers sélectionnés \(1\)/)).toBeInTheDocument();
    expect(
      (screen.getByRole('button', { name: "Lancer l'import" }) as HTMLButtonElement).disabled,
    ).toBe(false);
  });

  it('retire un fichier de la sélection', async () => {
    await renderReady();
    selectFile('a.jsonl');
    fireEvent.click(screen.getByRole('button', { name: 'Supprimer' }));
    expect(screen.queryByText('a.jsonl')).not.toBeInTheDocument();
    expect(
      (screen.getByRole('button', { name: "Lancer l'import" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it("propose les mappings existants dans une liste déroulante", async () => {
    render(<ImportScreen />);
    const select = (await screen.findByLabelText(/identifiant du mapping/i)) as HTMLSelectElement;
    await waitFor(() => expect(select.value).toBe('tracelab-jsonl'));
    expect(screen.getByRole('option', { name: /TraceLab \(jsonl\)/ })).toBeInTheDocument();
  });

  it("désactive l'envoi quand aucun mapping n'est disponible", async () => {
    get.mockResolvedValue({ items: [], total: 0, limit: 200, offset: 0 });
    render(<ImportScreen />);
    const select = (await screen.findByLabelText(/identifiant du mapping/i)) as HTMLSelectElement;
    await waitFor(() => expect(select.disabled).toBe(true));
    selectFile();
    expect(
      (screen.getByRole('button', { name: "Lancer l'import" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  });

  it('envoie le formulaire, affiche le bilan et notifie le parent', async () => {
    const onImportCompleted = vi.fn();
    const mockReport = {
      id: 'imp-123',
      mapping_id: 'tracelab-jsonl',
      status: 'completed' as const,
      imported_count: 10,
      duplicate_count: 2,
      rejected_count: 1,
      missing_info_count: 0,
      imported_at: '2026-09-08T10:00:00Z',
    };
    post.mockResolvedValueOnce(mockReport);

    await renderReady({ onImportCompleted });
    selectFile('trace.jsonl', 5000); // KB branch of formatFileSize
    fireEvent.click(screen.getByRole('button', { name: "Lancer l'import" }));

    await waitFor(() => {
      expect(post).toHaveBeenCalledWith('/imports', expect.any(FormData));
      expect(screen.getByText("Bilan de l'importation")).toBeInTheDocument();
      expect(screen.getByText('10')).toBeInTheDocument();
    });
    expect(onImportCompleted).toHaveBeenCalledWith(mockReport);
    expect(screen.getByText(/KB/)).toBeInTheDocument();
  });

  it("affiche un statut non 'completed' avec le style d'avertissement", async () => {
    post.mockResolvedValueOnce({
      id: 'imp-9',
      mapping_id: 'm',
      status: 'partial',
      imported_count: 1,
      duplicate_count: 0,
      rejected_count: 4,
      missing_info_count: 0,
      imported_at: '2026-09-08T10:00:00Z',
    });
    await renderReady();
    selectFile('big.parquet', 2 * 1024 * 1024); // MB branch
    fireEvent.click(screen.getByRole('button', { name: "Lancer l'import" }));
    expect(await screen.findByText('partial')).toBeInTheDocument();
    expect(screen.getByText(/MB/)).toBeInTheDocument();
  });

  it("montre le détail d'une ApiError renvoyée par le serveur", async () => {
    post.mockRejectedValueOnce(
      new ApiError({ title: 'Import refusé', status: 422, detail: 'mapping inconnu' }),
    );
    await renderReady();
    selectFile();
    fireEvent.click(screen.getByRole('button', { name: "Lancer l'import" }));
    expect(await screen.findByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('mapping inconnu')).toBeInTheDocument();
  });

  it('affiche un message générique pour une erreur inattendue', async () => {
    post.mockRejectedValueOnce(new Error('network down'));
    await renderReady();
    selectFile();
    fireEvent.click(screen.getByRole('button', { name: "Lancer l'import" }));
    expect(await screen.findByText('Erreur inattendue')).toBeInTheDocument();
  });
});
