import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Panel, Pill } from "../components/Chrome";
import { body, categoryColor, color, display } from "../theme";
import type { Scene } from "../types";
import { reveal, SceneFrame, useSceneDuration } from "./SceneFrame";

const ChipIcon: React.FC<{ tone: string; frame: number }> = ({ tone, frame }) => (
  <svg width="360" height="360" viewBox="0 0 100 100" style={{ transform: `rotate(${frame * 0.15}deg)` }}>
    <rect x="25" y="25" width="50" height="50" rx="8" fill="none" stroke={tone} strokeWidth="3" />
    <rect x="37" y="37" width="26" height="26" rx="4" fill={tone} opacity="0.5" />
    {[30, 40, 50, 60, 70].map((p) => (
      <g key={p} stroke={tone} strokeWidth="2.5" strokeLinecap="round">
        <line x1={p} y1="12" x2={p} y2="25" />
        <line x1={p} y1="75" x2={p} y2="88" />
        <line x1="12" y1={p} x2="25" y2={p} />
        <line x1="75" y1={p} x2="88" y2={p} />
      </g>
    ))}
  </svg>
);

export const NewsScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = useSceneDuration();
  const tone = categoryColor(scene.category);
  const pop = spring({ frame: frame - 6, fps, config: { damping: 14 } });
  const pointAt = (i: number) => Math.round(durationInFrames * (0.16 + i * 0.2));

  return (
    <SceneFrame>
      <Panel style={{ position: "absolute", inset: 0, padding: "48px 60px", boxSizing: "border-box", overflow: "hidden" }}>
        <div style={{ position: "absolute", right: -60, top: -40, opacity: 0.09 }}>
          <ChipIcon tone={tone} frame={frame} />
        </div>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Pill text={scene.category === "AI" ? "AI" : "Tech"} fg={tone} />
          {scene.followUp && <Pill text="Follow-up" fg={color.gold} />}
          <div style={{ marginLeft: "auto", fontFamily: body, fontSize: 24, color: color.muted, fontWeight: 600,
                        letterSpacing: 2 }}>
            STORY {scene.index} OF {scene.total}
          </div>
        </div>
        <div style={{ marginTop: 34, fontFamily: display, fontSize: 70, fontWeight: 600, lineHeight: 1.08,
                      color: color.text, maxWidth: 1060, opacity: pop,
                      transform: `translateY(${(1 - pop) * 24}px)` }}>
          {scene.headline}
        </div>
        <div style={{ width: 120 * pop, height: 8, borderRadius: 4, background: tone, marginTop: 28,
                      boxShadow: `0 0 20px ${tone}` }} />
        <div style={{ marginTop: 34 }}>
          {scene.bullets.map((p, i) => {
            const t = reveal(frame, pointAt(i));
            return (
              <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 20, marginBottom: 22, opacity: t,
                                    transform: `translateX(${(1 - t) * 36}px)` }}>
                <div style={{ marginTop: 13, width: 16, height: 16, borderRadius: 5, background: tone, flexShrink: 0 }} />
                <div style={{ fontFamily: body, fontSize: 34, color: color.text, lineHeight: 1.3, fontWeight: 500 }}>{p}</div>
              </div>
            );
          })}
        </div>
        <div style={{ position: "absolute", left: 60, bottom: 40, fontFamily: body, fontSize: 24, color: color.muted,
                      opacity: reveal(frame, 20) }}>
          Source: <span style={{ color: color.text, fontWeight: 600 }}>{scene.source}</span>
        </div>
      </Panel>
    </SceneFrame>
  );
};
