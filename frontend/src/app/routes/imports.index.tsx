import { createFileRoute } from '@tanstack/react-router';
import { ImportHistoryScreen } from '@features/import';

export const Route = createFileRoute('/imports/')({
  component: ImportHistoryScreen,
});
