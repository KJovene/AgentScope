import { createFileRoute } from '@tanstack/react-router';

import { metricFiltersSchema } from '@shared/lib/metric-filters';
import { DashboardScreen } from '@features/dashboard/ui/DashboardScreen.tsx';

export const Route = createFileRoute('/')({
  // Dashboard filters are URL search params so a filtered view is shareable.
  validateSearch: metricFiltersSchema,
  component: DashboardScreen,
});
