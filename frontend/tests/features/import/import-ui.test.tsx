import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { type ImportRow } from '@features/import/model/import.mappers';

vi.mock('@tanstack/react-router', () => ({
  Link: ({ to, params, children, ...rest }: Record<string, unknown>) => (
    <a href={typeof to === 'string' ? to : '#'} {...(rest as object)}>
      {children as never}
    </a>
  ),
}));

const historyState = {
  rows: [] as ImportRow[],
  isLoading: false,
  isError: false,
  error: null as unknown,
  refetch: vi.fn(),
};
vi.mock('@features/import/hooks/use-import-history', () => ({
  useImportHistory: () => historyState,
}));

const reportQuery = {
  data: undefined as unknown,
  isLoading: false,
  isError: false,
  error: null as unknown,
  refetch: vi.fn(),
};
vi.mock('@features/import/api/import.queries', () => ({
  useImportQuery: () => reportQuery,
}));

import { ImportHistoryScreen } from '@features/import/ui/ImportHistoryScreen';
import { ImportHistoryTable } from '@features/import/ui/ImportHistoryTable';
import { ImportReportPage } from '@features/import/ui/ImportReportPage';

const row: ImportRow = {
  id: 'sha-1',
  source: 'TraceLab',
  filename: 'trace.jsonl',
  format: 'JSONL',
  status: 'succeeded',
  statusLabel: 'Terminé',
  importedAt: '2 janv. 2026',
  imported: '10',
  duplicates: '1',
  rejected: '2',
  missingInfo: '0',
  hasRejects: true,
};

const batch = {
  id: 'sha-1',
  sourceName: 'TraceLab',
  originalFilename: 'trace.jsonl',
  fileFormat: 'jsonl',
  status: 'succeeded',
  importedAt: '2026-01-02T10:00:00Z',
  importedCount: 10,
  duplicateCount: 1,
  rejectedCount: 2,
  missingInfoCount: 0,
};

describe('ImportHistoryTable', () => {
  it('renders one row per import with a link to its report', () => {
    render(<ImportHistoryTable rows={[row]} />);
    expect(screen.getByText('TraceLab')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'trace.jsonl' })).toBeInTheDocument();
    expect(screen.getByText('Terminé')).toBeInTheDocument();
  });
});

describe('ImportHistoryScreen', () => {
  it('shows the loading spinner', () => {
    Object.assign(historyState, { isLoading: true, isError: false, rows: [] });
    render(<ImportHistoryScreen />);
    expect(screen.getByRole('status', { name: 'Chargement' })).toBeInTheDocument();
  });

  it('shows the empty state when there is no import', () => {
    Object.assign(historyState, { isLoading: false, isError: false, rows: [] });
    render(<ImportHistoryScreen />);
    expect(screen.getByText('Aucun import')).toBeInTheDocument();
  });

  it('renders the table once imports load', () => {
    Object.assign(historyState, { isLoading: false, isError: false, rows: [row] });
    render(<ImportHistoryScreen />);
    expect(screen.getByRole('link', { name: 'trace.jsonl' })).toBeInTheDocument();
  });

  it('renders the error state on failure', () => {
    Object.assign(historyState, {
      isLoading: false,
      isError: true,
      rows: [],
      error: new Error('ko'),
    });
    render(<ImportHistoryScreen />);
    expect(screen.getByText('Erreur')).toBeInTheDocument();
  });
});

describe('ImportReportPage', () => {
  it('shows the spinner while loading', () => {
    Object.assign(reportQuery, { isLoading: true, isError: false, data: undefined });
    render(<ImportReportPage importId="sha-1" />);
    expect(screen.getByRole('status', { name: 'Chargement' })).toBeInTheDocument();
  });

  it('renders the four metric cards from the loaded batch', () => {
    Object.assign(reportQuery, { isLoading: false, isError: false, data: batch });
    render(<ImportReportPage importId="sha-1" />);
    expect(screen.getByRole('heading', { name: 'trace.jsonl' })).toBeInTheDocument();
    expect(screen.getByText('Importés')).toBeInTheDocument();
    expect(screen.getByText('Rejets')).toBeInTheDocument();
  });

  it('renders the error state when the batch cannot be loaded', () => {
    Object.assign(reportQuery, {
      isLoading: false,
      isError: true,
      data: undefined,
      error: new Error('ko'),
    });
    render(<ImportReportPage importId="x" />);
    expect(screen.getByText('Erreur')).toBeInTheDocument();
  });
});
