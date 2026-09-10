import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DataQualityPanel } from '@features/data-quality/ui/DataQualityPanel';
import { SessionDetailPage } from '@/features/session-detail/ui/SessionTimeline';

// AddSourcePage is no longer a placeholder (I5.5) — see AddSourcePage.test.tsx.
describe('placeholder feature pages', () => {
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
