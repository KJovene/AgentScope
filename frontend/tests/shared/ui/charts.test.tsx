import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { ChartFrame, TimeSeriesChart } from '@shared/ui';

describe('ChartFrame', () => {
  it('renders the title and children when not empty', () => {
    render(
      <ChartFrame title="Activité" isEmpty={false}>
        <div>contenu du graphe</div>
      </ChartFrame>,
    );

    expect(screen.getByText('Activité')).toBeInTheDocument();
    expect(screen.getByText('contenu du graphe')).toBeInTheDocument();
    expect(screen.queryByText('Aucune donnée disponible')).not.toBeInTheDocument();
  });

  it('renders an empty state instead of children when isEmpty', () => {
    render(
      <ChartFrame title="Activité" isEmpty emptyDescription="Rien à afficher.">
        <div>contenu du graphe</div>
      </ChartFrame>,
    );

    expect(screen.getByText('Aucune donnée disponible')).toBeInTheDocument();
    expect(screen.getByText('Rien à afficher.')).toBeInTheDocument();
    expect(screen.queryByText('contenu du graphe')).not.toBeInTheDocument();
  });

  it('renders optional actions next to the title', () => {
    render(
      <ChartFrame title="Activité" isEmpty={false} actions={<button type="button">Bascule</button>}>
        <div>contenu</div>
      </ChartFrame>,
    );

    expect(screen.getByRole('button', { name: 'Bascule' })).toBeInTheDocument();
  });
});

describe('TimeSeriesChart', () => {
  it('renders without crashing given a list of points', () => {
    const { container } = render(
      <TimeSeriesChart
        data={[
          { period: '2026-01-01', value: 3 },
          { period: '2026-01-02', value: null },
        ]}
        valueLabel="Sessions"
      />,
    );

    // jsdom has no layout engine — Recharts' <ResponsiveContainer> renders an
    // empty box, but the wrapper itself must mount without throwing.
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});
