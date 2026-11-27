export function KpiTile({ label, value, hint, accent }: { label: string; value: string; hint?: string; accent: string }) {
  return (
    <div className="card relative overflow-hidden p-5">
      <span className="absolute inset-x-0 top-0 h-0.5" style={{ background: accent }} aria-hidden="true" />
      <div className="eyebrow">{label}</div>
      <div className="mt-2 truncate text-2xl font-bold tracking-tight" title={value}>{value}</div>
      {hint && <div className="mt-1 text-xs text-muted">{hint}</div>}
    </div>
  );
}
