/**
 * Chart color palette — pulls from the same CSS variables as Tailwind's theme
 * tokens (`tailwind.config.ts` / `styles/index.css`) so charts never hard-code
 * hex values and stay in sync with light/dark theme.
 */
export const CHART_COLORS = {
  primary: 'hsl(var(--primary))',
  success: 'hsl(var(--success))',
  warning: 'hsl(var(--warning))',
  danger: 'hsl(var(--danger))',
  foregroundMuted: 'hsl(var(--foreground-muted))',
  border: 'hsl(var(--border))',
} as const;

/** Ordered palette for series/categories with no inherent semantic color. */
export const CHART_SERIES_COLORS: readonly string[] = [
  CHART_COLORS.primary,
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
];
