import { act } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { useUiStore } from '@shared/stores/ui-store';

describe('useUiStore', () => {
  beforeEach(() => {
    act(() => useUiStore.setState({ theme: 'light', sidebarOpen: true }));
    delete document.documentElement.dataset.theme;
  });

  it('toggleTheme flips the theme and reflects it on <html data-theme>', () => {
    act(() => useUiStore.getState().toggleTheme());
    expect(useUiStore.getState().theme).toBe('dark');
    expect(document.documentElement.dataset.theme).toBe('dark');

    act(() => useUiStore.getState().toggleTheme());
    expect(useUiStore.getState().theme).toBe('light');
    expect(document.documentElement.dataset.theme).toBe('light');
  });

  it('setSidebarOpen updates the flag', () => {
    act(() => useUiStore.getState().setSidebarOpen(false));
    expect(useUiStore.getState().sidebarOpen).toBe(false);
  });
});
