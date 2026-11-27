import type { KeywordCount } from "@/lib/contract";

export function KeywordCloud({ keywords, accent }: { keywords: KeywordCount[]; accent: string }) {
  const max = Math.max(...keywords.map((k) => k.count), 1);
  return (
    <ul className="flex flex-wrap items-center gap-2" aria-label="Trending keywords" style={{ ["--cat" as string]: accent }}>
      {keywords.map((k) => {
        const weight = k.count / max;
        return (
          <li
            key={k.term}
            className="rounded-full border px-3 py-1 font-medium"
            style={{
              fontSize: `${0.78 + weight * 0.5}rem`,
              borderColor: `color-mix(in srgb, ${accent} ${25 + weight * 40}%, transparent)`,
              background: `color-mix(in srgb, ${accent} ${6 + weight * 16}%, transparent)`,
            }}
          >
            {k.term} <span className="num text-xs text-muted">{k.count}</span>
          </li>
        );
      })}
    </ul>
  );
}
