import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';

import {
  CHART_ANIM,
  CHART_AXIS_PROPS,
  CHART_COLORS,
  CHART_GRID_PROPS,
  CHART_SERIES_COLORS,
} from './chart-colors';
import { ChartTooltip } from './ChartTooltip';

export interface StackedBarSeries {
  key: string;
  label: string;
  color?: string;
}

export interface StackedBarDatum {
  category: string;
  [seriesKey: string]: string | number;
}

const LEGEND_STYLE = { fontFamily: 'inherit', fontSize: 11, textTransform: 'uppercase' as const };

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
      <BarChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }} barCategoryGap="28%">
        <CartesianGrid {...CHART_GRID_PROPS} />
        <XAxis dataKey="category" {...CHART_AXIS_PROPS} tickMargin={8} />
        <YAxis {...CHART_AXIS_PROPS} allowDecimals={false} tickMargin={8} width={44} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: CHART_COLORS.border, opacity: 0.35 }} />
        <Legend wrapperStyle={LEGEND_STYLE} />
        {series.map((s, index) => {
          const last = index === series.length - 1;
          return (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.label}
              stackId="stack"
              maxBarSize={56}
              radius={last ? [3, 3, 0, 0] : 0}
              fill={s.color ?? CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length]}
              {...CHART_ANIM}
            />
          );
        })}
      </BarChart>
    </ResponsiveContainer>
  );
}
