import { categories, isTabSlug, relativeTime } from "@newsroom/brand";
import { ExternalLink } from "lucide-react";
import type { SiteNewsItem } from "@/lib/contract";
import { Chip } from "@/components/ui/Chip";

const tagColor = (tag: string) => (isTabSlug(tag) ? categories[tag].color : undefined);

function Meta({ item }: { item: SiteNewsItem }) {
  return (
    <div className="flex items-center gap-2 text-xs text-muted">
      <span className="font-semibold text-ink/90">{item.source}</span>
      <span aria-hidden="true">·</span>
      <time dateTime={item.published}>{relativeTime(item.published)}</time>
    </div>
  );
}

export function StoryCard({ item, accent }: { item: SiteNewsItem; accent?: string }) {
  return (
    <article className="group relative flex flex-col gap-2 border-b border-line py-4 last:border-b-0" style={{ ["--cat" as string]: accent ?? "var(--muted)" }}>
      <Meta item={item} />
      <h3 className="text-base font-semibold leading-snug tracking-tight">
        <a
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
          className="after:absolute after:inset-0 group-hover:text-[color:var(--cat)]"
        >
          {item.title}
          <ExternalLink size={12} className="ml-1.5 inline opacity-0 transition-opacity group-hover:opacity-70" aria-label="(opens in a new tab)" />
        </a>
      </h3>
      <p className="line-clamp-2 text-sm text-muted">{item.summary}</p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {item.tags.map((t) => (
          <Chip key={t} color={tagColor(t)}>{isTabSlug(t) ? categories[t].label : t}</Chip>
        ))}
      </div>
    </article>
  );
}

export function FeaturedStory({ item, accent }: { item: SiteNewsItem; accent: string }) {
  return (
    <article
      className="card group relative overflow-hidden p-6 sm:p-8"
      style={{ ["--cat" as string]: accent, background: `linear-gradient(135deg, color-mix(in srgb, ${accent} 12%, var(--surface)), var(--surface) 60%)` }}
    >
      <div className="eyebrow cat-text mb-3">Top story</div>
      <h2 className="max-w-3xl text-2xl font-bold leading-tight tracking-tight sm:text-3xl">
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="after:absolute after:inset-0">
          {item.title}
        </a>
      </h2>
      <p className="mt-3 max-w-2xl text-base text-muted">{item.summary}</p>
      <div className="mt-5 flex flex-wrap items-center gap-3">
        <Meta item={item} />
        {item.tags.map((t) => (
          <Chip key={t} color={tagColor(t)}>{isTabSlug(t) ? categories[t].label : t}</Chip>
        ))}
      </div>
    </article>
  );
}

export function StoryCompact({ item, accent }: { item: SiteNewsItem; accent: string }) {
  return (
    <article className="group relative py-3" style={{ ["--cat" as string]: accent }}>
      <h3 className="text-sm font-semibold leading-snug group-hover:text-[color:var(--cat)]">
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="after:absolute after:inset-0">
          {item.title}
        </a>
      </h3>
      <div className="mt-1"><Meta item={item} /></div>
    </article>
  );
}
