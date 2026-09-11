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

const ROW_HEIGHT = 26;
const CHROME_HEIGHT = 60;

/**
 * Stacked bar chart for a breakdown by category (e.g. tool usage success vs
 * error). Takes already-shaped data from the feature's `api` layer — never
 * fetches, never formats units itself.
 *
 * `orientation="rows"` lays the bars horizontally. Prefer it as soon as the
 * categories are names rather than short codes: a column axis can only fit a
 * few characters per tick before labels collide or run past the card.
 */
export function StackedBarChart({
  data,
  series,
  height = 280,
  orientation = 'columns',
  categoryFormatter,
}: {
  data: StackedBarDatum[];
  series: StackedBarSeries[];
  height?: number;
  orientation?: 'columns' | 'rows';
  /** Shortens a long category so the tick never runs past the card edge. */
  categoryFormatter?: (category: string) => string;
}) {
  const rows = orientation === 'rows';
  // Rows grow with the data so the axis band is never squeezed into a scrollbar.
  const chartHeight = rows ? data.length * ROW_HEIGHT + CHROME_HEIGHT : height;

  const categoryAxis = {
    dataKey: 'category',
    ...CHART_AXIS_PROPS,
    tickMargin: 8,
    tickFormatter: categoryFormatter,
    interval: 0 as const,
  };
  const valueAxis = { ...CHART_AXIS_PROPS, allowDecimals: false, tickMargin: 8 };

  // Both axes stay DIRECT children of <BarChart>: Recharts reads its axis
  // configuration off its own children, and a <Fragment> wrapper hides them —
  // the ticks still draw, but the bars fall back to an implicit scale and
  // render a few pixels wide.
  const xAxisProps = rows
    ? ({ type: 'number', ...valueAxis, height: 28 } as const)
    : ({ ...categoryAxis, height: 28, minTickGap: 2 } as const);
  const yAxisProps = rows
    ? ({ type: 'category', ...categoryAxis, width: 132 } as const)
    : ({ ...valueAxis, width: 44 } as const);

  return (
    <ResponsiveContainer width="100%" height={chartHeight}>
      <BarChart
        data={data}
        layout={rows ? 'vertical' : 'horizontal'}
        margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
        barCategoryGap={rows ? '20%' : '28%'}
      >
        <CartesianGrid {...CHART_GRID_PROPS} vertical={rows} horizontal={!rows} />
        <XAxis {...xAxisProps} />
        <YAxis {...yAxisProps} />
        <Tooltip content={<ChartTooltip />} cursor={{ fill: CHART_COLORS.border, opacity: 0.35 }} />
        <Legend wrapperStyle={LEGEND_STYLE} />
        {series.map((s, index) => {
          const last = index === series.length - 1;
          const radius: [number, number, number, number] = rows ? [0, 3, 3, 0] : [3, 3, 0, 0];
          return (
            <Bar
              key={s.key}
              dataKey={s.key}
              name={s.label}
              stackId="stack"
              maxBarSize={rows ? 16 : 56}
              radius={last ? radius : 0}
              fill={s.color ?? CHART_SERIES_COLORS[index % CHART_SERIES_COLORS.length]}
              {...CHART_ANIM}
            />
          );
        })}
      </BarChart>
    </ResponsiveContainer>
  );
}
