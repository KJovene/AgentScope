import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { DataQualityPanel } from '@features/data-quality/ui/DataQualityPanel';

// AddSourcePage is no longer a placeholder (I5.5) — see AddSourcePage.test.tsx.
// SessionDetailPage is no longer a placeholder either — it fetches and renders
// the real timeline; see SessionDetails.test.tsx / SessionListPage.test.tsx.
describe('placeholder feature pages', () => {
  it('DataQualityPanel renders the empty state', () => {
    render(<DataQualityPanel />);
    expect(screen.getByText('Qualité des données à venir')).toBeInTheDocument();
  });
});
