import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useDebounce } from '@shared/hooks/use-debounce';
import { useDisclosure } from '@shared/hooks/use-disclosure';

describe('useDebounce', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('returns the initial value immediately, then the latest after the delay', () => {
    const { result, rerender } = renderHook(({ v }) => useDebounce(v, 200), {
      initialProps: { v: 'a' },
    });
    expect(result.current).toBe('a');

    rerender({ v: 'b' });
    expect(result.current).toBe('a');

    act(() => vi.advanceTimersByTime(199));
    expect(result.current).toBe('a');

    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe('b');
  });

  it('resets the timer when the value changes again before it fires', () => {
    const { result, rerender } = renderHook(({ v }) => useDebounce(v, 100), {
      initialProps: { v: 1 },
    });
    rerender({ v: 2 });
    act(() => vi.advanceTimersByTime(60));
    rerender({ v: 3 });
    act(() => vi.advanceTimersByTime(60));
    expect(result.current).toBe(1);
    act(() => vi.advanceTimersByTime(40));
    expect(result.current).toBe(3);
  });
});

describe('useDisclosure', () => {
  it('defaults closed and opens / closes / toggles', () => {
    const { result } = renderHook(() => useDisclosure());
    expect(result.current.isOpen).toBe(false);

    act(() => result.current.open());
    expect(result.current.isOpen).toBe(true);

    act(() => result.current.close());
    expect(result.current.isOpen).toBe(false);

    act(() => result.current.toggle());
    expect(result.current.isOpen).toBe(true);
  });

  it('honours the initial value', () => {
    const { result } = renderHook(() => useDisclosure(true));
    expect(result.current.isOpen).toBe(true);
  });
});
