import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CountUp, LineChart, MoverBars, Sparkline } from "../components/Charts";
import { Panel, Pill } from "../components/Chrome";
import { arrow, body, color, display, fmtPct, layout, moveColor } from "../theme";
import type { Episode, Scene } from "../types";
import { reveal, SceneFrame, useSceneDuration } from "./SceneFrame";

export const MarketScene: React.FC<{ episode: Episode; scene: Scene }> = ({ episode, scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = useSceneDuration();
  const { indices, gainers, losers } = episode.market;
  const split = Math.round(durationInFrames * 0.52);
  const phaseA = interpolate(frame, [split - 10, split + 4], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const phaseB = interpolate(frame, [split, split + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const cardW = (layout.contentW - 2 * 24) / 3;
  const lead = indices[0];

  return (
    <SceneFrame>
      <div style={{ display: "flex", alignItems: "center", gap: 22, marginBottom: 24 }}>
        <Pill text="Markets" fg={color.gold} size={24} />
        <div style={{ fontFamily: display, fontSize: 52, fontWeight: 600, color: color.text, lineHeight: 1.1,
                      whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
          {scene.headline}
        </div>
      </div>

      <div style={{ position: "absolute", top: 100, left: 0, width: "100%", opacity: phaseA }}>
        <div style={{ display: "flex", gap: 24 }}>
          {indices.map((q, i) => {
            const s = spring({ frame: frame - 6 - i * 6, fps, config: { damping: 14 } });
            const tone = moveColor(q.changePct);
            return (
              <Panel key={q.symbol} style={{ width: cardW, height: 178, padding: "22px 28px", boxSizing: "border-box",
                                             opacity: s, transform: `translateY(${(1 - s) * 30}px)`, position: "relative" }}>
                <div style={{ fontFamily: body, color: color.muted, fontSize: 26, fontWeight: 600 }}>{q.name}</div>
                <CountUp value={q.price} delay={8 + i * 6}
                         style={{ fontFamily: display, fontSize: 54, fontWeight: 600, color: color.text }} />
                <div style={{ fontFamily: body, fontSize: 30, fontWeight: 700, color: tone }}>
                  {arrow(q.changePct)} {fmtPct(q.changePct)}
                </div>
                <div style={{ position: "absolute", right: 24, bottom: 26 }}>
                  <Sparkline series={q.series} width={130} height={56} tone={tone} />
                </div>
              </Panel>
            );
          })}
        </div>
        {lead && (
          <Panel style={{ marginTop: 24, padding: "22px 28px 8px", position: "relative" }}>
            <div style={{ fontFamily: body, fontSize: 24, color: color.muted, fontWeight: 600, marginBottom: 6 }}>
              {lead.name} · last month
            </div>
            <LineChart quote={lead} width={layout.contentW - 56} height={300} delay={20} />
          </Panel>
        )}
      </div>

      <div style={{ position: "absolute", top: 110, left: 0, width: "100%", opacity: phaseB }}>
        <Panel style={{ padding: "36px 44px", display: "flex", justifyContent: "space-between" }}>
          <MoverBars title="▲ Top gainers" quotes={gainers} tone={color.up} width={560} delay={split + 6}
                     emptyText="No gainers in our watchlist" />
          <MoverBars title="▼ Top decliners" quotes={losers} tone={color.down} width={560} delay={split + 14}
                     emptyText="Every stock on our watchlist rose" />
        </Panel>
        <div style={{ display: "flex", gap: 18, marginTop: 26 }}>
          {scene.bullets.map((b, i) => {
            const t = reveal(frame, split + 30 + i * 14);
            return (
              <Panel key={i} style={{ flex: 1, padding: "20px 24px", opacity: t,
                                      transform: `translateY(${(1 - t) * 20}px)` }}>
                <div style={{ fontFamily: body, fontSize: 27, color: color.text, fontWeight: 500, lineHeight: 1.3 }}>
                  {b}
                </div>
              </Panel>
            );
          })}
        </div>
      </div>
    </SceneFrame>
  );
};
