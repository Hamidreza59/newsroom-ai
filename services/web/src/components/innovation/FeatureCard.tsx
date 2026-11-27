import { categories, fmtDate } from "@newsroom/brand";
import { Clock } from "lucide-react";
import Link from "next/link";
import { Chip } from "@/components/ui/Chip";
import type { FeatureSummary } from "@/lib/contract";

export function FeatureCard({ feature }: { feature: FeatureSummary }) {
  return (
    <Link
      href={`/innovation/${feature.slug}`}
      className="card group flex flex-col gap-3 p-6 transition-colors hover:border-line-strong"
      style={{ background: `linear-gradient(160deg, color-mix(in srgb, ${categories.ai.color} 9%, var(--surface)), var(--surface) 55%)` }}
    >
      <div className="flex items-center justify-between">
        <span className="num text-xs font-semibold tracking-wider text-muted">{feature.week}</span>
        <Chip color={categories.ai.color}>AI Innovation</Chip>
      </div>
      <h3 className="text-xl font-bold leading-snug tracking-tight">{feature.title}</h3>
      <p className="line-clamp-3 text-sm text-muted">{feature.dek}</p>
      <div className="mt-auto flex items-center gap-3 pt-3 text-xs text-muted">
        <span className="inline-flex items-center gap-1"><Clock size={12} aria-hidden="true" />{feature.readingMinutes} min read</span>
        <span aria-hidden="true">·</span>
        <time dateTime={feature.publishedAt}>{fmtDate(feature.publishedAt, { month: "short", day: "numeric", year: "numeric" })}</time>
      </div>
    </Link>
  );
}
