import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  CHART_ANIM,
  CHART_AXIS_PROPS,
  CHART_COLORS,
  CHART_GRID_PROPS,
  CHART_SERIES_COLORS,
} from './chart-colors';
import { ChartTooltip } from './ChartTooltip';

export interface BreakdownDatum {
  category: string;
  value: number;
  /** Share of the total, in [0, 1]. Rendered as the direct label at the bar end. */
  share: number;
}

const BAR_HEIGHT = 30;
const AXIS_BAND = 34;

/**
 * Horizontal bar chart for a part-to-whole breakdown by a nominal dimension
 * (agent, source, model). Categories have no natural order, so every bar wears
 * the SAME categorical hue — bar length already encodes magnitude, and a
 * value-ramp would burn the color channel on redundant information.
 *
 * The share is direct-labelled at the bar end so a value is never reachable by
 * tooltip alone.
 */
export function BreakdownBarChart({
  data,
  valueLabel,
  valueFormatter = (v) => String(v),
  color = CHART_SERIES_COLORS[0],
}: {
  data: BreakdownDatum[];
  valueLabel: string;
  valueFormatter?: (value: number) => string;
  color?: string;
}) {
  // Grow with the data instead of a fixed height, so the axis band is never
  // clipped into a nested scrollbar.
  const height = data.length * BAR_HEIGHT + AXIS_BAND;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart
        data={data}
        layout="vertical"
        margin={{ top: 4, right: 56, bottom: 0, left: 0 }}
        barCategoryGap="22%"
      >
        <CartesianGrid {...CHART_GRID_PROPS} vertical horizontal={false} />
        <XAxis type="number" {...CHART_AXIS_PROPS} tickMargin={8} allowDecimals={false} />
        <YAxis
          type="category"
          dataKey="category"
          {...CHART_AXIS_PROPS}
          width={124}
          tickMargin={6}
        />
        <Tooltip
          content={<ChartTooltip valueFormatter={(v) => valueFormatter(Number(v))} />}
          cursor={{ fill: CHART_COLORS.border, opacity: 0.35 }}
        />
        <Bar
          dataKey="value"
          name={valueLabel}
          fill={color}
          maxBarSize={18}
          radius={[0, 3, 3, 0]}
          {...CHART_ANIM}
        >
          <LabelList
            dataKey="share"
            position="right"
            offset={8}
            fill={CHART_COLORS.foregroundMuted}
            fontSize={11}
            formatter={(share: number) => `${(share * 100).toFixed(1)} %`}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
