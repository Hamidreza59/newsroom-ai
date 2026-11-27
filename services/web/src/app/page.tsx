import { categories, fmtDate, fmtDuration } from "@newsroom/brand";
import { Clock } from "lucide-react";
import Link from "next/link";
import { EpisodeCard, shortTitle } from "@/components/episodes/EpisodeCard";
import { EpisodeVisual } from "@/components/episodes/EpisodeVisual";
import { MarketOverviewPanel } from "@/components/markets/MarketOverviewPanel";
import { TopStoriesGrid } from "@/components/news/TopStoriesGrid";
import { SectionHeader } from "@/components/ui/Section";
import { Unavailable } from "@/components/ui/Unavailable";
import { getEpisode, getEpisodes, getHome } from "@/lib/api";
import type { EpisodeDetail, EpisodeSummary } from "@/lib/contract";
import { mediaUrl } from "@/lib/env";
import { siteConfig } from "@/site.config";

export const metadata = { title: { absolute: `${siteConfig.name} · ${siteConfig.tagline}` } };

function Hero({ episode, detail }: { episode: EpisodeSummary; detail: EpisodeDetail | null }) {
  const video = mediaUrl(episode.videoUrl);
  return (
    <section aria-labelledby="hero-heading" className="card overflow-hidden">
      {video ? (
        <video controls preload="metadata" className="aspect-video w-full bg-black">
          <source src={video} type="video/mp4" />
        </video>
      ) : (
        <Link href={`/episodes/${episode.date}`} aria-label="Open latest episode">
          <EpisodeVisual thumbnailUrl={episode.thumbnailUrl} date={episode.date} />
        </Link>
      )}
      <div className="grid gap-6 p-5 sm:p-6 md:grid-cols-[1.4fr_1fr]">
        <div>
          <div className="eyebrow cat-text mb-2" style={{ ["--cat" as string]: categories.markets.color }}>Latest episode</div>
          <h1 id="hero-heading" className="text-2xl font-bold leading-tight tracking-tight sm:text-[1.75rem]">
            <Link href={`/episodes/${episode.date}`} className="hover:underline">{shortTitle(episode.title)}</Link>
          </h1>
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-muted">
            <time dateTime={episode.date}>{fmtDate(episode.date, { weekday: "long", month: "long", day: "numeric" })}</time>
            {episode.durationSeconds != null && (
              <span className="inline-flex items-center gap-1"><Clock size={13} aria-hidden="true" /><span className="num">{fmtDuration(episode.durationSeconds)}</span></span>
            )}
            <span>{episode.storyCount} stories</span>
          </div>
        </div>
        {detail && detail.chapters.length > 0 && (
          <div>
            <h2 className="eyebrow mb-2">Chapters</h2>
            <ol className="space-y-1.5 text-sm">
              {detail.chapters.slice(0, 5).map((c) => (
                <li key={c.time + c.title} className="flex gap-3">
                  <span className="num w-9 shrink-0 text-xs text-gold">{c.time}</span>
                  <span className="line-clamp-1">{c.title}</span>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </section>
  );
}

export default async function HomePage() {
  const [home, episodes] = await Promise.all([getHome(), getEpisodes()]);
  if (!home) return <Unavailable what="The front page" />;
  const detail = home.latestEpisode ? await getEpisode(home.latestEpisode.date) : null;
  const recent = (episodes ?? []).filter((e) => e.date !== home.latestEpisode?.date).slice(0, 4);

  return (
    <div className="space-y-14">
      <div className="grid gap-6 lg:grid-cols-12">
        <div className="lg:col-span-8">
          {home.latestEpisode ? (
            <Hero episode={home.latestEpisode} detail={detail} />
          ) : (
            <div className="card p-10 text-center text-muted">The first episode is on its way.</div>
          )}
        </div>
        <div className="lg:col-span-4">
          <MarketOverviewPanel markets={home.markets} />
        </div>
      </div>

      <section aria-labelledby="top-stories">
        <SectionHeader title="Top stories" eyebrow="By desk" href="/markets" hrefLabel="Markets" />
        <h2 id="top-stories" className="sr-only">Top stories by desk</h2>
        <TopStoriesGrid desks={home.topStories} />
      </section>

      {home.feature && (
        <section
          aria-labelledby="innovation-banner"
          className="card relative overflow-hidden p-8 sm:p-12"
          style={{ background: "radial-gradient(700px 300px at 85% 0%, rgb(34 211 238 / 0.2), transparent 60%), radial-gradient(600px 300px at 0% 100%, rgb(167 139 250 / 0.18), transparent 60%), var(--surface)" }}
        >
          <div className="eyebrow cat-text mb-3" style={{ ["--cat" as string]: categories.ai.color }}>This week in AI innovation · {home.feature.week}</div>
          <h2 id="innovation-banner" className="max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{home.feature.title}</h2>
          <p className="mt-3 max-w-2xl text-base text-muted">{home.feature.dek}</p>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <Link href={`/innovation/${home.feature.slug}`} className="rounded-lg bg-ink px-5 py-2.5 text-sm font-semibold text-bg hover:opacity-90">
              Read the feature
            </Link>
            <Link href="/innovation" className="text-sm font-medium text-muted hover:text-ink">All features →</Link>
          </div>
        </section>
      )}

      {recent.length > 0 && (
        <section aria-labelledby="recent-eps">
          <SectionHeader title="Recent episodes" eyebrow="Watch" href="/episodes" />
          <h2 id="recent-eps" className="sr-only">Recent episodes</h2>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {recent.map((e) => <EpisodeCard key={e.date} episode={e} />)}
          </div>
        </section>
      )}
    </div>
  );
}
