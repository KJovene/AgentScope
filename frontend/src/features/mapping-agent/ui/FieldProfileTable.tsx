import { Card, CardHeader, CardTitle } from '@shared/ui';
import { formatNumber, formatPercent } from '@shared/lib/format';

import { type FieldProfileSetView } from '../model/analyze.mappers';

function renderSample(values: unknown[]): string {
  if (values.length === 0) return '—';
  return values.map((v) => (typeof v === 'string' ? v : JSON.stringify(v))).join(', ');
}

/** I5.5 — le profil des champs : types, taux de nuls, cardinalité, exemples. */
export function FieldProfileTable({ profile }: { profile: FieldProfileSetView }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>
          Profil des champs — {formatNumber(profile.recordCount)} enregistrement(s) analysé(s)
        </CardTitle>
      </CardHeader>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="text-xs uppercase text-foreground-muted">
            <tr>
              <th className="p-2">Champ</th>
              <th className="p-2">Type</th>
              <th className="p-2">% nuls</th>
              <th className="p-2">Distincts</th>
              <th className="p-2">Exemples</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {profile.fields.map((field) => (
              <tr key={field.path}>
                <td className="p-2 font-mono text-xs">{field.path}</td>
                <td className="p-2">{field.inferredType}</td>
                <td className="p-2">{formatPercent(field.nullRatio)}</td>
                <td className="p-2">{formatNumber(field.distinctCount)}</td>
                <td className="max-w-xs truncate p-2 text-xs text-foreground-muted">
                  {renderSample(field.sampleValues)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
