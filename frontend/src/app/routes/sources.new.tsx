import { createFileRoute } from '@tanstack/react-router';

import { AddSourcePage } from '@features/mapping-agent';

export const Route = createFileRoute('/sources/new')({
  component: AddSourcePage,
});
