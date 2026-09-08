import { createFileRoute } from '@tanstack/react-router';

import { metricFiltersSchema } from '@shared/lib/metric-filters';
import { SessionListPage } from '@features/session-detail';

export const Route = createFileRoute('/sessions/')({
  // Same shared filter state as the dashboard — a filtered link is shareable.
  validateSearch: metricFiltersSchema,
  component: SessionListPage,
});
