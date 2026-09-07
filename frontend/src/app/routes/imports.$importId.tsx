import { createFileRoute } from '@tanstack/react-router';

import { ImportReportPage } from '@features/import';

export const Route = createFileRoute('/imports/$importId')({
  component: () => {
    const { importId } = Route.useParams();
    return <ImportReportPage importId={importId} />;
  },
});
