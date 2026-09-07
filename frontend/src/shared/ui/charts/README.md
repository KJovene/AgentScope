# shared/ui/charts

Themed, reusable chart wrappers (Recharts) so features never configure axes,
tooltips, colors or the "no data" state twice.

Planned primitives (WS-D front, issues I5.10–I5.12):

- `TimeSeriesChart` — activité / tokens par jour
- `StackedBarChart` — répartition (outils, tokens par modèle)
- `DistributionChart` — durée des sessions (histogramme / box)
- `ChartFrame` — shared container: title, legend slot, `<EmptyState />` when `data.length === 0`

Each wrapper takes already-shaped data from the feature `model/` layer and pulls
colors from the Tailwind theme tokens — no hex values in feature code.
