import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { CHART_COLORS } from './chart-colors';

export interface TimeSeriesPoint {
  period: string;
  value: number | null;
}

/**
 * Line chart for activity/tokens per day (I5.10). Takes already-shaped data
 * from the feature's `api` layer — never fetches, never formats units itself.
 */
export function TimeSeriesChart({
  data,
  valueLabel,
  height = 280,
  color = CHART_COLORS.primary,
}: {
  data: TimeSeriesPoint[];
  valueLabel: string;
  height?: number;
  color?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
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
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
