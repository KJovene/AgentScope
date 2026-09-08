import { createFileRoute } from '@tanstack/react-router';

import { ImportHistoryScreen, ImportScreen } from '@features/import';

function ImportsPage() {
  return (
    <div className="space-y-10">
      <ImportScreen />
      <ImportHistoryScreen />
    </div>
  );
}

export const Route = createFileRoute('/imports/')({
  component: ImportsPage,
});
