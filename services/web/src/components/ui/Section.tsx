import Link from "next/link";
import { ArrowRight } from "lucide-react";

interface Props {
  title: string;
  eyebrow?: string;
  accent?: string;
  href?: string;
  hrefLabel?: string;
  children?: React.ReactNode;
}

export function SectionHeader({ title, eyebrow, accent, href, hrefLabel = "View all", children }: Props) {
  return (
    <div className="mb-4 flex items-end justify-between gap-4">
      <div style={accent ? ({ "--cat": accent } as React.CSSProperties) : undefined}>
        {eyebrow && <div className="eyebrow cat-text mb-1">{eyebrow}</div>}
        <h2 className="text-xl font-bold tracking-tight sm:text-2xl">{title}</h2>
      </div>
      {children}
      {href && (
        <Link href={href} className="group flex shrink-0 items-center gap-1 text-sm font-medium text-muted hover:text-ink">
          {hrefLabel}
          <ArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
        </Link>
      )}
    </div>
  );
}

export function PageHeader({
  title,
  description,
  accent,
  eyebrow,
  children,
}: {
  title: string;
  description?: string;
  accent?: string;
  eyebrow?: string;
  children?: React.ReactNode;
}) {
  return (
    <header className="mb-8 border-b border-line pb-6" style={accent ? ({ "--cat": accent } as React.CSSProperties) : undefined}>
      {eyebrow && <div className="eyebrow cat-text mb-2">{eyebrow}</div>}
      <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{title}</h1>
      {description && <p className="mt-2 max-w-2xl text-base text-muted">{description}</p>}
      {children}
    </header>
  );
}
