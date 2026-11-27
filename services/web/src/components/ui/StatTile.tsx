import { fmtChange, fmtPrice } from "@newsroom/brand";
import type { Quote } from "@/lib/contract";
import { Delta } from "./Delta";
import { Sparkline } from "./Sparkline";

export function StatTile({ quote, compact = false }: { quote: Quote; compact?: boolean }) {
  return (
    <div className="card flex flex-col gap-2 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-semibold">{quote.name}</span>
        <span className="num text-xs text-muted">{quote.symbol}</span>
      </div>
      <div className="flex items-end justify-between gap-3">
        <div>
          <div className={`num font-semibold tracking-tight ${compact ? "text-xl" : "text-2xl"}`}>
            {fmtPrice(quote.price)}
          </div>
          <div className="mt-0.5 flex items-center gap-2 text-sm">
            <Delta value={quote.changePct} />
            <span className={`num text-xs ${quote.change >= 0 ? "up" : "down"}`}>{fmtChange(quote.change)}</span>
          </div>
        </div>
        <Sparkline series={quote.series} width={96} height={40} className="shrink-0" />
      </div>
    </div>
  );
}
