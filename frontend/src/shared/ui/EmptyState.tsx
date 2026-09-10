import { cn } from '@shared/lib/cn';

/**
 * Shown when data is genuinely absent — NOT a zero. The brief requires an
 * unavailable metric to read as "non disponible", never as 0.
 */
export function EmptyState({
  title = 'Donnée non disponible',
  description,
  className,
}: {
  title?: string;
  description?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center border border-dashed border-border-strong',
        'bg-surface-muted/40 p-6 text-center',
        className,
      )}
    >
      <p className="text-sm font-medium uppercase tracking-wider text-foreground-muted">{title}</p>
      {description && <p className="mt-1 text-xs text-foreground-muted">{description}</p>}
    </div>
  );
}
