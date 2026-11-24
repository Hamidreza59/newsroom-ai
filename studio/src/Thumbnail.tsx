import React from "react";
import { AbsoluteFill } from "remotion";
import { Logo } from "./components/Chrome";
import { Presenter } from "./components/Presenter";
import { body, color, display, fmtDate, moveColor } from "./theme";
import type { Episode } from "./types";

export const Thumbnail: React.FC<Episode> = (episode) => {
  const { gainers, losers, indices } = episode.market;
  const movers = [...gainers, ...losers].sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct));
  const big = movers[0] && Math.abs(movers[0].changePct) >= 3 ? movers[0] : indices[0];
  const story = episode.scenes.find((s) => s.type === "news");
  const tone = moveColor(big?.changePct ?? 0);

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(700px 520px at 78% 55%, rgba(34,211,238,0.25), transparent 65%),
          radial-gradient(600px 500px at 10% 90%, ${tone}33, transparent 60%),
          linear-gradient(160deg, ${color.bg1}, ${color.bg0})`,
        padding: 52, boxSizing: "border-box", fontFamily: body, overflow: "hidden",
      }}
    >
      <Logo name={episode.showName} size={34} />
      {big && (
        <div style={{ marginTop: 36, fontFamily: display, fontWeight: 700, lineHeight: 0.95, position: "relative", zIndex: 2 }}>
          <div style={{ fontSize: 88, color: color.text }}>{big.name.toUpperCase()}</div>
          <div style={{ fontSize: 132, color: tone, textShadow: `0 0 40px ${tone}88` }}>
            {big.changePct >= 0 ? "+" : "−"}{Math.abs(big.changePct).toFixed(1)}%
          </div>
        </div>
      )}
      <div style={{ position: "absolute", right: 230, top: 210 }}>
        <Presenter id="a" mouth={0.5} look={0.4} speaking size={360} frameOverride={30} seed={episode.date} />
      </div>
      <div style={{ position: "absolute", right: -10, top: 196 }}>
        <Presenter id="b" mouth={0} look={-0.6} speaking={false} size={360} frameOverride={30} seed={episode.date} />
      </div>
      {story && (
        <div style={{ position: "absolute", left: 52, bottom: 52, maxWidth: 700, padding: "18px 26px", zIndex: 2,
                      borderRadius: 20, background: color.gold, color: color.bg0, fontSize: 36,
                      fontWeight: 800, lineHeight: 1.15, boxShadow: "0 16px 40px rgba(0,0,0,0.45)" }}>
          + {story.headline}
        </div>
      )}
      <div style={{ position: "absolute", right: 52, top: 56, color: color.muted, fontSize: 30, fontWeight: 600 }}>
        {fmtDate(episode.date, { month: "short", day: "numeric", year: "numeric" })}
      </div>
    </AbsoluteFill>
  );
};
