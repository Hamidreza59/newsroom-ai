import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { body, categoryColor, color, display, layout } from "../theme";
import type { Scene } from "../types";

const toneFor = (scene: Scene) =>
  scene.type === "market" ? color.gold : scene.followUp ? "#FF9F43" : categoryColor(scene.category);

const subtitleFor = (scene: Scene) =>
  scene.type === "market" ? "Closing bell" : `Story ${scene.index} of ${scene.total}`;

/** Full-screen "news alert" bumper played over the sting before each segment. */
export const AlertCard: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const total = scene.alertFrames;
  const tone = toneFor(scene);
  const W = layout.contentW;
  const H = layout.contentH;
  if (frame > total + 12) return null;

  const ease = { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) } as const;
  const wipeIn = interpolate(frame, [0, 10], [-1.3, 0], ease);
  const wipeOut = interpolate(frame, [total - 6, total + 10], [0, 1.3], ease);
  const x = (frame < total - 6 ? wipeIn : wipeOut) * W;
  const textPop = spring({ frame: frame - 9, fps, config: { damping: 11, stiffness: 160 } });
  const textOut = interpolate(frame, [total - 8, total], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const ring = (at: number) => {
    const t = interpolate(frame, [at, at + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
    return { scale: 0.4 + t * 1.6, opacity: (1 - t) * (frame >= at ? 0.8 : 0) };
  };
  const blink = Math.floor(frame / 5) % 2 === 0;

  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden", borderRadius: 28, zIndex: 10 }}>
      <div style={{ position: "absolute", top: -200, left: x - 200, width: W + 400, height: H + 400,
                    transform: "skewX(-14deg)", background: `linear-gradient(90deg, ${tone}, ${color.bg1} 18%, ${color.bg0} 82%, ${tone})` }}>
        <div style={{ position: "absolute", inset: 0, opacity: 0.12,
                      backgroundImage: `repeating-linear-gradient(90deg, ${tone} 0 22px, transparent 22px 64px)`,
                      backgroundPosition: `${frame * 6}px 0` }} />
      </div>

      {[12, 15, 18].map((at) => {
        const r = ring(at);
        return (
          <div key={at} style={{ position: "absolute", left: W / 2 - 220, top: H / 2 - 220, width: 440, height: 440,
                                 borderRadius: "50%", border: `6px solid ${tone}`, opacity: r.opacity * textOut,
                                 transform: `scale(${r.scale})` }} />
        );
      })}

      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center",
                    justifyContent: "center", opacity: textOut, transform: `scale(${0.6 + 0.4 * textPop})` }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "10px 26px", borderRadius: 999,
                      background: "rgba(229,48,63,0.18)", border: "2px solid #E5303F", fontFamily: body,
                      fontWeight: 800, fontSize: 26, letterSpacing: 6, color: "#FF6B78" }}>
          <div style={{ width: 16, height: 16, borderRadius: 8, background: "#FF3B4E", opacity: blink ? 1 : 0.25,
                        boxShadow: "0 0 18px #FF3B4E" }} />
          NEWS ALERT
        </div>
        <div style={{ marginTop: 22, fontFamily: display, fontWeight: 700, fontSize: 132, letterSpacing: 6,
                      color: color.text, textShadow: `0 0 40px ${tone}AA`, textTransform: "uppercase", lineHeight: 1 }}>
          {scene.alert}
        </div>
        <div style={{ marginTop: 18, width: 140 * textPop, height: 8, borderRadius: 4, background: tone,
                      boxShadow: `0 0 24px ${tone}` }} />
        <div style={{ marginTop: 20, fontFamily: body, fontWeight: 700, fontSize: 30, letterSpacing: 5,
                      color: color.muted, textTransform: "uppercase" }}>
          {subtitleFor(scene)}
        </div>
      </div>
    </div>
  );
};
