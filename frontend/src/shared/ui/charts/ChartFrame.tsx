import type { ReactNode } from 'react';

import { cn } from '@shared/lib/cn';
import { Card, CardHeader, CardTitle } from '@shared/ui/Card';
import { EmptyState } from '@shared/ui/EmptyState';

/**
 * Shared container for every chart: title, optional legend/actions slot, and the
 * "no data" state — so a feature never re-implements empty-state handling (DRY).
 * A chart with zero points reads as "non disponible", never as an empty/zero graph.
 */
export function ChartFrame({
  title,
  actions,
  isEmpty,
  emptyDescription,
  className,
  children,
}: {
  title: string;
  actions?: ReactNode;
  isEmpty: boolean;
  emptyDescription?: string;
  className?: string;
  children: ReactNode;
}) {
  return (
    <Card className={cn('flex flex-col', className)}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {actions}
      </CardHeader>
      {isEmpty ? (
        <EmptyState title="Aucune donnée disponible" description={emptyDescription} />
      ) : (
        children
      )}
    </Card>
  );
}
