export interface HistogramBucket {
  /** Full bucket span, e.g. "2 h – 6 h". Shown in the tooltip. */
  range: string;
  /** Short lower-bound label for the axis tick, e.g. "2 h". */
  label: string;
  count: number;
}

/**
 * One unit, no decimals — an axis tick has room for "6 j", never for
 * "598540.8s". The exact span stays readable in `range`.
 */
function compactMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)} ms`;
  const seconds = ms / 1000;
  if (seconds < 60) return `${Math.round(seconds)} s`;
  const minutes = seconds / 60;
  if (minutes < 60) return `${Math.round(minutes)} min`;
  const hours = minutes / 60;
  if (hours < 24) return `${Math.round(hours)} h`;
  return `${Math.round(hours / 24)} j`;
}

/** Bins a list of durations (ms) into equal-width buckets for a histogram. */
export function buildDurationHistogram(values: number[], bucketCount = 8): HistogramBucket[] {
  if (values.length === 0) return [];

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    const only = compactMs(min);
    return [{ range: only, label: only, count: values.length }];
  }

  const width = (max - min) / bucketCount;
  const buckets = Array.from({ length: bucketCount }, (_, i) => ({
    start: min + i * width,
    end: min + (i + 1) * width,
    count: 0,
  }));

  for (const value of values) {
    const index = Math.min(bucketCount - 1, Math.floor((value - min) / width));
    buckets[index]!.count += 1;
  }

  return buckets.map((b) => ({
    range: `${compactMs(b.start)} – ${compactMs(b.end)}`,
    label: compactMs(b.start),
    count: b.count,
  }));
}
