import type { QueryClient } from '@tanstack/react-query';
import { Link, Outlet, createRootRouteWithContext } from '@tanstack/react-router';

import { cn } from '@shared/lib/cn';
import { useUiStore } from '@shared/stores/ui-store';

export interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

const NAV = [
  { to: '/', label: 'Dashboard' },
  { to: '/imports', label: 'Imports' },
  { to: '/sources/new', label: 'Ajouter une source' },
] as const;

function RootLayout() {
  const { theme, toggleTheme } = useUiStore();

  return (
    <div className="min-h-screen bg-surface-muted text-foreground">
      <header className="border-b border-border bg-surface">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-4 py-3">
          <span className="text-sm font-bold">AgentScope</span>
          <nav className="flex gap-1">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'rounded-md px-3 py-1.5 text-sm text-foreground-muted hover:bg-surface-muted',
                  '[&.active]:bg-surface-muted [&.active]:font-medium [&.active]:text-foreground',
                )}
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <button
            type="button"
            onClick={toggleTheme}
            className="ml-auto rounded-md px-2 py-1 text-sm text-foreground-muted hover:bg-surface-muted"
            aria-label="Basculer le thème"
          >
            {theme === 'light' ? '🌙' : '☀️'}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
