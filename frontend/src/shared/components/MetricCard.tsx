import { Card } from '@shared/ui';
import { UNAVAILABLE } from '@shared/lib/format';
import { cn } from '@shared/lib/cn';

/**
 * One dashboard KPI. `value` is already formatted by the feature (via shared/lib/format),
 * so a missing metric arrives here as "—" and is styled as unavailable, never as 0.
 */
export function MetricCard({
  label,
  value,
  hint,
  definitionId,
  className,
}: {
  label: string;
  value: string;
  hint?: string;
  /** Anchor into docs/data/indicators.md for the accessible definition. */
  definitionId?: string;
  className?: string;
}) {
  const unavailable = value === UNAVAILABLE;

  return (
    <Card className={cn('flex flex-col gap-1', className)}>
      <div className="flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-foreground-muted">
        <span>{label}</span>
        {definitionId && (
          <a
            href={`/docs/data/indicators.md#${definitionId}`}
            target="_blank"
            rel="noreferrer"
            className="text-primary hover:underline"
            aria-label={`Définition de ${label}`}
          >
            ⓘ
          </a>
        )}
      </div>
      <div
        className={cn('text-2xl font-semibold', unavailable ? 'text-foreground-muted' : 'text-foreground')}
      >
        {value}
      </div>
      {hint && <div className="text-xs text-foreground-muted">{hint}</div>}
    </Card>
  );
}
