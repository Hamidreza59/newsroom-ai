"use client";

import { fmtPrice } from "@newsroom/brand";
import { ArrowDown, ArrowUp } from "lucide-react";
import { useMemo, useState } from "react";
import type { Quote } from "@/lib/contract";
import { Delta } from "@/components/ui/Delta";
import { Sparkline } from "@/components/ui/Sparkline";

type Key = "symbol" | "price" | "changePct";

export function Watchlist({ quotes, title = "Watchlist" }: { quotes: Quote[]; title?: string }) {
  const [key, setKey] = useState<Key>("symbol");
  const [dir, setDir] = useState<1 | -1>(1);

  const rows = useMemo(() => {
    const sorted = [...quotes].sort((a, b) =>
      key === "symbol" ? a.symbol.localeCompare(b.symbol) : a[key] - b[key],
    );
    return dir === 1 ? sorted : sorted.reverse();
  }, [quotes, key, dir]);

  const sort = (k: Key) => {
    if (k === key) setDir((d) => (d === 1 ? -1 : 1));
    else {
      setKey(k);
      setDir(k === "symbol" ? 1 : -1);
    }
  };

  const Th = ({ k, label, align = "right" }: { k: Key; label: string; align?: "left" | "right" }) => (
    <th scope="col" aria-sort={key === k ? (dir === 1 ? "ascending" : "descending") : "none"} className={`px-4 py-3 ${align === "left" ? "text-left" : "text-right"}`}>
      <button type="button" onClick={() => sort(k)} className="inline-flex items-center gap-1 font-semibold uppercase tracking-wider hover:text-ink">
        {label}
        {key === k && (dir === 1 ? <ArrowUp size={12} aria-hidden="true" /> : <ArrowDown size={12} aria-hidden="true" />)}
      </button>
    </th>
  );

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full min-w-[560px] text-sm">
          <caption className="sr-only">{title}, sortable by symbol, price and daily change</caption>
          <thead className="border-b border-line text-[0.68rem] text-muted">
            <tr>
              <Th k="symbol" label="Symbol" align="left" />
              <th scope="col" className="px-4 py-3 text-left font-semibold uppercase tracking-wider">Name</th>
              <Th k="price" label="Price" />
              <Th k="changePct" label="Change" />
              <th scope="col" className="px-4 py-3 text-right font-semibold uppercase tracking-wider">1M</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {rows.map((q) => (
              <tr key={q.symbol} className="hover:bg-surface-2">
                <th scope="row" className="num px-4 py-2.5 text-left font-semibold">{q.symbol}</th>
                <td className="px-4 py-2.5 text-muted">{q.name}</td>
                <td className="num px-4 py-2.5 text-right">{fmtPrice(q.price)}</td>
                <td className="px-4 py-2.5 text-right"><Delta value={q.changePct} /></td>
                <td className="px-4 py-2.5">
                  <Sparkline series={q.series} width={96} height={28} className="ml-auto" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
