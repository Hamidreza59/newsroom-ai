import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Logo, Panel, Pill } from "../components/Chrome";
import { body, categoryColor, color, display, fmtDate } from "../theme";
import type { Episode } from "../types";
import { reveal, SceneFrame } from "./SceneFrame";

export const IntroScene: React.FC<{ episode: Episode }> = ({ episode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame: frame - 4, fps, config: { damping: 12, mass: 0.8 } });
  const market = episode.scenes.find((s) => s.type === "market");
  const stories = episode.scenes.filter((s) => s.type === "news").slice(0, 3);
  const rundown = [
    { label: "Markets", text: market?.headline ?? "", tone: color.gold },
    ...stories.map((s) => ({ label: s.category ?? "Tech", text: s.headline, tone: categoryColor(s.category) })),
  ];

  return (
    <SceneFrame>
      <Panel style={{ position: "absolute", inset: 0, padding: "56px 64px", boxSizing: "border-box" }}>
        <div style={{ transform: `scale(${0.7 + 0.3 * pop})`, transformOrigin: "left center", opacity: pop }}>
          <Logo name={episode.showName} size={92} />
        </div>
        <div style={{ marginTop: 26, display: "flex", gap: 18, alignItems: "center", opacity: reveal(frame, 18) }}>
          <Pill text="Daily briefing" fg={color.gold} />
          <div style={{ color: color.muted, fontFamily: body, fontSize: 30 }}>
            Markets · AI · Tech — {fmtDate(episode.date, { weekday: "long", month: "long", day: "numeric" })}
          </div>
        </div>
        <div style={{ marginTop: 54, fontFamily: display, fontSize: 36, color: color.text, fontWeight: 600,
                      opacity: reveal(frame, 34) }}>
          Today on the show
        </div>
        <div style={{ marginTop: 18 }}>
          {rundown.map((r, i) => {
            const t = reveal(frame, 44 + i * 12, 12);
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 16,
                                    opacity: t, transform: `translateX(${(1 - t) * 40}px)` }}>
                <div style={{ width: 14, height: 14, borderRadius: 7, background: r.tone,
                              boxShadow: `0 0 16px ${r.tone}` }} />
                <div style={{ fontFamily: body, fontSize: 21, fontWeight: 700, color: r.tone, width: 120,
                              letterSpacing: 2, textTransform: "uppercase" }}>{r.label}</div>
                <div style={{ fontFamily: body, fontSize: 31, color: color.text, fontWeight: 500,
                              whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 920 }}>
                  {r.text}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </SceneFrame>
  );
};
