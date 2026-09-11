# shared/components/filters

Presentational filter controls bound to `useMetricFilters()` — the filter state lives in the
route's URL search params, so a filtered dashboard is shareable by copy-pasting the address.

| Export | Role |
| --- | --- |
| `FilterBar` | Layout wrapper, "réinitialiser" action, active-filter count |
| `SourceFilter` · `AgentFilter` · `ModelFilter` | Multi-select; options come from `GET /api/v1/sources` and `GET /api/v1/metrics/dimensions` — only values that actually exist in the data |
| `DateRangeFilter` | Period bounds (`from` inclusive, `to` exclusive), shown only when the data supports it |
| `OptionMultiSelect` | The shared primitive the three multi-selects are built on |

These write through `setFilters(...)`; they hold **no local copy** of the filter state. A change
updates indicators, charts and drill-down together, because everything reads the same
`MetricFilter` (see `docs/data/indicators.md` § "Les filtres communs").
