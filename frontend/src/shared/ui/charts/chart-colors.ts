/**
 * Chart color palette — pulls from the same CSS variables as Tailwind's theme
 * tokens (`tailwind.config.ts` / `styles/index.css`) so charts never hard-code
 * hex values and stay in sync with light/dark theme and the "pure contrast"
 * accessibility mode.
 */
export const CHART_COLORS = {
  primary: 'hsl(var(--primary))',
  success: 'hsl(var(--success))',
  warning: 'hsl(var(--warning))',
  danger: 'hsl(var(--danger))',
  foreground: 'hsl(var(--foreground))',
  foregroundMuted: 'hsl(var(--foreground-muted))',
  border: 'hsl(var(--border))',
  borderStrong: 'hsl(var(--border-strong))',
  surface: 'hsl(var(--surface))',
} as const;

/**
 * Ordered palette for series/categories with no inherent semantic color.
 * `--chart-1..6` are an Okabe-Ito-derived set — distinct under deuteranopia,
 * protanopia and tritanopia — defined per theme in `styles/index.css`.
 */
export const CHART_SERIES_COLORS: readonly string[] = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
  'hsl(var(--chart-6))',
];

/** Shared axis config — monospace ticks, high-contrast baseline. */
export const CHART_AXIS_PROPS = {
  stroke: CHART_COLORS.borderStrong,
  tick: { fill: CHART_COLORS.foregroundMuted, fontSize: 11 },
  tickLine: { stroke: CHART_COLORS.border },
} as const;

/** Shared cartesian grid config — discreet but readable. */
export const CHART_GRID_PROPS = {
  stroke: CHART_COLORS.border,
  strokeDasharray: '2 4',
  vertical: false,
} as const;

/** Shared entrance animation for every series mark. */
export const CHART_ANIM = {
  isAnimationActive: true,
  animationDuration: 900,
  animationEasing: 'ease-out',
} as const;
