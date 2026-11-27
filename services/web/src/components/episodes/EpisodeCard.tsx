import { fmtDate, fmtDuration } from "@newsroom/brand";
import { Clock, Play } from "lucide-react";
import Link from "next/link";
import type { EpisodeSummary } from "@/lib/contract";
import { EpisodeVisual } from "./EpisodeVisual";

export const shortTitle = (t: string) => t.split("|")[0].trim();

export function EpisodeCard({ episode }: { episode: EpisodeSummary }) {
  return (
    <Link href={`/episodes/${episode.date}`} className="card group flex flex-col overflow-hidden transition-colors hover:border-line-strong">
      <div className="relative">
        <EpisodeVisual thumbnailUrl={episode.thumbnailUrl} date={episode.date} />
        <span className="absolute bottom-3 left-3 flex h-9 w-9 items-center justify-center rounded-full bg-gold text-[#060a1a] opacity-90 transition-transform group-hover:scale-110" aria-hidden="true">
          <Play size={14} fill="currentColor" />
        </span>
      </div>
      <div className="flex flex-1 flex-col gap-2 p-4">
        <time dateTime={episode.date} className="eyebrow">{fmtDate(episode.date, { weekday: "short", month: "short", day: "numeric", year: "numeric" })}</time>
        <h3 className="line-clamp-3 text-base font-semibold leading-snug">{shortTitle(episode.title)}</h3>
        <div className="mt-auto flex items-center gap-3 pt-2 text-xs text-muted">
          {episode.durationSeconds != null && (
            <span className="inline-flex items-center gap-1"><Clock size={12} aria-hidden="true" /><span className="num">{fmtDuration(episode.durationSeconds)}</span></span>
          )}
          <span>{episode.storyCount} stories</span>
        </div>
      </div>
    </Link>
  );
}
