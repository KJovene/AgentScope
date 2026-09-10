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
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
        Période
      </span>
      <div className="flex min-w-0 flex-col gap-2">
        <input
          type="date"
          aria-label="Date de début"
          value={toDateInputValue(from)}
          onChange={(e) => onChange({ from: fromDateInputValue(e.target.value, false), to })}
          className="cyber-field"
        />
        <input
          type="date"
          aria-label="Date de fin"
          value={toDateInputValue(to)}
          onChange={(e) => onChange({ from, to: fromDateInputValue(e.target.value, true) })}
          className="cyber-field"
        />
      </div>
    </div>
  );
}
