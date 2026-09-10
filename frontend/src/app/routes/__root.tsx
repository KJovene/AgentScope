import type { QueryClient } from '@tanstack/react-query';
import {
  Link,
  Outlet,
  createRootRouteWithContext,
  useRouterState,
} from '@tanstack/react-router';

import { AccessibilityPanel } from '@features/accessibility';
import { FloatingChat } from '@features/chat';
import { cn } from '@shared/lib/cn';
import { useUiStore } from '@shared/stores/ui-store';

export interface RouterContext {
  queryClient: QueryClient;
}

export const Route = createRootRouteWithContext<RouterContext>()({
  component: RootLayout,
});

const NAV = [
  { to: '/', label: 'Dashboard', glyph: '◈' },
  { to: '/imports', label: 'Imports', glyph: '⇩' },
  { to: '/sessions', label: 'Sessions', glyph: '⟐' },
  { to: '/sources/new', label: 'Source', glyph: '＋' },
] as const;

const NAV_LINK = cn(
  'flex items-center gap-3 border border-transparent px-3 py-2.5',
  'text-sm uppercase tracking-wider text-foreground-muted transition',
  'hover:border-border-strong hover:text-foreground',
  '[&.active]:border-neon-cyan [&.active]:text-neon-cyan [&.active]:neon-cyan',
);

function RootLayout() {
  const { theme, toggleTheme } = useUiStore();
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <div className="flex min-h-screen text-foreground">
      {/* Menu principal — barre verticale latérale */}
      <nav
        aria-label="Navigation principale"
        className="sticky top-0 flex h-screen w-16 shrink-0 flex-col items-stretch border-r border-border bg-surface md:w-56"
      >
        <div className="cyber-scanline edge-top-cyan flex items-center justify-center gap-2 border-b border-border px-3 py-4">
          <span aria-hidden="true" className="text-neon-cyan neon-text-cyan">
            ▲
          </span>
          <span className="hidden text-sm font-bold uppercase tracking-[0.2em] text-foreground md:inline">
            Agent<span className="text-neon-cyan neon-text-cyan">Scope</span>
          </span>
        </div>

        <ul className="stagger flex flex-1 flex-col gap-1 p-2">
          {NAV.map((item) => (
            <li key={item.to}>
              <Link to={item.to} className={NAV_LINK}>
                <span aria-hidden="true" className="text-base leading-none">
                  {item.glyph}
                </span>
                <span className="hidden md:inline">{item.label}</span>
              </Link>
            </li>
          ))}
        </ul>

        <div className="flex flex-col gap-1 border-t border-border p-2">
          <AccessibilityPanel />
          <button
            type="button"
            onClick={toggleTheme}
            className="flex items-center gap-3 border border-border px-3 py-2.5 text-sm uppercase tracking-wider text-foreground-muted transition hover:border-neon-magenta hover:text-neon-magenta"
            aria-label="Basculer le thème"
          >
            <span aria-hidden="true">{theme === 'light' ? '☾' : '☀'}</span>
            <span className="hidden md:inline">{theme === 'light' ? 'Dark' : 'Light'}</span>
          </button>
        </div>
      </nav>

      {/* Zone de contenu principale — refade à chaque changement de route */}
      <main className="min-w-0 flex-1 px-4 py-6 md:px-8">
        <div key={pathname} className="mx-auto max-w-6xl animate-fade-in">
          <Outlet />
        </div>
      </main>

      {/* Assistant flottant (bas-droite) */}
      <FloatingChat />
    </div>
  );
}
