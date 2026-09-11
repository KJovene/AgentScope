/**
 * Closed-choice multi-value filter: a dropdown of the values that actually
 * exist, plus a chip per selection. Replaces free-text entry for dimensions
 * where a typo silently yields an empty dashboard.
 *
 * The dropdown itself stays unselected — picking an option adds a chip and the
 * control resets, so it reads as "add one more" rather than "current value".
 */
export function OptionMultiSelect({
  label,
  options,
  values,
  onChange,
  isLoading = false,
  placeholder,
  emptyMessage,
}: {
  label: string;
  options: string[];
  values: string[];
  onChange: (next: string[]) => void;
  isLoading?: boolean;
  placeholder: string;
  emptyMessage: string;
}) {
  // An already-picked value has its chip; offering it again would be a no-op.
  const available = options.filter((option) => !values.includes(option));

  function add(value: string) {
    if (value && !values.includes(value)) onChange([...values, value]);
  }

  function remove(value: string) {
    onChange(values.filter((v) => v !== value));
  }

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
        {label}
      </span>

      {values.length > 0 && (
        <div className="flex min-w-0 flex-wrap items-center gap-1">
          {values.map((value) => (
            <span
              key={value}
              className="inline-flex max-w-full items-center gap-1 border border-neon-cyan/50 bg-neon-cyan/10 px-2 py-0.5 text-xs text-foreground"
            >
              <span className="truncate">{value}</span>
              <button
                type="button"
                aria-label={`Retirer ${value}`}
                onClick={() => remove(value)}
                className="shrink-0 text-foreground-muted hover:text-neon-magenta"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {isLoading ? (
        <span className="text-xs text-foreground-muted">Chargement...</span>
      ) : options.length === 0 ? (
        <span className="text-xs text-foreground-muted">{emptyMessage}</span>
      ) : (
        <select
          aria-label={label}
          className="cyber-field min-w-0"
          value=""
          disabled={available.length === 0}
          onChange={(event) => {
            add(event.target.value);
            event.target.value = '';
          }}
        >
          <option value="">
            {available.length === 0 ? `Tous sélectionnés (${options.length})` : placeholder}
          </option>
          {available.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      )}
    </div>
  );
}
