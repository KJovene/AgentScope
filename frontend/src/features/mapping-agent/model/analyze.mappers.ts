import { type FieldProfile, type FieldProfileSet } from '../api/analyze.contracts';

export interface FieldProfileRow {
  path: string;
  inferredType: string;
  nullRatio: number;
  distinctCount: number;
  sampleValues: unknown[];
}

export interface FieldProfileSetView {
  recordCount: number;
  fields: FieldProfileRow[];
}

function toFieldProfileRow(field: FieldProfile): FieldProfileRow {
  return {
    path: field.path,
    inferredType: field.inferred_type,
    nullRatio: field.null_ratio,
    distinctCount: field.distinct_count,
    sampleValues: field.sample_values,
  };
}

/** Wire DTO -> UI view model (camelCase). One place to map (DRY). */
export function toFieldProfileSetView(profile: FieldProfileSet): FieldProfileSetView {
  return {
    recordCount: profile.record_count,
    fields: profile.fields.map(toFieldProfileRow),
  };
}
