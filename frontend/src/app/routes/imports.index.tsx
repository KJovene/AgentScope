import { createFileRoute } from '@tanstack/react-router';

import { ImportHistoryScreen, ImportScreen } from '@features/import';
import { PageHeader } from '@shared/components/PageHeader';

function ImportsPage() {
  return (
    <div className="stagger space-y-8">
      <PageHeader
        title="Imports"
        description="Téléversez de nouvelles traces à gauche, suivez l'historique des lots à droite."
      />
      <div className="grid gap-8 lg:grid-cols-[minmax(0,22rem)_minmax(0,1fr)] xl:grid-cols-[minmax(0,26rem)_minmax(0,1fr)]">
        <div className="lg:sticky lg:top-6 lg:self-start">
          <ImportScreen />
        </div>
        <ImportHistoryScreen />
      </div>
    </div>
  );
}

export const Route = createFileRoute('/imports/')({
  component: ImportsPage,
});
