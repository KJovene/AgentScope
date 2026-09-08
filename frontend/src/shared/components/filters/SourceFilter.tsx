import { useSourcesQuery } from '@shared/api/sources.queries';

/** Multi-select over the real source registry (`GET /sources`). */
export function SourceFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (next: string[]) => void;
}) {
  const { data: sources, isLoading } = useSourcesQuery();

  function toggle(name: string) {
    onChange(values.includes(name) ? values.filter((v) => v !== name) : [...values, name]);
  }

  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="text-xs font-medium uppercase tracking-wide text-foreground-muted">
        Sources
      </legend>
      {isLoading ? (
        <span className="text-xs text-foreground-muted">Chargement...</span>
      ) : !sources || sources.length === 0 ? (
        <span className="text-xs text-foreground-muted">Aucune source enregistrée.</span>
      ) : (
        <div className="flex flex-wrap gap-x-3 gap-y-1">
          {sources.map((source) => (
            <label key={source.id} className="flex items-center gap-1.5 text-sm">
              <input
                type="checkbox"
                checked={values.includes(source.name)}
                onChange={() => toggle(source.name)}
              />
              {source.name}
            </label>
          ))}
        </div>
      )}
    </fieldset>
  );
}
