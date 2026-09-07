import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * GLOBAL CLIENT state only (theme, layout chrome). Server data lives in TanStack
 * Query; URL-shareable state (dashboard filters) lives in the URL. Keep this store
 * small so there is one obvious home for each kind of state.
 */
type Theme = 'light' | 'dark';

interface UiState {
  theme: Theme;
  sidebarOpen: boolean;
  toggleTheme: () => void;
  setSidebarOpen: (open: boolean) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      theme: 'light',
      sidebarOpen: true,
      toggleTheme: () =>
        set((s) => {
          const theme = s.theme === 'light' ? 'dark' : 'light';
          document.documentElement.dataset.theme = theme;
          return { theme };
        }),
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
    }),
    {
      name: 'agentscope.ui',
      onRehydrateStorage: () => (state) => {
        if (state) document.documentElement.dataset.theme = state.theme;
      },
    },
  ),
);
