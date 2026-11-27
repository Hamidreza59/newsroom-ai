const price = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const whole = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const compact = new Intl.NumberFormat("en-US", { notation: "compact", maximumFractionDigits: 1 });

export const fmtPrice = (v: number) => (v >= 10000 ? whole.format(v) : price.format(v));
export const fmtPct = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(2)}%`;
export const fmtChange = (v: number) => `${v >= 0 ? "+" : "−"}${price.format(Math.abs(v))}`;
export const fmtCompact = (v: number) => compact.format(v);
export const arrow = (v: number) => (v >= 0 ? "▲" : "▼");

export const fmtDate = (iso: string, opts: Intl.DateTimeFormatOptions) =>
  new Date(iso.length === 10 ? `${iso}T12:00:00Z` : iso).toLocaleDateString("en-US", {
    timeZone: "UTC",
    ...opts,
  });

export const fmtDuration = (seconds: number | null) => {
  if (seconds == null) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
};

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ["day", 86400],
  ["hour", 3600],
  ["minute", 60],
];
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto", style: "short" });

export const relativeTime = (iso: string, now: number = Date.now()) => {
  const diff = (new Date(iso).getTime() - now) / 1000;
  const abs = Math.abs(diff);
  if (abs < 60) return "just now";
  if (abs > 30 * 86400) return fmtDate(iso, { month: "short", day: "numeric" });
  for (const [unit, secs] of UNITS) {
    if (abs >= secs) return rtf.format(Math.trunc(diff / secs), unit);
  }
  return "just now";
};
