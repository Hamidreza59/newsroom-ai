import Link from "next/link";
import { StatTile } from "@/components/ui/StatTile";
import type { MarketOverview } from "@/lib/contract";
import { SectorHeatmap } from "./SectorHeatmap";

export function MarketOverviewPanel({ markets }: { markets: MarketOverview }) {
  return (
    <section aria-labelledby="mo-heading" className="flex flex-col gap-3">
      <div className="flex items-end justify-between">
        <h2 id="mo-heading" className="text-lg font-bold tracking-tight">Market overview</h2>
        <Link href="/markets" className="text-sm font-medium text-muted hover:text-ink">Full markets →</Link>
      </div>
      <div className="grid gap-3">
        {markets.indices.map((q) => (
          <StatTile key={q.symbol} quote={q} compact />
        ))}
      </div>
      <div className="card p-4">
        <h3 className="eyebrow mb-3">Sector heatmap</h3>
        <SectorHeatmap sectors={markets.sectors.slice(0, 2)} compact />
      </div>
      {markets.sampleData && <p className="text-xs text-muted">Sample data for preview.</p>}
    </section>
  );
}
