import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AddSourcePage } from '@features/mapping-agent/ui/AddSourcePage';
import { DataQualityPanel } from '@features/data-quality/ui/DataQualityPanel';
import { SessionDetailPage } from '@features/session-detail/ui/SessionDetailPage';

describe('placeholder feature pages', () => {
  it('AddSourcePage renders its header and "coming soon" body', () => {
    render(<AddSourcePage />);
    expect(screen.getByRole('heading', { name: 'Ajouter une source' })).toBeInTheDocument();
    expect(screen.getByText("Assistant d'import à venir")).toBeInTheDocument();
  });

  it('DataQualityPanel renders the empty state', () => {
    render(<DataQualityPanel />);
    expect(screen.getByText('Qualité des données à venir')).toBeInTheDocument();
  });

  it('SessionDetailPage shows the session id in the header', () => {
    render(<SessionDetailPage sessionId="sess-42" />);
    expect(screen.getByRole('heading', { name: 'Session' })).toBeInTheDocument();
    expect(screen.getByText('#sess-42')).toBeInTheDocument();
    expect(screen.getByText('Vue détaillée à venir')).toBeInTheDocument();
  });
});
