import { categories } from "@newsroom/brand";
import Link from "next/link";
import type { TopStories } from "@/lib/contract";
import { StoryCard } from "./StoryCard";

export function TopStoriesGrid({ desks }: { desks: TopStories[] }) {
  return (
    <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-6">
      {desks.map((d, i) => {
        const span = [
          desks.length % 2 === 1 && i === desks.length - 1 ? "md:col-span-2" : "",
          i < 3 ? "xl:col-span-2" : "xl:col-span-3",
        ].join(" ");
        const cat = categories[d.tab];
        return (
          <section key={d.tab} className={`card relative overflow-hidden px-5 pb-2 pt-5 ${span}`} style={{ ["--cat" as string]: cat.color }} aria-labelledby={`desk-${d.tab}`}>
            <span className="absolute inset-x-0 top-0 h-0.5" style={{ background: cat.color }} aria-hidden="true" />
            <div className="flex items-center justify-between">
              <h3 id={`desk-${d.tab}`} className="eyebrow cat-text">{d.label}</h3>
              <Link href={d.tab === "markets" ? "/markets" : `/${d.tab}`} className="text-xs font-medium text-muted hover:text-ink">
                More →
              </Link>
            </div>
            <div>
              {d.items.slice(0, 3).map((item) => (
                <StoryCard key={item.id} item={{ ...item, tags: [] }} accent={cat.color} />
              ))}
              {d.items.length === 0 && <p className="py-6 text-sm text-muted">No stories yet.</p>}
            </div>
          </section>
        );
      })}
    </div>
  );
}
