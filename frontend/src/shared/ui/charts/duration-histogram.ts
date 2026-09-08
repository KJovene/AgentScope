export interface HistogramBucket {
  range: string;
  count: number;
}

function formatMs(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)}ms` : `${(ms / 1000).toFixed(1)}s`;
}

/** Bins a list of durations (ms) into equal-width buckets for a histogram. */
export function buildDurationHistogram(values: number[], bucketCount = 8): HistogramBucket[] {
  if (values.length === 0) return [];

  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) return [{ range: formatMs(min), count: values.length }];

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

  return buckets.map((b) => ({ range: `${formatMs(b.start)}–${formatMs(b.end)}`, count: b.count }));
}
