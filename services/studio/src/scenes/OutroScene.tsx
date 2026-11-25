import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Logo, Panel } from "../components/Chrome";
import { body, color, display } from "../theme";
import type { Episode } from "../types";
import { reveal, SceneFrame, useSceneDuration } from "./SceneFrame";

export const OutroScene: React.FC<{ episode: Episode }> = ({ episode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const durationInFrames = useSceneDuration();
  const clickAt = Math.min(70, Math.round(durationInFrames * 0.35));
  const pop = spring({ frame: frame - 4, fps, config: { damping: 12 } });
  const cursor = interpolate(frame, [20, clickAt], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const pressed = frame >= clickAt;
  const press = spring({ frame: frame - clickAt, fps, config: { damping: 8, stiffness: 220 } });
  const scale = pressed ? 0.92 + 0.08 * press : 1;

  return (
    <SceneFrame>
      <Panel style={{ position: "absolute", inset: 0, padding: "64px", boxSizing: "border-box",
                      display: "flex", flexDirection: "column", alignItems: "center" }}>
        <div style={{ opacity: pop, transform: `scale(${0.8 + 0.2 * pop})` }}>
          <Logo name={episode.showName} size={60} />
        </div>
        <div style={{ marginTop: 40, fontFamily: display, fontSize: 84, fontWeight: 700, color: color.text }}>
          Thanks for watching!
        </div>
        <div style={{ marginTop: 14, fontFamily: body, fontSize: 32, color: color.muted, opacity: reveal(frame, 12) }}>
          A new episode every weekday after the closing bell
        </div>
        <div style={{ position: "relative", marginTop: 56 }}>
          <div style={{ transform: `scale(${scale})`, padding: "24px 64px", borderRadius: 999,
                        background: pressed ? "#3A4366" : "#E5303F", color: "#fff", fontFamily: body,
                        fontSize: 40, fontWeight: 800, letterSpacing: 1,
                        boxShadow: pressed ? "none" : "0 18px 50px rgba(229,48,63,0.45)" }}>
            {pressed ? "✓ SUBSCRIBED" : "SUBSCRIBE"}
          </div>
          <svg width="56" height="56" viewBox="0 0 24 24"
               style={{ position: "absolute", left: interpolate(cursor, [0, 1], [460, 250]),
                        top: interpolate(cursor, [0, 1], [170, 50]), opacity: frame > clickAt + 30 ? 0 : 1 }}>
            <path d="M4 2 L4 20 L9 15 L12.5 22 L15.5 20.5 L12 14 L19 14 Z" fill="#fff" stroke={color.bg0} strokeWidth="1.2" />
          </svg>
        </div>
        <div style={{ position: "absolute", bottom: 44, left: 80, right: 80, textAlign: "center",
                      fontFamily: body, fontSize: 22, color: color.muted, lineHeight: 1.4, opacity: reveal(frame, 24) }}>
          {episode.disclaimer}
          {episode.market.sampleData ? " Market figures shown are sample data." : ""}
        </div>
      </Panel>
    </SceneFrame>
  );
};
