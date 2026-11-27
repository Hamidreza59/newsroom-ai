import type { Metadata } from "next";
import { categories, fmtDate } from "@newsroom/brand";
import { Bot, ExternalLink, Lightbulb } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Chip } from "@/components/ui/Chip";
import { Unavailable } from "@/components/ui/Unavailable";
import { getFeature } from "@/lib/api";

type Params = Promise<{ slug: string }>;

export async function generateMetadata({ params }: { params: Params }): Promise<Metadata> {
  const { slug } = await params;
  const f = await getFeature(slug);
  return f ? { title: f.title, description: f.dek, openGraph: { title: f.title, description: f.dek, type: "article" } } : { title: "AI Innovation" };
}

const anchor = (h: string, i: number) => `s${i + 1}-${h.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "")}`;

export default async function FeaturePage({ params }: { params: Params }) {
  const { slug } = await params;
  if (!/^[a-z0-9-]+$/.test(slug)) notFound();
  const f = await getFeature(slug);
  if (!f) return <Unavailable what="This article" />;

  const toc = [
    ...f.sections.map((s, i) => ({ id: anchor(s.heading, i), label: s.heading })),
    ...(f.glossary.length ? [{ id: "glossary", label: "Glossary" }] : []),
    ...(f.related.length ? [{ id: "related", label: "Related stories" }] : []),
    ...(f.sources.length ? [{ id: "sources", label: "Sources" }] : []),
  ];

  return (
    <article>
      <header
        className="card mb-10 overflow-hidden p-8 sm:p-12"
        style={{ background: "radial-gradient(700px 300px at 90% 0%, rgb(34 211 238 / 0.2), transparent 60%), radial-gradient(600px 300px at 0% 100%, rgb(167 139 250 / 0.16), transparent 60%), var(--surface)" }}
      >
        <div className="flex flex-wrap items-center gap-3">
          <Link href="/innovation" className="eyebrow hover:text-ink">AI Innovation</Link>
          <span className="num text-xs text-muted">{f.week}</span>
          <Chip color={categories.ai.color}>{f.topic}</Chip>
        </div>
        <h1 className="mt-4 max-w-3xl text-3xl font-bold leading-tight tracking-tight sm:text-5xl">{f.title}</h1>
        <p className="mt-4 max-w-2xl text-lg text-muted">{f.dek}</p>
        <div className="mt-6 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted">
          <time dateTime={f.publishedAt}>{fmtDate(f.publishedAt, { month: "long", day: "numeric", year: "numeric" })}</time>
          <span aria-hidden="true">·</span>
          <span>{f.readingMinutes} min read</span>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-line px-3 py-1 text-xs">
            <Bot size={13} aria-hidden="true" />
            Written by the Feature Writer agent · <span className="num">{f.generatedBy.model}</span>
          </span>
        </div>
      </header>

      <div className="grid gap-10 lg:grid-cols-[220px_1fr]">
        <aside className="hidden lg:block">
          <nav aria-label="Table of contents" className="sticky top-24">
            <h2 className="eyebrow mb-3">On this page</h2>
            <ul className="space-y-1 border-l border-line">
              {toc.map((t) => (
                <li key={t.id}>
                  <a href={`#${t.id}`} className="-ml-px block border-l border-transparent py-1.5 pl-4 text-sm text-muted hover:border-ink hover:text-ink">
                    {t.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </aside>

        <div className="max-w-3xl">
          {f.takeaways.length > 0 && (
            <aside className="mb-10 rounded-2xl border p-6" style={{ borderColor: "color-mix(in srgb, var(--ai) 40%, transparent)", background: "color-mix(in srgb, var(--ai) 8%, var(--surface))" }} aria-labelledby="takeaways-h">
              <h2 id="takeaways-h" className="mb-3 flex items-center gap-2 text-sm font-bold uppercase tracking-wider">
                <Lightbulb size={16} aria-hidden="true" /> Key takeaways
              </h2>
              <ul className="list-disc space-y-2 pl-5 text-[0.95rem] leading-relaxed">
                {f.takeaways.map((t) => <li key={t}>{t}</li>)}
              </ul>
            </aside>
          )}

          {f.sections.map((s, i) => (
            <section key={s.heading} id={anchor(s.heading, i)} className="mb-8">
              <h2 className="mb-3 text-2xl font-bold tracking-tight">{s.heading}</h2>
              {s.body.split(/\n{2,}/).map((p, j) => (
                <p key={j} className="mb-4 text-[1.02rem] leading-8">{p}</p>
              ))}
            </section>
          ))}

          {f.glossary.length > 0 && (
            <section id="glossary" className="mb-10">
              <h2 className="mb-4 text-2xl font-bold tracking-tight">Glossary</h2>
              <dl className="card divide-y divide-line">
                {f.glossary.map((g) => (
                  <div key={g.term} className="grid gap-1 px-5 py-4 sm:grid-cols-[180px_1fr] sm:gap-6">
                    <dt className="font-semibold">{g.term}</dt>
                    <dd className="text-sm leading-relaxed text-muted">{g.definition}</dd>
                  </div>
                ))}
              </dl>
            </section>
          )}

          {f.related.length > 0 && (
            <section id="related" className="mb-10">
              <h2 className="mb-4 text-2xl font-bold tracking-tight">Related stories</h2>
              <ul className="card divide-y divide-line">
                {f.related.map((r) => (
                  <li key={r.url}>
                    <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex items-start justify-between gap-4 px-5 py-4 hover:bg-surface-2">
                      <span className="font-medium">{r.title}</span>
                      <span className="flex shrink-0 items-center gap-1 text-xs text-muted">{r.source}<ExternalLink size={12} aria-label="(opens in a new tab)" /></span>
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}

          {f.sources.length > 0 && (
            <section id="sources" className="mb-10">
              <h2 className="mb-3 text-2xl font-bold tracking-tight">Sources</h2>
              <ol className="list-decimal space-y-1.5 pl-5 text-sm">
                {f.sources.map((s) => (
                  <li key={s.url}>
                    <a href={s.url} target="_blank" rel="noopener noreferrer" className="text-muted underline underline-offset-4 hover:text-ink">{s.title}</a>
                  </li>
                ))}
              </ol>
            </section>
          )}

          <p className="rounded-xl border border-line bg-surface p-4 text-xs leading-relaxed text-muted">{f.disclaimer}</p>
        </div>
      </div>
    </article>
  );
}
