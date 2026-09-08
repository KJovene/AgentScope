import { TagMultiSelect } from './TagMultiSelect';

/** No `GET /models` endpoint exists — free-text entry (see `TagMultiSelect`). */
export function ModelFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <TagMultiSelect
      label="Modèles"
      values={values}
      onChange={onChange}
      placeholder="Ajouter un modèle..."
    />
  );
}
