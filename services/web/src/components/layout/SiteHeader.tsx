"use client";

import { Logo } from "@newsroom/brand";
import { Menu, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { siteConfig } from "@/site.config";
import { ThemeToggle } from "./ThemeToggle";

const isActive = (path: string, href: string) => (href === "/" ? path === "/" : path.startsWith(href));
const EXIT_MS = 200;

export function SiteHeader() {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  const [shown, setShown] = useState(false);
  const [mounted, setMounted] = useState(false);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => setMounted(true), []);

  const close = useCallback((restoreFocus = true) => {
    setOpen(false);
    if (restoreFocus) buttonRef.current?.focus();
  }, []);

  useEffect(() => setOpen(false), [path]);

  useEffect(() => {
    if (open) {
      setShown(true);
      return;
    }
    const t = setTimeout(() => setShown(false), EXIT_MS);
    return () => clearTimeout(t);
  }, [open]);

  useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";
    drawerRef.current?.querySelector<HTMLElement>("a")?.focus();
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onResize = () => {
      if (window.matchMedia("(min-width: 1280px)").matches) close(false);
    };
    document.addEventListener("keydown", onKey);
    window.addEventListener("resize", onResize);
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKey);
      window.removeEventListener("resize", onResize);
    };
  }, [open, close]);

  const drawer = (
    <div
      ref={drawerRef}
      id="mobile-nav"
      role="dialog"
      aria-modal="true"
      aria-label="Site navigation"
      data-state={open ? "open" : "closed"}
      className="mobile-drawer fixed inset-x-0 bottom-0 top-16 z-[60] overflow-y-auto overscroll-contain bg-bg px-4 py-4 xl:hidden"
      onKeyDown={(e) => {
        if (e.key !== "Tab") return;
        const els = drawerRef.current?.querySelectorAll<HTMLElement>("a[href]");
        if (!els?.length) return;
        const first = els[0];
        const last = els[els.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }}
    >
      <ul className="divide-y divide-line">
        {siteConfig.nav.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              aria-current={isActive(path, item.href) ? "page" : undefined}
              className={`block py-4 text-lg font-semibold ${isActive(path, item.href) ? "text-gold" : ""}`}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );

  return (
    <header className="sticky top-0 z-[70] border-b border-line bg-bg/85 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1280px] items-center gap-6 px-4 sm:px-6 lg:px-8">
        <Link href="/" aria-label={`${siteConfig.name} home`} className="shrink-0">
          <Logo name={siteConfig.name} size={20} fontFamily="var(--font-inter)" textColor="var(--text)" />
        </Link>
        <nav aria-label="Primary" className="hidden flex-1 items-center gap-0.5 xl:flex">
          {siteConfig.nav.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              aria-current={isActive(path, item.href) ? "page" : undefined}
              className={`relative rounded-md px-3 py-2 text-sm font-medium transition-colors hover:text-ink ${
                isActive(path, item.href) ? "text-ink" : "text-muted"
              }`}
            >
              {item.label}
              {isActive(path, item.href) && (
                <span className="absolute inset-x-3 -bottom-[13px] h-0.5 rounded-full bg-gold" aria-hidden="true" />
              )}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-2 xl:ml-0">
          <ThemeToggle />
          <button
            ref={buttonRef}
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line text-muted hover:bg-surface-2 xl:hidden"
            aria-label={open ? "Close menu" : "Open menu"}
            aria-expanded={open}
            aria-controls="mobile-nav"
            onClick={() => setOpen((v) => !v)}
          >
            {open ? <X size={18} aria-hidden="true" /> : <Menu size={18} aria-hidden="true" />}
          </button>
        </div>
      </div>
      {mounted && (open || shown) && createPortal(drawer, document.body)}
    </header>
  );
}
