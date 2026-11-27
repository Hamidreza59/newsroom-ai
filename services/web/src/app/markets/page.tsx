import type { Metadata } from "next";
import { categories } from "@newsroom/brand";
import { MoversChart } from "@/components/charts/MoversChart";
import { HeatmapLegend, SectorBreadth, SectorHeatmap } from "@/components/markets/SectorHeatmap";
import { MarketsExplorer } from "@/components/markets/MarketsExplorer";
import { Watchlist } from "@/components/markets/Watchlist";
import { StoryCard } from "@/components/news/StoryCard";
import { PageHeader, SectionHeader } from "@/components/ui/Section";
import { StatTile } from "@/components/ui/StatTile";
import { Unavailable } from "@/components/ui/Unavailable";
import { getMarkets, getNews } from "@/lib/api";

export const metadata: Metadata = {
  title: "Markets",
  description: categories.markets.description,
  openGraph: { title: "Markets" },
};

export default async function MarketsPage() {
  const [markets, news] = await Promise.all([getMarkets(), getNews("markets", 12)]);
  const cat = categories.markets;
  if (!markets) {
    return (
      <>
        <PageHeader title="Markets" description={cat.description} accent={cat.color} />
        <Unavailable what="Market data" />
      </>
    );
  }
  return (
    <div className="space-y-12">
      <PageHeader title="Markets" description={cat.description} accent={cat.color} eyebrow={`As of ${markets.asOf}`}>
        {markets.sampleData && <p className="mt-3 text-xs text-muted">Showing sample data.</p>}
      </PageHeader>

      <div className="-mt-4 grid gap-4 sm:grid-cols-3">
        {markets.indices.map((q) => <StatTile key={q.symbol} quote={q} />)}
      </div>

      <MarketsExplorer indices={markets.indices} watchlist={markets.watchlist} />

      <div className="grid gap-6 lg:grid-cols-12">
        <section className="card flex flex-col p-5 sm:p-6 lg:col-span-7" aria-labelledby="heatmap-h">
          <h2 id="heatmap-h" className="mb-4 text-lg font-bold tracking-tight">Sector heatmap</h2>
          <SectorHeatmap sectors={markets.sectors} />
          <HeatmapLegend />
          <div className="h-5" />
          <SectorBreadth sectors={markets.sectors} />
        </section>
        <div className="grid gap-6 lg:col-span-5 lg:grid-rows-2">
          <section className="card p-5 sm:p-6" aria-labelledby="gain-h">
            <h2 id="gain-h" className="mb-3 text-lg font-bold tracking-tight">Top gainers</h2>
            <MoversChart quotes={markets.gainers} title="Top gainers" />
          </section>
          <section className="card p-5 sm:p-6" aria-labelledby="lose-h">
            <h2 id="lose-h" className="mb-3 text-lg font-bold tracking-tight">Top losers</h2>
            <MoversChart quotes={markets.losers} title="Top losers" />
          </section>
        </div>
      </div>

      <section aria-labelledby="watch-h">
        <SectionHeader title="Watchlist" eyebrow="AI, big tech & biotech" />
        <h2 id="watch-h" className="sr-only">Watchlist</h2>
        <Watchlist quotes={markets.watchlist} />
      </section>

      {news && news.items.length > 0 && (
        <section aria-labelledby="mnews-h">
          <SectionHeader title="Markets news" eyebrow="Latest" accent={cat.color} />
          <h2 id="mnews-h" className="sr-only">Markets news</h2>
          <div className="card px-6 py-2">
            {news.items.map((item) => <StoryCard key={item.id} item={item} accent={cat.color} />)}
          </div>
        </section>
      )}
    </div>
  );
}
