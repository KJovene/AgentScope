import { useFilterDimensionsQuery } from '@shared/api/dimensions.queries';

import { OptionMultiSelect } from './OptionMultiSelect';

/** Closed choice over the models present in the data (`GET /metrics/dimensions`). */
export function ModelFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (next: string[]) => void;
}) {
  const { data, isLoading } = useFilterDimensionsQuery();

  return (
    <OptionMultiSelect
      label="Modèles"
      options={data?.models ?? []}
      values={values}
      onChange={onChange}
      isLoading={isLoading}
      placeholder="Choisir un modèle..."
      emptyMessage="Aucun modèle enregistré."
    />
  );
}
