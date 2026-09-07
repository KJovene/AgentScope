import { EmptyState } from '@shared/ui';

/**
 * Data-quality panel embedded in the dashboard: completeness, rejects and missing
 * fields per source. Issue I5.16. Consumes `GET /data-quality`.
 */
export function DataQualityPanel() {
  return (
    <EmptyState
      title="Qualité des données à venir"
      description="Complétude, rejets et champs manquants par source."
    />
  );
}
