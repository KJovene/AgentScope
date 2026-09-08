import { render, screen, fireEvent } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { EMPTY_METRIC_FILTERS } from '@shared/lib/metric-filters';

const reset = vi.fn();
let filters = EMPTY_METRIC_FILTERS;

vi.mock('@shared/hooks/use-metric-filters', () => ({
  useMetricFilters: () => ({ filters, reset, setFilters: vi.fn() }),
}));

import { DashboardPage } from '@features/dashboard/ui/DashboardPage';

describe('DashboardPage', () => {
  beforeEach(() => {
    reset.mockClear();
    filters = EMPTY_METRIC_FILTERS;
  });

  it('renders the four KPI cards with the "unavailable" placeholder', () => {
    render(<DashboardPage />);
    expect(screen.getByRole('heading', { name: 'Dashboard' })).toBeInTheDocument();
    for (const label of ['Sessions', 'Tokens', 'Coût estimé', "Taux d'erreur"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
    expect(screen.getAllByText('—')).toHaveLength(4);
    expect(screen.getByText('Visualisations à venir')).toBeInTheDocument();
  });

  it('hides the reset action when no filter is active', () => {
    render(<DashboardPage />);
    expect(screen.queryByRole('button', { name: /Réinitialiser/ })).not.toBeInTheDocument();
  });

  it('shows the reset action when filters are active and calls reset()', () => {
    filters = { ...EMPTY_METRIC_FILTERS, sources: ['tracelab'] };
    render(<DashboardPage />);
    fireEvent.click(screen.getByRole('button', { name: /Réinitialiser/ }));
    expect(reset).toHaveBeenCalledOnce();
  });
});
