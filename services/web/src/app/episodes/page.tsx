import type { Metadata } from "next";
import { categories } from "@newsroom/brand";
import { EpisodeCard } from "@/components/episodes/EpisodeCard";
import { PageHeader } from "@/components/ui/Section";
import { Unavailable } from "@/components/ui/Unavailable";
import { getEpisodes } from "@/lib/api";

export const metadata: Metadata = {
  title: "Episodes",
  description: "Every daily episode of the show, with chapters, sources and the daily quiz.",
  openGraph: { title: "Episodes" },
};

export default async function EpisodesPage() {
  const episodes = await getEpisodes();
  return (
    <>
      <PageHeader title="Episodes" eyebrow="Daily show" accent={categories.markets.color} description="Under four minutes a day: the markets, the biggest stories in AI, tech and biotech, and a daily quiz." />
      {!episodes ? (
        <Unavailable what="The episode archive" />
      ) : episodes.length === 0 ? (
        <p className="card p-10 text-center text-muted">No episodes yet.</p>
      ) : (
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {episodes.map((e) => <EpisodeCard key={e.date} episode={e} />)}
        </div>
      )}
    </>
  );
}
