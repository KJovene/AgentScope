import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { metricFiltersSchema } from '@shared/lib/metric-filters';
import { FilterBar } from '@shared/components/filters';
import { TagMultiSelect } from '@shared/components/filters/TagMultiSelect';
import { DateRangeFilter } from '@shared/components/filters/DateRangeFilter';

import { server } from '../../msw/server';
import { renderRouted } from '../../utils';

describe('TagMultiSelect', () => {
  it('adds a value on Enter and calls onChange, clearing the draft', () => {
    let values: string[] = [];
    const { rerender } = render(
      <TagMultiSelect label="Agents" values={values} onChange={(next) => (values = next)} />,
    );

    const input = screen.getByLabelText('Agents');
    fireEvent.change(input, { target: { value: 'claude' } });
    fireEvent.keyDown(input, { key: 'Enter' });

    expect(values).toEqual(['claude']);
    rerender(<TagMultiSelect label="Agents" values={values} onChange={() => {}} />);
    expect(screen.getByText('claude')).toBeInTheDocument();
  });

  it('removes a value when its × button is clicked', () => {
    let values = ['claude'];
    render(
      <TagMultiSelect label="Agents" values={values} onChange={(next) => (values = next)} />,
    );

    fireEvent.click(screen.getByLabelText('Retirer claude'));

    expect(values).toEqual([]);
  });

  it('never adds an empty or duplicate value', () => {
    const onChange = () => {
      throw new Error('should not be called');
    };
    render(<TagMultiSelect label="Agents" values={['claude']} onChange={onChange} />);

    const input = screen.getByLabelText('Agents');
    fireEvent.keyDown(input, { key: 'Enter' }); // empty draft
    fireEvent.change(input, { target: { value: 'claude' } });
    fireEvent.keyDown(input, { key: 'Enter' }); // duplicate
  });
});

describe('DateRangeFilter', () => {
  it('maps a picked date to an ISO datetime string (start / end of day)', () => {
    let range: { from?: string; to?: string } = {};
    render(<DateRangeFilter from={undefined} to={undefined} onChange={(next) => (range = next)} />);

    fireEvent.change(screen.getByLabelText('Date de début'), { target: { value: '2026-01-01' } });
    expect(range.from).toBe('2026-01-01T00:00:00Z');

    fireEvent.change(screen.getByLabelText('Date de fin'), { target: { value: '2026-01-31' } });
    expect(range.to).toBe('2026-01-31T23:59:59Z');
  });
});

describe('FilterBar', () => {
  it('renders sources from GET /sources and toggles one into the URL filters', async () => {
    server.use(
      http.get('/api/sources', () =>
        HttpResponse.json([{ id: 's1', name: 'TraceLab', session_count: 1 }]),
      ),
    );

    const { router } = renderRouted(<FilterBar />, { validateSearch: metricFiltersSchema });

    const checkbox = await screen.findByLabelText('TraceLab');
    fireEvent.click(checkbox);

    await waitFor(() => {
      expect(router.state.location.search).toMatchObject({ sources: ['TraceLab'] });
    });
  });

  it('adds an agent tag and resets all filters', async () => {
    renderRouted(<FilterBar />, {
      validateSearch: metricFiltersSchema,
      initialSearch: '?agents=claude',
    });

    expect(await screen.findByText('Filtres (1)')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));

    await waitFor(() => expect(screen.getByText('Filtres')).toBeInTheDocument());
  });
});
