import { createFileRoute } from '@tanstack/react-router';

import { ImportHistoryScreen } from '@features/import/ui/ImportHistoryScreen';

export const Route = createFileRoute('/imports/')({
  component: ImportHistoryScreen,
});
