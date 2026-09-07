# shared/components/filters

Presentational filter controls bound to `useMetricFilters()` (URL-synced).

Planned (WS-D front, issue I5.13):

- `FilterBar` — layout wrapper, "réinitialiser" action, active-filter count
- `SourceFilter`, `AgentFilter`, `ModelFilter` — multi-select, options from `GET /sources`
- `DateRangeFilter` — period, shown only when the data supports it

These write through `setFilters(...)`; they hold no local copy of the filter state.
