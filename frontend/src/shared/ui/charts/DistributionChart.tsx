import { useId } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { CHART_ANIM, CHART_AXIS_PROPS, CHART_COLORS, CHART_GRID_PROPS } from './chart-colors';
import { ChartTooltip } from './ChartTooltip';
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
  const gradientId = useId();
  // The tick is a lower bound; the tooltip restores the full span.
  const spanByLabel = new Map(data.map((bucket) => [bucket.label, bucket.range]));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 20, bottom: 0, left: 0 }} barCategoryGap="20%">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={CHART_COLORS.primary} stopOpacity={0.95} />
            <stop offset="100%" stopColor={CHART_COLORS.primary} stopOpacity={0.35} />
          </linearGradient>
        </defs>
        <CartesianGrid {...CHART_GRID_PROPS} />
        <XAxis
          dataKey="label"
          {...CHART_AXIS_PROPS}
          interval="preserveStartEnd"
          minTickGap={4}
          height={28}
          tickMargin={8}
        />
        <YAxis {...CHART_AXIS_PROPS} allowDecimals={false} tickMargin={8} width={44} />
        <Tooltip
          content={<ChartTooltip labelFormatter={(l) => spanByLabel.get(String(l)) ?? l} />}
          cursor={{ fill: CHART_COLORS.border, opacity: 0.35 }}
        />
        <Bar
          dataKey="count"
          name="Sessions"
          fill={`url(#${gradientId})`}
          radius={[3, 3, 0, 0]}
          maxBarSize={64}
          className="chart-glow"
          {...CHART_ANIM}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
