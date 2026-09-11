import { useId } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type MouseHandlerDataParam,
} from 'recharts';

import { CHART_ANIM, CHART_AXIS_PROPS, CHART_COLORS, CHART_GRID_PROPS } from './chart-colors';
import { ChartTooltip } from './ChartTooltip';

export interface TimeSeriesPoint {
  period: string;
  value: number | null;
}

/**
 * Area/line chart for activity/tokens per day (I5.10). Takes already-shaped data
 * from the feature's `api` layer — never fetches, never formats units itself.
 * `onPointClick` powers drill-down (I5.14): click a point, get its datum back.
 */
export function TimeSeriesChart({
  data,
  valueLabel,
  height = 280,
  color = CHART_COLORS.primary,
  onPointClick,
}: {
  data: TimeSeriesPoint[];
  valueLabel: string;
  height?: number;
  color?: string;
  onPointClick?: (point: TimeSeriesPoint) => void;
}) {
  const gradientId = useId();

  function handleClick(state: MouseHandlerDataParam) {
    const period = state?.activeLabel;
    const point = typeof period === 'string' ? data.find((d) => d.period === period) : undefined;
    if (point) onPointClick?.(point);
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={data}
        margin={{ top: 8, right: 44, bottom: 0, left: 0 }}
        onClick={onPointClick ? handleClick : undefined}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.35} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid {...CHART_GRID_PROPS} />
        {/* A dense daily series must thin its ticks, or the last date collides
            with the card edge and neighbouring labels overlap. */}
        <XAxis
          dataKey="period"
          {...CHART_AXIS_PROPS}
          tickMargin={8}
          height={28}
          minTickGap={48}
          interval="preserveStartEnd"
        />
        <YAxis {...CHART_AXIS_PROPS} allowDecimals={false} tickMargin={8} width={44} />
        <Tooltip
          content={<ChartTooltip />}
          cursor={{ stroke: CHART_COLORS.borderStrong, strokeDasharray: '3 3' }}
        />
        <Area
          type="monotone"
          dataKey="value"
          name={valueLabel}
          stroke={color}
          strokeWidth={2}
          fill={`url(#${gradientId})`}
          dot={false}
          activeDot={{ r: 4, strokeWidth: 2, stroke: CHART_COLORS.surface }}
          connectNulls={false}
          className={onPointClick ? 'chart-glow cursor-pointer' : 'chart-glow'}
          {...CHART_ANIM}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
