import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { HttpResponse, http } from 'msw';
import { describe, expect, it } from 'vitest';

import { metricFiltersSchema } from '@shared/lib/metric-filters';
import { FilterBar } from '@shared/components/filters';
import { OptionMultiSelect } from '@shared/components/filters/OptionMultiSelect';
import { DateRangeFilter } from '@shared/components/filters/DateRangeFilter';

import { server } from '../../msw/server';
import { renderRouted } from '../../utils';

describe('OptionMultiSelect', () => {
  const OPTIONS = ['claude', 'codex', 'OpenCode'];

  function setup(values: string[], onChange: (next: string[]) => void) {
    return render(
      <OptionMultiSelect
        label="Agents"
        options={OPTIONS}
        values={values}
        onChange={onChange}
        placeholder="Choisir un agent..."
        emptyMessage="Aucun agent enregistré."
      />,
    );
  }

  it('offers only the values that exist, and adds the picked one', () => {
    let values: string[] = [];
    setup(values, (next) => (values = next));

    const select = screen.getByLabelText('Agents');
    expect(screen.getByRole('option', { name: 'claude' })).toBeInTheDocument();
    // Free text is impossible: the control is a closed list.
    expect(select.tagName).toBe('SELECT');

    fireEvent.change(select, { target: { value: 'codex' } });
    expect(values).toEqual(['codex']);
  });

  it('drops an already-selected value from the options and shows it as a chip', () => {
    setup(['claude'], () => {});

    expect(screen.getByText('claude')).toBeInTheDocument();
    expect(screen.queryByRole('option', { name: 'claude' })).not.toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'codex' })).toBeInTheDocument();
  });

  it('removes a value when its × button is clicked', () => {
    let values = ['claude'];
    setup(values, (next) => (values = next));

    fireEvent.click(screen.getByLabelText('Retirer claude'));

    expect(values).toEqual([]);
  });

  it('disables the dropdown once every value is selected', () => {
    setup(OPTIONS, () => {});

    expect(screen.getByLabelText('Agents')).toBeDisabled();
  });

  it('says so when the dimension has no value at all', () => {
    render(
      <OptionMultiSelect
        label="Agents"
        options={[]}
        values={[]}
        onChange={() => {}}
        placeholder="Choisir un agent..."
        emptyMessage="Aucun agent enregistré."
      />,
    );

    expect(screen.getByText('Aucun agent enregistré.')).toBeInTheDocument();
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

  it('counts an agent coming from the URL and resets every filter', async () => {
    renderRouted(<FilterBar />, {
      validateSearch: metricFiltersSchema,
      initialSearch: '?agents=claude',
    });

    expect(await screen.findByText('Filtres (1)')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Réinitialiser' }));

    await waitFor(() => expect(screen.getByText('Filtres')).toBeInTheDocument());
  });

  it('picks an agent from the dropdown into the URL filters', async () => {
    server.use(
      http.get('/api/metrics/dimensions', () =>
        HttpResponse.json({ agents: ['claude', 'codex'], models: [] }),
      ),
    );

    const { router } = renderRouted(<FilterBar />, { validateSearch: metricFiltersSchema });

    const select = await screen.findByLabelText('Agents');
    fireEvent.change(select, { target: { value: 'codex' } });

    await waitFor(() => {
      expect(router.state.location.search).toMatchObject({ agents: ['codex'] });
    });
  });
});
