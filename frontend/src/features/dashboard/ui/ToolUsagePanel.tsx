import { useState } from 'react';

import { ChartSkeleton, EmptyState, StackedBarChart } from '@shared/ui';
import { formatDuration, formatNumber, formatPercent } from '@shared/lib/format';

import type { ToolUsageItem } from '../api/dashboard.contracts';

/** Past a dozen bars the category axis is unreadable whatever the label length. */
const CHART_LIMIT = 12;
const ALL = '__all__';

/** Tool names run long (`mcp__sequential-thinking__sequentialthinking`). */
function shortenToolName(name: string): string {
  return name.length > 18 ? `${name.slice(0, 17)}…` : name;
}

function ToolDetail({ tool, totalCalls }: { tool: ToolUsageItem; totalCalls: number }) {
  const errorRate = tool.n_calls > 0 ? tool.n_errors / tool.n_calls : null;

  const stats = [
    { label: 'Appels', value: formatNumber(tool.n_calls) },
    { label: 'Part du volume', value: totalCalls > 0 ? formatPercent(tool.n_calls / totalCalls) : '—' },
    { label: 'Erreurs', value: `${formatNumber(tool.n_errors)} (${formatPercent(errorRate)})` },
    { label: 'Durée moyenne', value: formatDuration(tool.avg_duration_ms) },
  ];

  return (
    <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      {stats.map((stat) => (
        <div key={stat.label}>
          <dt className="text-[11px] uppercase tracking-wider text-foreground-muted">
            {stat.label}
          </dt>
          <dd className="mt-1 font-semibold tabular-nums text-foreground">{stat.value}</dd>
        </div>
      ))}
    </dl>
  );
}

/**
 * Tool breakdown, scoped by a dropdown. "Tous les outils" charts the busiest
 * dozen — a bar per tool would otherwise crowd the axis past reading. Picking
 * one tool swaps the chart for its figures, since a one-bar bar chart says less
 * than the numbers themselves.
 */
export function ToolUsagePanel({
  items,
  isLoading,
}: {
  items: ToolUsageItem[];
  isLoading: boolean;
}) {
  const [selected, setSelected] = useState<string>(ALL);

  if (isLoading) return <ChartSkeleton />;

  const sorted = [...items].sort((a, b) => b.n_calls - a.n_calls);
  const totalCalls = sorted.reduce((sum, item) => sum + item.n_calls, 0);
  const tool = sorted.find((item) => item.tool_name === selected);

  // A horizontal category axis renders the first row at the top, so the
  // descending sort already puts the busiest tool there.
  const chartData = sorted.slice(0, CHART_LIMIT).map((item) => ({
    category: item.tool_name,
    success: item.n_calls - item.n_errors,
    error: item.n_errors,
  }));

  return (
    <div>
      <label className="mb-3 flex flex-wrap items-center gap-2 text-xs text-foreground-muted">
        <span className="uppercase tracking-wider">Outil</span>
        <select
          className="cyber-field max-w-xs flex-1"
          value={selected}
          onChange={(event) => setSelected(event.target.value)}
        >
          <option value={ALL}>Tous les outils ({sorted.length})</option>
          {sorted.map((item) => (
            <option key={item.tool_name} value={item.tool_name}>
              {item.tool_name} — {formatNumber(item.n_calls)} appels
            </option>
          ))}
        </select>
      </label>

      {tool ? (
        <>
          <ToolDetail tool={tool} totalCalls={totalCalls} />
        </>
      ) : selected !== ALL ? (
        <EmptyState
          title="Outil introuvable"
          description="Cet outil n'apparaît pas dans le périmètre filtré."
        />
      ) : (
        <>
          <StackedBarChart
            data={chartData}
            series={[
              { key: 'success', label: 'Réussis' },
              { key: 'error', label: 'Erreurs', color: 'hsl(var(--danger))' },
            ]}
            orientation="rows"
            categoryFormatter={shortenToolName}
          />
        </>
      )}
    </div>
  );
}
