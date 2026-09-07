import { useCallback } from 'react';

import { useNavigate, useSearch } from '@tanstack/react-router';

import { type MetricFilters } from '@shared/lib/metric-filters';

/**
 * Read/update the dashboard filters that live in the URL search params.
 * Any route that renders filtered data validates `metricFiltersSchema` in its
 * `validateSearch`, so `useSearch({ strict: false })` is already typed there.
 */
export function useMetricFilters() {
  const filters = useSearch({ strict: false }) as MetricFilters;
  const navigate = useNavigate();

  const setFilters = useCallback(
    (patch: Partial<MetricFilters>) => {
      void navigate({
        // stay on the current route, merge the patch into existing search
        to: '.',
        search: (prev) => ({ ...prev, ...patch }),
        replace: true,
      });
    },
    [navigate],
  );

  const reset = useCallback(() => {
    void navigate({ to: '.', search: {}, replace: true });
  }, [navigate]);

  return { filters, setFilters, reset };
}
