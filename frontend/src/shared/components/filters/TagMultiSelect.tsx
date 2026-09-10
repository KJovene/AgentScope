import { useState } from 'react';

import { cn } from '@shared/lib/cn';

/**
 * Free-text multi-value input (type + Enter/comma to add, click × to remove).
 * Used for dimensions with no backend "list distinct values" endpoint
 * (agents, models) — `SourceFilter` uses a real list instead.
 */
export function TagMultiSelect({
  label,
  values,
  onChange,
  placeholder,
}: {
  label: string;
  values: string[];
  onChange: (next: string[]) => void;
  placeholder?: string;
}) {
  const [draft, setDraft] = useState('');

  function commit() {
    const value = draft.trim();
    if (value && !values.includes(value)) onChange([...values, value]);
    setDraft('');
  }

  function remove(value: string) {
    onChange(values.filter((v) => v !== value));
  }

  return (
    <div className="flex min-w-0 flex-col gap-1">
      <span className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
        {label}
      </span>
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
        <input
          type="text"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ',') {
              e.preventDefault();
              commit();
            }
          }}
          onBlur={commit}
          placeholder={placeholder}
          aria-label={label}
          className={cn('cyber-field w-full min-w-0 flex-1 basis-24')}
        />
      </div>
    </div>
  );
}
