import type { Metadata } from "next";
import { fmtDate, fmtDuration } from "@newsroom/brand";
import { Clock, ExternalLink } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { shortTitle } from "@/components/episodes/EpisodeCard";
import { EpisodePlayer } from "@/components/episodes/EpisodePlayer";
import { Markdown } from "@/components/episodes/Markdown";
import { Quiz } from "@/components/episodes/Quiz";
import { Chip } from "@/components/ui/Chip";
import { Unavailable } from "@/components/ui/Unavailable";
import { getEpisode } from "@/lib/api";
import { mediaUrl } from "@/lib/env";

type Params = Promise<{ date: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { date } = await params;
  const ep = await getEpisode(date);
  return ep
    ? { title: shortTitle(ep.title), description: ep.summary.slice(0, 200), openGraph: { title: shortTitle(ep.title), type: "video.other" } }
    : { title: "Episode" };
}

export default async function EpisodePage({ params }: { params: Params }) {
  const { date } = await params;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) notFound();
  const ep = await getEpisode(date);
  if (!ep) return <Unavailable what="This episode" />;

  return (
    <article className="space-y-10">
      <header>
        <Link href="/episodes" className="eyebrow hover:text-ink">← Episodes</Link>
        <h1 className="mt-3 max-w-4xl text-3xl font-bold leading-tight tracking-tight sm:text-4xl">{shortTitle(ep.title)}</h1>
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-muted">
          <time dateTime={ep.date}>{fmtDate(ep.date, { weekday: "long", month: "long", day: "numeric", year: "numeric" })}</time>
          {ep.durationSeconds != null && (
            <span className="inline-flex items-center gap-1"><Clock size={13} aria-hidden="true" /><span className="num">{fmtDuration(ep.durationSeconds)}</span></span>
          )}
          <span>{ep.storyCount} stories</span>
          {ep.tags.map((t) => <Chip key={t}>{t}</Chip>)}
        </div>
      </header>

      <EpisodePlayer videoSrc={mediaUrl(ep.videoUrl)} thumbnailUrl={ep.thumbnailUrl} date={ep.date} chapters={ep.chapters} />

      <div className="grid gap-10 lg:grid-cols-12">
        <div className="space-y-10 lg:col-span-7">
          <section aria-labelledby="sum-h">
            <h2 id="sum-h" className="eyebrow mb-3">Summary</h2>
            <p className="leading-relaxed">{ep.summary}</p>
          </section>
          {ep.quiz && <Quiz quiz={ep.quiz} />}
          {ep.scriptMarkdown && (
            <section aria-labelledby="script-h">
              <h2 id="script-h" className="mb-4 text-xl font-bold tracking-tight">Script</h2>
              <div className="card p-6 sm:p-8"><Markdown source={ep.scriptMarkdown} /></div>
            </section>
          )}
        </div>
        <aside className="space-y-6 lg:col-span-5" aria-label="Sources">
          <section className="card p-5">
            <h2 className="eyebrow mb-3">Sources</h2>
            <ul className="divide-y divide-line">
              {ep.sources.map((s) => (
                <li key={s.url}>
                  <a href={s.url} target="_blank" rel="noopener noreferrer" className="group flex items-start justify-between gap-3 py-3 text-sm">
                    <span><span className="font-medium group-hover:underline">{s.title}</span><span className="block text-xs text-muted">{s.publisher}</span></span>
                    <ExternalLink size={13} className="mt-1 shrink-0 text-muted" aria-label="(opens in a new tab)" />
                  </a>
                </li>
              ))}
            </ul>
          </section>
          <p className="text-xs leading-relaxed text-muted">{ep.disclaimer}</p>
        </aside>
      </div>
    </article>
  );
}
