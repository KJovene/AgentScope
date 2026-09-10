import type { ReactNode } from 'react';

import { cn } from '@shared/lib/cn';
import { Card } from '@shared/ui/Card';
import { EmptyState } from '@shared/ui/EmptyState';

/**
 * Shared container for every chart: HUD-style header, optional legend/actions
 * slot, and the "no data" state — so a feature never re-implements empty-state
 * handling (DRY). A chart with zero points reads as "non disponible", never as
 * an empty/zero graph.
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
      <div className="mb-3 flex items-center justify-between gap-3 border-b border-border pb-2.5">
        <h3 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.16em] text-neon-cyan neon-text-cyan">
          <span
            aria-hidden="true"
            className="inline-block h-1.5 w-1.5 shrink-0 animate-pulse-neon bg-neon-cyan"
          />
          {title}
        </h3>
        {actions}
      </div>

      <div className={cn('relative flex-1', !isEmpty && 'chart-reveal')}>
        {isEmpty ? (
          <EmptyState title="Aucune donnée disponible" description={emptyDescription} />
        ) : (
          children
        )}
      </div>
    </Card>
  );
}
