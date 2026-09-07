import { createFileRoute } from '@tanstack/react-router';

import { ImportReportPage } from '@features/import';

export const Route = createFileRoute('/imports/$importId')({
  component: ImportReportRoute,
});

function ImportReportRoute() {
  const { importId } = Route.useParams();
  return <ImportReportPage importId={importId} />;
}
