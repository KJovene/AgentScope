function toDateInputValue(iso?: string): string {
  return iso ? iso.slice(0, 10) : '';
}

function fromDateInputValue(value: string, endOfDay: boolean): string | undefined {
  if (!value) return undefined;
  return `${value}T${endOfDay ? '23:59:59' : '00:00:00'}Z`;
}

/** Two native date inputs, mapped to/from the ISO datetime strings the API expects. */
export function DateRangeFilter({
  from,
  to,
  onChange,
}: {
  from?: string;
  to?: string;
  onChange: (next: { from?: string; to?: string }) => void;
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
        Période
      </span>
      <div className="flex items-center gap-2">
        <input
          type="date"
          aria-label="Date de début"
          value={toDateInputValue(from)}
          onChange={(e) => onChange({ from: fromDateInputValue(e.target.value, false), to })}
          className="rounded-md border border-border bg-surface px-2 py-1 text-sm"
        />
        <span className="text-xs text-foreground-muted">à</span>
        <input
          type="date"
          aria-label="Date de fin"
          value={toDateInputValue(to)}
          onChange={(e) => onChange({ from, to: fromDateInputValue(e.target.value, true) })}
          className="rounded-md border border-border bg-surface px-2 py-1 text-sm"
        />
      </div>
    </div>
  );
}
