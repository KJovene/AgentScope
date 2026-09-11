import { useFilterDimensionsQuery } from '@shared/api/dimensions.queries';

import { OptionMultiSelect } from './OptionMultiSelect';

/** Closed choice over the agents present in the data (`GET /metrics/dimensions`). */
export function AgentFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (next: string[]) => void;
}) {
  const { data, isLoading } = useFilterDimensionsQuery();

  return (
    <OptionMultiSelect
      label="Agents"
      options={data?.agents ?? []}
      values={values}
      onChange={onChange}
      isLoading={isLoading}
      placeholder="Choisir un agent..."
      emptyMessage="Aucun agent enregistré."
    />
  );
}
