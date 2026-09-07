import { createFileRoute } from '@tanstack/react-router';

import { ImportHistoryPage } from '@features/import';

export const Route = createFileRoute('/imports/')({
  component: ImportHistoryPage,
});
