import { fmtPrice } from "@newsroom/brand";
import type { Quote } from "@/lib/contract";
import { Delta } from "@/components/ui/Delta";

function Items({ quotes, hidden }: { quotes: Quote[]; hidden?: boolean }) {
  return (
    <ul className="flex shrink-0 items-center" aria-hidden={hidden || undefined}>
      {quotes.map((q) => (
        <li key={q.symbol} className="flex items-center gap-2 border-r border-line px-5 text-xs">
          <span className="font-semibold">{q.symbol.replace("^", "")}</span>
          <span className="num text-muted">{fmtPrice(q.price)}</span>
          <Delta value={q.changePct} />
        </li>
      ))}
    </ul>
  );
}

export function Ticker({ quotes }: { quotes: Quote[] }) {
  return (
    <section aria-label="Market ticker" className="ticker overflow-hidden border-b border-line bg-surface/70">
      <div className="ticker-track py-2">
        <Items quotes={quotes} />
        <Items quotes={quotes} hidden />
      </div>
    </section>
  );
}
