import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type MouseHandlerDataParam,
} from 'recharts';

import { CHART_COLORS } from './chart-colors';

export interface TimeSeriesPoint {
  period: string;
  value: number | null;
}

/**
 * Line chart for activity/tokens per day (I5.10). Takes already-shaped data
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
  function handleClick(state: MouseHandlerDataParam) {
    const period = state?.activeLabel;
    const point = typeof period === 'string' ? data.find((d) => d.period === period) : undefined;
    if (point) onPointClick?.(point);
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={data}
        margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
        onClick={onPointClick ? handleClick : undefined}
      >
        <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.border} />
        <XAxis dataKey="period" stroke={CHART_COLORS.foregroundMuted} fontSize={12} />
        <YAxis stroke={CHART_COLORS.foregroundMuted} fontSize={12} allowDecimals={false} />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="value"
          name={valueLabel}
          stroke={color}
          strokeWidth={2}
          dot={false}
          connectNulls={false}
          className={onPointClick ? 'cursor-pointer' : undefined}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
