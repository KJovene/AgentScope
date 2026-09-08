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
  const width = 640;
  const padding = { top: 8, right: 16, bottom: 28, left: 40 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;
  const values = data.map(({ value }) => value).filter((value): value is number => value !== null);
  const max = Math.max(...values, 0);
  const min = Math.min(...values, 0);
  const range = max - min || 1;
  const x = (index: number) =>
    padding.left + (data.length > 1 ? (index / (data.length - 1)) * chartWidth : chartWidth / 2);
  const y = (value: number) => padding.top + ((max - value) / range) * chartHeight;

  return (
    <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} role="img" aria-label={valueLabel}>
      <g stroke={CHART_COLORS.border} strokeDasharray="3 3">
        {[0, 0.5, 1].map((fraction) => (
          <line key={fraction} x1={padding.left} x2={width - padding.right} y1={padding.top + fraction * chartHeight} y2={padding.top + fraction * chartHeight} />
        ))}
      </g>
      <g fill={CHART_COLORS.foregroundMuted} fontSize="12">
        {data.map((point, index) => (
          <text key={`${point.period}-${index}`} x={x(index)} y={height - 8} textAnchor="middle">{point.period}</text>
        ))}
      </g>
      <path
        d={data.reduce((path, point, index) => {
          if (point.value === null) return path;
          return `${path}${path && data[index - 1]?.value !== null ? ' L' : ' M'}${x(index)} ${y(point.value)}`;
        }, '')}
        fill="none"
        stroke={color}
        strokeWidth="2"
      />
    </svg>
  );
}
