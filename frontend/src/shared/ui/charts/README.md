# shared/ui/charts

Themed, reusable chart wrappers (Recharts) so features never configure axes,
tooltips, colors or the "no data" state twice.

| Export | What it draws |
| --- | --- |
| `ChartFrame` | Shared container: title, legend slot, `<EmptyState />` when there is no data |
| `TimeSeriesChart` | Activity / tokens over time |
| `StackedBarChart` | Stacked breakdown (tokens per model, calls per agent) |
| `BreakdownBarChart` | Single-series ranking (tool usage, error rate per tool) |
| `DistributionChart` | Session-duration histogram, fed by `buildDurationHistogram` |
| `ProportionBar` | One-line share bar (cache read / write / miss) |
| `ChartTooltip` | The single tooltip used by every chart |
| `chart-colors.ts` | `CHART_COLORS`, `CHART_SERIES_COLORS`, `CHART_AXIS_PROPS`, `CHART_GRID_PROPS` |
| `duration-histogram.ts` | Pure bucketing helper (`HistogramBucket`), unit-tested on its own |

Each wrapper takes already-shaped data from the feature `model/` layer and pulls
colors from the Tailwind theme tokens — **no hex values in feature code**.

Two rules they enforce for free:

- **Missing is not zero.** A series with nothing to show renders `EmptyState`, never a flat
  zero line — same contract as the backend (`docs/data/indicators.md`).
- **Sessions without timing are excluded and said so**, rather than defaulted to a duration.
