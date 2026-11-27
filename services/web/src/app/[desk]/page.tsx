import type { Metadata } from "next";
import { categories, isTabSlug, type TabSlug } from "@newsroom/brand";
import { SourceDonut } from "@/components/charts/SourceDonut";
import { VolumeChart } from "@/components/charts/VolumeChart";
import { Watchlist } from "@/components/markets/Watchlist";
import { KeywordCloud } from "@/components/news/KeywordCloud";
import { KpiTile } from "@/components/news/KpiTile";
import { FeaturedStory, StoryCard } from "@/components/news/StoryCard";
import { PageHeader } from "@/components/ui/Section";
import { Unavailable } from "@/components/ui/Unavailable";
import { getMarkets, getNews } from "@/lib/api";
import { notFound } from "next/navigation";

const DESKS: TabSlug[] = ["ai", "ai-finance", "tech", "biotech"];
const SECTOR: Partial<Record<TabSlug, string>> = { biotech: "Biotech", "ai-finance": "AI & Chips" };

export const dynamicParams = false;
export const generateStaticParams = () => DESKS.map((desk) => ({ desk }));

type Params = Promise<{ desk: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { desk } = await params;
  if (!isTabSlug(desk)) return {};
  const cat = categories[desk];
  return { title: cat.label, description: cat.description, openGraph: { title: cat.label } };
}

export default async function DeskPage({ params }: { params: Params }) {
  const { desk } = await params;
  if (!isTabSlug(desk) || !DESKS.includes(desk)) notFound();
  const cat = categories[desk];
  const sectorName = SECTOR[desk];
  const [feed, markets] = await Promise.all([getNews(desk, 30), sectorName ? getMarkets() : null]);

  if (!feed) {
    return (
      <>
        <PageHeader title={cat.label} description={cat.description} accent={cat.color} eyebrow="Desk" />
        <Unavailable what={`The ${cat.label} desk`} />
      </>
    );
  }

  const week = feed.volume.reduce((a, v) => a + v.count, 0);
  const [featured, ...rest] = feed.items;
  const sector = markets?.sectors.find((s) => s.name === sectorName);
  const sectorQuotes = sector
    ? markets!.watchlist.filter((q) => sector.members.some((m) => m.symbol === q.symbol))
    : [];

  return (
    <div className="space-y-10">
      <PageHeader title={cat.label} description={cat.description} accent={cat.color} eyebrow="Desk" />

      <div className="-mt-4 grid gap-4 sm:grid-cols-3">
        <KpiTile label="Stories this week" value={String(week)} hint="Last 7 days" accent={cat.color} />
        <KpiTile label="Top source" value={feed.topSources[0]?.source ?? "—"} hint={feed.topSources[0] ? `${feed.topSources[0].count} stories` : undefined} accent={cat.color} />
        <KpiTile label="Trending term" value={feed.keywords[0]?.term ?? "—"} hint={feed.keywords[0] ? `${feed.keywords[0].count} mentions` : undefined} accent={cat.color} />
      </div>

      <div className="grid gap-8 lg:grid-cols-12">
        <div className="space-y-6 lg:col-span-8">
          {featured ? <FeaturedStory item={featured} accent={cat.color} /> : <p className="card p-8 text-muted">No stories on this desk yet.</p>}
          {rest.length > 0 && (
            <div className="card px-6 py-2">
              {rest.map((item) => <StoryCard key={item.id} item={item} accent={cat.color} />)}
            </div>
          )}
        </div>

        <aside className="space-y-6 lg:col-span-4" aria-label="Desk analytics">
          <section className="card p-5" aria-labelledby="vol-h">
            <h2 id="vol-h" className="eyebrow mb-3">Story volume · 7 days</h2>
            <VolumeChart data={feed.volume} color={cat.color} />
          </section>
          {feed.topSources.length > 0 && (
            <section className="card p-5" aria-labelledby="src-h">
              <h2 id="src-h" className="eyebrow mb-4">Top sources</h2>
              <SourceDonut data={feed.topSources} accent={cat.color} />
            </section>
          )}
          {feed.keywords.length > 0 && (
            <section className="card p-5" aria-labelledby="kw-h">
              <h2 id="kw-h" className="eyebrow mb-4">Trending keywords</h2>
              <KeywordCloud keywords={feed.keywords} accent={cat.color} />
            </section>
          )}
        </aside>
      </div>

      {sectorQuotes.length > 0 && (
        <section aria-labelledby="sector-h">
          <h2 id="sector-h" className="mb-4 text-xl font-bold tracking-tight">{sectorName} stocks</h2>
          <Watchlist quotes={sectorQuotes} title={`${sectorName} stocks`} />
        </section>
      )}
    </div>
  );
}
