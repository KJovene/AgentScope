import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import { CHART_COLORS, CHART_SERIES_COLORS } from './chart-colors';

export interface StackedBarSeries {
  key: string;
  label: string;
  color?: string;
}

export interface StackedBarDatum {
  category: string;
  [seriesKey: string]: string | number;
}

/**
 * Stacked bar chart for a breakdown by category (e.g. tool usage success vs
 * error). Takes already-shaped data from the feature's `api` layer — never
 * fetches, never formats units itself.
 */
export function StackedBarChart({
  data,
  series,
  height = 280,
}: {
  data: StackedBarDatum[];
  series: StackedBarSeries[];
  height?: number;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
        <XAxis dataKey="category" stroke={CHART_COLORS.foregroundMuted} fontSize={12} />
        <YAxis stroke={CHART_COLORS.foregroundMuted} fontSize={12} allowDecimals={false} />
        <Tooltip />
        <Legend />
        {series.map((s, index) => (
          <Bar
            key={s.key}
            dataKey={s.key}
            name={s.label}
            stackId="stack"
            fill={s.color ?? CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
