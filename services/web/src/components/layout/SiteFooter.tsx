import { Logo } from "@newsroom/brand";
import Link from "next/link";
import { siteConfig } from "@/site.config";

export function SiteFooter() {
  return (
    <footer className="border-t border-line bg-surface/60">
      <div className="mx-auto grid max-w-[1280px] gap-10 px-4 py-12 sm:px-6 md:grid-cols-[1.4fr_1fr_1fr] lg:px-8">
        <div className="space-y-4">
          <Logo name={siteConfig.name} size={18} fontFamily="var(--font-inter)" textColor="var(--text)" />
          <p className="max-w-sm text-sm text-muted">{siteConfig.tagline}</p>
          <p className="max-w-md text-xs leading-relaxed text-muted">
            Not financial or medical advice. Hosts and content are produced with AI tools and automated fact checks.
          </p>
        </div>
        <nav aria-label="Sections">
          <div className="eyebrow mb-3">Sections</div>
          <ul className="space-y-2 text-sm">
            {siteConfig.nav.map((n) => (
              <li key={n.href}>
                <Link href={n.href} className="text-muted hover:text-ink">{n.label}</Link>
              </li>
            ))}
          </ul>
        </nav>
        <div>
          <div className="eyebrow mb-3">More</div>
          <ul className="space-y-2 text-sm">
            {[...siteConfig.footerLinks, ...siteConfig.social].map((l) => (
              <li key={l.label}>
                <a href={l.href} className="text-muted hover:text-ink">{l.label}</a>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="border-t border-line py-5 text-center text-xs text-muted">
        © {new Date().getFullYear()} {siteConfig.name}. All rights reserved.
      </div>
    </footer>
  );
}
