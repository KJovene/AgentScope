/**
 * Presentation formatting — the ONLY place numbers/dates become strings.
 *
 * Rule from the brief: a missing value is never shown as 0. Pass `null`/`undefined`
 * and every formatter returns `UNAVAILABLE` so the UI can style it distinctly.
 */
export const UNAVAILABLE = '—' as const;

type Maybe = number | null | undefined;

const isMissing = (v: Maybe): v is null | undefined => v === null || v === undefined || Number.isNaN(v);

const compact = new Intl.NumberFormat('fr-FR', { notation: 'compact', maximumFractionDigits: 1 });
const decimal = new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 });
const percentFmt = new Intl.NumberFormat('fr-FR', { style: 'percent', maximumFractionDigits: 1 });
const usdFmt = new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'USD' });

export function formatNumber(value: Maybe): string {
  return isMissing(value) ? UNAVAILABLE : decimal.format(value);
}

/** Tokens: compact ("12,3 k") above 10 000. */
export function formatTokens(value: Maybe): string {
  if (isMissing(value)) return UNAVAILABLE;
  return value >= 10_000 ? compact.format(value) : decimal.format(value);
}

export function formatUsd(value: Maybe): string {
  return isMissing(value) ? UNAVAILABLE : usdFmt.format(value);
}

/** Ratio in [0, 1] -> "42,0 %". */
export function formatPercent(ratio: Maybe): string {
  return isMissing(ratio) ? UNAVAILABLE : percentFmt.format(ratio);
}

/** Milliseconds -> "2 j 3 h" / "1 h 05 min" / "1 min 12 s" / "820 ms". */
export function formatDuration(ms: Maybe): string {
  if (isMissing(ms)) return UNAVAILABLE;
  if (ms < 1000) return `${decimal.format(ms)} ms`;

  const totalSeconds = Math.round(ms / 1000);
  const seconds = totalSeconds % 60;
  const totalMinutes = Math.floor(totalSeconds / 60);
  const minutes = totalMinutes % 60;
  const totalHours = Math.floor(totalMinutes / 60);
  const hours = totalHours % 24;
  const days = Math.floor(totalHours / 24);

  // Two units are enough to read a duration; more is noise.
  if (days > 0) return `${days} j ${hours} h`;
  if (totalHours > 0) return `${totalHours} h ${String(minutes).padStart(2, '0')} min`;
  if (totalMinutes > 0) return `${totalMinutes} min ${seconds} s`;
  return `${seconds} s`;
}

const dateTimeFmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium', timeStyle: 'short' });
const dateFmt = new Intl.DateTimeFormat('fr-FR', { dateStyle: 'medium' });

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? UNAVAILABLE : dateTimeFmt.format(d);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? UNAVAILABLE : dateFmt.format(d);
}
