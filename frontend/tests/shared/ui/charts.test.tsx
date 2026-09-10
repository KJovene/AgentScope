import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { buildDurationHistogram, ChartFrame, DistributionChart, StackedBarChart, TimeSeriesChart } from '@shared/ui';

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

  it('renders without crashing when onPointClick is provided', () => {
    const { container } = render(
      <TimeSeriesChart
        data={[{ period: '2026-01-01', value: 3 }]}
        valueLabel="Sessions"
        onPointClick={() => {}}
      />,
    );

    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});

describe('StackedBarChart', () => {
  it('renders one bar per series without crashing', () => {
    const { container } = render(
      <StackedBarChart
        data={[
          { category: 'bash', success: 10, error: 2 },
          { category: 'grep', success: 5, error: 0 },
        ]}
        series={[
          { key: 'success', label: 'Réussis' },
          { key: 'error', label: 'Erreurs' },
        ]}
      />,
    );

    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});

describe('buildDurationHistogram', () => {
  it('returns an empty array for no values', () => {
    expect(buildDurationHistogram([])).toEqual([]);
  });

  it('puts every value in a single bucket when they are all equal', () => {
    expect(buildDurationHistogram([500, 500, 500])).toEqual([
      { range: '500 ms', label: '500 ms', count: 3 },
    ]);
  });

  it('bins values into the requested bucket count, min and max both included', () => {
    const buckets = buildDurationHistogram([0, 1000, 2000, 3000, 4000], 4);

    expect(buckets).toHaveLength(4);
    expect(buckets.reduce((sum, b) => sum + b.count, 0)).toBe(5);
    // The max value falls in the last bucket, not dropped/overflowed.
    expect(buckets[3]?.count).toBeGreaterThan(0);
  });

  it('labels a bucket with one unit and no decimals, so an axis tick always fits', () => {
    expect(buildDurationHistogram([100, 100], 1)[0]?.label).toBe('100 ms');
    expect(buildDurationHistogram([1500, 1500], 1)[0]?.label).toBe('2 s');
    expect(buildDurationHistogram([7_200_000, 7_200_000], 1)[0]?.label).toBe('2 h');
    expect(buildDurationHistogram([259_200_000, 259_200_000], 1)[0]?.label).toBe('3 j');
  });

  it('keeps the full span in `range` for the tooltip', () => {
    const buckets = buildDurationHistogram([0, 120_000], 2);
    expect(buckets[0]?.range).toBe('0 ms – 1 min');
  });
});

describe('DistributionChart', () => {
  it('renders without crashing given a list of durations', () => {
    const { container } = render(<DistributionChart values={[100, 200, 300, 4000]} />);

    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});
