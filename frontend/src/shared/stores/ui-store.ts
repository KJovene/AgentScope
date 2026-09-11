import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * GLOBAL CLIENT state only (theme, layout chrome, accessibility prefs). Server
 * data lives in TanStack Query; URL-shareable state (dashboard filters) lives in
 * the URL. Keep this store small so there is one obvious home for each kind of
 * state.
 */
type Theme = 'light' | 'dark';
export type FontScale = 'normal' | 'large' | 'xl';

interface UiState {
  theme: Theme;
  sidebarOpen: boolean;
  /** Accessibility: typographic scale (drives `--font-scale`). */
  fontScale: FontScale;
  /** Accessibility: "Mode contraste pur" — disable all neon glow / bloom. */
  pureContrast: boolean;
  /** Accessibility: reduce / disable non-essential animations. */
  reduceMotion: boolean;
  toggleTheme: () => void;
  setSidebarOpen: (open: boolean) => void;
  setFontScale: (scale: FontScale) => void;
  togglePureContrast: () => void;
  toggleReduceMotion: () => void;
}

/** Reflect the current accessibility/theme prefs onto <html data-*>. */
export function applyUiPrefs(state: {
  theme: Theme;
  fontScale: FontScale;
  pureContrast: boolean;
  reduceMotion: boolean;
}): void {
  const root = document.documentElement;
  root.dataset.theme = state.theme;
  root.dataset.fontScale = state.fontScale === 'normal' ? '' : state.fontScale;
  root.dataset.fx = state.pureContrast ? 'off' : 'on';
  root.dataset.motion = state.reduceMotion ? 'reduced' : 'normal';
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      fontScale: 'normal',
      pureContrast: false,
      reduceMotion: false,
      toggleTheme: () =>
        set((s) => {
          const theme = s.theme === 'light' ? 'dark' : 'light';
          applyUiPrefs({ ...s, theme });
          return { theme };
        }),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
      setFontScale: (fontScale) =>
        set((s) => {
          applyUiPrefs({ ...s, fontScale });
          return { fontScale };
        }),
      togglePureContrast: () =>
        set((s) => {
          const pureContrast = !s.pureContrast;
          applyUiPrefs({ ...s, pureContrast });
          return { pureContrast };
        }),
      toggleReduceMotion: () =>
        set((s) => {
          const reduceMotion = !s.reduceMotion;
          applyUiPrefs({ ...s, reduceMotion });
          return { reduceMotion };
        }),
    }),
    {
      name: 'agentscope.ui',
      onRehydrateStorage: () => (state) => {
        if (state) applyUiPrefs(state);
      },
    },
  ),
);
