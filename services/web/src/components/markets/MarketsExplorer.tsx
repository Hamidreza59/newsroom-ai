"use client";

import { fmtChange, fmtPrice } from "@newsroom/brand";
import { useEffect, useMemo, useRef, useState } from "react";
import { PriceChartLoader } from "@/components/charts/PriceChartLoader";
import { Delta } from "@/components/ui/Delta";
import type { PricePoint, Quote } from "@/lib/contract";
import { fetchHistory, type Range } from "@/lib/history";

const RANGES: { id: Range; label: string }[] = [
  { id: "1mo", label: "1M" },
  { id: "6mo", label: "6M" },
  { id: "1y", label: "1Y" },
];

export function MarketsExplorer({ indices, watchlist }: { indices: Quote[]; watchlist: Quote[] }) {
  const all = useMemo(() => [...indices, ...watchlist], [indices, watchlist]);
  const [symbol, setSymbol] = useState(all[0]?.symbol ?? "");
  const [range, setRange] = useState<Range>("1mo");
  const cache = useRef(new Map<string, PricePoint[]>(all.map((q) => [`${q.symbol}:1mo`, q.series])));
  const [points, setPoints] = useState<PricePoint[]>(all[0]?.series ?? []);
  const [state, setState] = useState<"ready" | "loading" | "error">("ready");

  const quote = all.find((q) => q.symbol === symbol);

  useEffect(() => {
    const key = `${symbol}:${range}`;
    const hit = cache.current.get(key);
    if (hit) {
      setPoints(hit);
      setState("ready");
      return;
    }
    const ctrl = new AbortController();
    setState("loading");
    fetchHistory(symbol, range, ctrl.signal)
      .then((h) => {
        cache.current.set(key, h.points);
        setPoints(h.points);
        setState("ready");
      })
      .catch((e) => {
        if (e.name !== "AbortError") setState("error");
      });
    return () => ctrl.abort();
  }, [symbol, range]);

  if (!quote) return null;
  const first = points[0]?.close ?? 0;
  const last = points[points.length - 1]?.close ?? 0;
  const periodPct = first ? ((last - first) / first) * 100 : 0;

  return (
    <section aria-labelledby="chart-heading" className="card p-4 sm:p-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 id="chart-heading" className="text-sm font-semibold text-muted">
            {quote.name} <span className="num">({quote.symbol})</span>
          </h2>
          <div className="mt-1 flex flex-wrap items-baseline gap-x-4 gap-y-1">
            <span className="num text-3xl font-bold tracking-tight">{fmtPrice(quote.price)}</span>
            <Delta value={quote.changePct} className="text-base" />
            <span className={`num text-sm ${quote.change >= 0 ? "up" : "down"}`}>{fmtChange(quote.change)} today</span>
          </div>
          <p className="mt-1 text-xs text-muted">
            <span className={`num ${periodPct >= 0 ? "up" : "down"}`}>{periodPct >= 0 ? "+" : "−"}{Math.abs(periodPct).toFixed(2)}%</span>{" "}
            over the selected period
          </p>
        </div>
        <div role="radiogroup" aria-label="Time range" className="inline-flex rounded-lg border border-line bg-surface-2 p-0.5">
          {RANGES.map((r) => (
            <button
              key={r.id}
              type="button"
              role="radio"
              aria-checked={range === r.id}
              onClick={() => setRange(r.id)}
              className={`num rounded-md px-3.5 py-1.5 text-xs font-semibold transition-colors ${
                range === r.id ? "bg-surface text-ink shadow-sm" : "text-muted hover:text-ink"
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-1.5" role="radiogroup" aria-label="Symbol">
        {all.map((q, i) => (
          <button
            key={q.symbol}
            type="button"
            role="radio"
            aria-checked={symbol === q.symbol}
            onClick={() => setSymbol(q.symbol)}
            className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
              symbol === q.symbol ? "border-gold bg-gold/15 text-ink" : "border-line text-muted hover:border-line-strong hover:text-ink"
            } ${i === indices.length ? "ml-2" : ""}`}
          >
            {i < indices.length ? q.name : q.symbol}
          </button>
        ))}
      </div>

      <div className="relative">
        {points.length > 1 ? (
          <PriceChartLoader points={points} name={quote.name} height={420} />
        ) : (
          <div className="flex h-[420px] items-center justify-center text-sm text-muted">No price history available.</div>
        )}
        {state !== "ready" && (
          <div
            role="status"
            className="absolute inset-0 flex items-center justify-center rounded-lg bg-surface/70 text-sm text-muted backdrop-blur-[1px]"
          >
            {state === "loading" ? "Loading history…" : "Could not load price history. Try another range."}
          </div>
        )}
      </div>
    </section>
  );
}
