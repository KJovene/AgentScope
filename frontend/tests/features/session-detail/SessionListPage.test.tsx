import { fireEvent, screen, waitFor } from '@testing-library/react';
import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { SessionListPage } from '@features/session-detail';
import { metricFiltersSchema } from '@shared/lib/metric-filters';

import { server } from '../../msw/server';
import { renderRouted } from '../../utils';

const SESSION = {
  session_id: 1,
  source_name: 'TraceLab',
  agent_name: 'claude',
  repository_name: null,
  started_at: '2026-01-15T10:00:00Z',
  duration_ms: 4200,
  model_call_count: 2,
  tool_call_count: 1,
  total_tokens: 500,
  total_cost_usd: 0.02,
  error_count: 0,
};

function renderSessionList(initialSearch = '') {
  return renderRouted(<SessionListPage />, { validateSearch: metricFiltersSchema, initialSearch });
}

describe('SessionListPage', () => {
  it('renders a row per session, linking to the session detail page', async () => {
    server.use(
      http.get('/api/sessions', () =>
        HttpResponse.json({ items: [SESSION], total: 1, limit: 50, offset: 0 }),
      ),
    );

    renderSessionList();

    await waitFor(() => {
      expect(screen.getByText('TraceLab')).toBeInTheDocument();
      expect(screen.getByText('claude')).toBeInTheDocument();
    });

    const link = screen.getByRole('link', { name: /2026/ });
    expect(link).toHaveAttribute('href', '/sessions/1');
  });

  it('shows an empty state when no session matches the active filters', async () => {
    server.use(
      http.get('/api/sessions', () =>
        HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 }),
      ),
    );

    renderSessionList();

    await waitFor(() => {
      expect(screen.getByText('Aucune session')).toBeInTheDocument();
    });
  });

  it('paginates: "Suivant" requests the next page, "Précédent" is disabled on page 1', async () => {
    const requestedOffsets: string[] = [];
    server.use(
      http.get('/api/sessions', ({ request }) => {
        const offset = new URL(request.url).searchParams.get('offset') ?? '0';
        requestedOffsets.push(offset);
        return HttpResponse.json({
          items: Array.from({ length: 50 }, (_, i) => ({ ...SESSION, session_id: i + 1 })),
          total: 120,
          limit: 50,
          offset: Number(offset),
        });
      }),
    );

    renderSessionList();

    const previous = await screen.findByRole('button', { name: 'Précédent' });
    expect(previous).toBeDisabled();

    fireEvent.click(screen.getByRole('button', { name: 'Suivant' }));

    await waitFor(() => {
      expect(requestedOffsets).toContain('50');
    });
  });

  it('resets to the first page when a filter changes', async () => {
    server.use(
      http.get('/api/sessions', () =>
        HttpResponse.json({ items: [SESSION], total: 1, limit: 50, offset: 0 }),
      ),
    );

    // Starts already filtered by a source — the offset-reset effect must not
    // depend on this being the first render.
    renderSessionList('?sources=TraceLab');

    await waitFor(() => {
      expect(screen.getByText('TraceLab')).toBeInTheDocument();
    });
  });
});
