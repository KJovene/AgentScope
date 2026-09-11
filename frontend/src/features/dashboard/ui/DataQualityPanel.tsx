import type { DataQualityMetrics } from '../types';

export function DataQualityPanel({ metrics }: { metrics?: DataQualityMetrics }) {
  if (!metrics || metrics.sources.length === 0) {
    return <p>Aucune source de données analysée pour le moment.</p>;
  }

  return (
    <section>
      <div>
        <strong>{metrics.globalCompleteness}%</strong>
        <strong>{metrics.globalRejectionRate}%</strong>
      </div>
      <ul>
        {metrics.sources.map((source) => (
          <li key={source.id}>
            <h3>{source.sourceName}</h3>
            <p>{source.completeness.toFixed(1)}% complet</p>
            <p>{source.validRows}</p>
            <p>{source.rejectedRows}</p>
            {source.missingFields.map((field) => (
              <p key={field.field}>
                <span>{`⚠️ ${field.field}`}</span>{' '}
                <span>{`${field.percentage.toFixed(1)}% vide`}</span>
              </p>
            ))}
          </li>
        ))}
      </ul>
    </section>
  );
}
