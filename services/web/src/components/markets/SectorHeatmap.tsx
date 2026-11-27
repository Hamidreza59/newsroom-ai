import { fmtPct } from "@newsroom/brand";
import type { Sector } from "@/lib/contract";

const tint = (pct: number) => {
  const strength = Math.min(Math.abs(pct) / 4, 1);
  const mix = Math.round(14 + strength * 46);
  return `color-mix(in srgb, var(${pct >= 0 ? "--up" : "--down"}) ${mix}%, var(--surface-2))`;
};

export function SectorHeatmap({ sectors, compact = false }: { sectors: Sector[]; compact?: boolean }) {
  return (
    <div
      className="space-y-4"
      role="group"
      aria-label={`Sector heatmap: ${sectors.map((s) => `${s.name} ${fmtPct(s.changePct)}`).join(", ")}`}
    >
      {sectors.map((s) => (
        <div key={s.name}>
          <div className="mb-1.5 flex items-baseline justify-between">
            <h3 className="text-sm font-semibold">{s.name}</h3>
            <span className={`num text-xs font-medium ${s.changePct >= 0 ? "up" : "down"}`}>
              avg {fmtPct(s.changePct)}
            </span>
          </div>
          <ul className={`grid gap-1.5 ${compact ? "grid-cols-4" : "grid-cols-2 sm:grid-cols-4"}`}>
            {s.members.map((m) => (
              <li
                key={m.symbol}
                title={`${m.name} ${fmtPct(m.changePct)}`}
                className="flex flex-col items-center justify-center rounded-lg border border-line px-1 py-2.5 text-center"
                style={{ background: tint(m.changePct) }}
              >
                <span className="text-xs font-bold">{m.symbol}</span>
                <span className="num text-[0.7rem] font-medium">{fmtPct(m.changePct)}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

export function HeatmapLegend() {
  return (
    <div className="mt-3 flex items-center gap-2 text-[0.7rem] text-muted" aria-hidden="true">
      <span>−4%</span>
      <span
        className="h-2 flex-1 rounded-full"
        style={{ background: "linear-gradient(90deg, color-mix(in srgb, var(--down) 60%, var(--surface-2)), var(--surface-2), color-mix(in srgb, var(--up) 60%, var(--surface-2)))" }}
      />
      <span>+4%</span>
    </div>
  );
}

export function SectorBreadth({ sectors }: { sectors: Sector[] }) {
  const members = sectors.flatMap((s) => s.members);
  const up = members.filter((m) => m.changePct >= 0).length;
  const down = members.length - up;
  if (!members.length) return null;
  return (
    <div className="mt-auto border-t border-line pt-5">
      <div className="mb-2 flex items-baseline justify-between text-sm">
        <h3 className="font-semibold">Market breadth</h3>
        <span className="num text-xs text-muted">
          <span className="up font-medium">{up} advancing</span> · <span className="down font-medium">{down} declining</span>
        </span>
      </div>
      <div className="flex h-2 gap-0.5 overflow-hidden rounded-full" role="img" aria-label={`${up} advancing, ${down} declining`}>
        <span className="rounded-full" style={{ flex: up, background: "var(--up)" }} />
        <span className="rounded-full" style={{ flex: down, background: "var(--down)" }} />
      </div>
      <ul className="mt-4 grid grid-cols-3 gap-2">
        {sectors.map((s) => (
          <li key={s.name} className="rounded-lg border border-line bg-surface-2 px-3 py-2">
            <div className="truncate text-[0.7rem] text-muted">{s.name}</div>
            <div className={`num text-sm font-bold ${s.changePct >= 0 ? "up" : "down"}`}>{fmtPct(s.changePct)}</div>
          </li>
        ))}
      </ul>
    </div>
  );
}
