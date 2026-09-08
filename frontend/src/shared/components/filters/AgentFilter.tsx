import { TagMultiSelect } from './TagMultiSelect';

/** No `GET /agents` endpoint exists — free-text entry (see `TagMultiSelect`). */
export function AgentFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (next: string[]) => void;
}) {
  return (
    <TagMultiSelect
      label="Agents"
      values={values}
      onChange={onChange}
      placeholder="Ajouter un agent..."
    />
  );
}
