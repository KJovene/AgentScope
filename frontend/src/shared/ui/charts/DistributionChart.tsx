import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { CHART_COLORS } from './chart-colors';
import { buildDurationHistogram } from './duration-histogram';

/**
 * Histogram of session durations (I5.12). Takes raw duration values (ms) —
 * bins them client-side, since the backend has no dedicated distribution
 * endpoint. Sessions with no timing must be filtered out by the caller
 * (never treated as a 0ms duration).
 */
export function DistributionChart({
  values,
  bucketCount = 8,
  height = 280,
}: {
  values: number[];
  bucketCount?: number;
  height?: number;
}) {
  const data = buildDurationHistogram(values, bucketCount);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 24, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
        <XAxis
          dataKey="range"
          stroke={CHART_COLORS.foregroundMuted}
          fontSize={11}
          interval={0}
          angle={-30}
          textAnchor="end"
          height={50}
        />
        <YAxis stroke={CHART_COLORS.foregroundMuted} fontSize={12} allowDecimals={false} />
        <Tooltip />
        <Bar dataKey="count" name="Sessions" fill={CHART_COLORS.primary} />
      </BarChart>
    </ResponsiveContainer>
  );
}
