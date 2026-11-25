import React from "react";
import { useCurrentFrame } from "remotion";
import { arrow, body, color, fmtPct, fmtPrice, layout, moveColor } from "../theme";
import type { Quote } from "../types";

const GAP = 64;
const itemWidth = (q: Quote) =>
  Math.round((q.name.length + fmtPrice(q.price).length + fmtPct(q.changePct).length + 2) * 13.6) + 24 + GAP;

export const Ticker: React.FC<{ quotes: Quote[]; asOf: string; sample: boolean }> = ({
  quotes,
  asOf,
  sample,
}) => {
  const frame = useCurrentFrame();
  const widths = quotes.map(itemWidth);
  const loop = widths.reduce((a, b) => a + b, 0);
  const x = -((frame * 2.2) % loop);
  const items = [...quotes, ...quotes, ...quotes];
  return (
    <div
      style={{
        position: "absolute", left: 0, bottom: 0, width: layout.width, height: layout.tickerH,
        background: "rgba(4,7,20,0.92)", borderTop: `2px solid ${color.gold}`, overflow: "hidden",
        fontFamily: body,
      }}
    >
      <div style={{ position: "absolute", left: x + 260, top: 0, height: "100%", display: "flex" }}>
        {items.map((q, i) => (
          <div key={i} style={{ width: widths[i % quotes.length], display: "flex", alignItems: "center", gap: 12,
                                fontSize: 24, color: color.text, whiteSpace: "nowrap" }}>
            <span style={{ fontWeight: 700 }}>{q.name}</span>
            <span style={{ color: color.muted }}>{fmtPrice(q.price)}</span>
            <span style={{ color: moveColor(q.changePct), fontWeight: 700 }}>
              {arrow(q.changePct)} {fmtPct(q.changePct)}
            </span>
          </div>
        ))}
      </div>
      <div
        style={{
          position: "absolute", left: 0, top: 0, width: 250, height: "100%", display: "flex",
          alignItems: "center", justifyContent: "center", flexDirection: "column",
          background: color.gold, color: color.bg0, fontWeight: 800, letterSpacing: 2,
        }}
      >
        <div style={{ fontSize: 22 }}>{sample ? "SAMPLE DATA" : "MARKETS"}</div>
        <div style={{ fontSize: 15, fontWeight: 600 }}>CLOSE {asOf}</div>
      </div>
    </div>
  );
};
