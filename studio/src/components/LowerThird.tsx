import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { anchorColor, body, color, display, layout } from "../theme";
import type { Anchor, Caption } from "../types";

export const LowerThird: React.FC<{ captions: Caption[]; anchors: Anchor[] }> = ({ captions, anchors }) => {
  const frame = useCurrentFrame();
  const cap = captions.find((c) => frame >= c.startFrame && frame < c.endFrame + 6);
  if (!cap) return null;
  const opacity = interpolate(frame, [cap.startFrame, cap.startFrame + 5, cap.endFrame, cap.endFrame + 6],
    [0, 1, 1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const name = anchors.find((a) => a.id === cap.speaker)?.name ?? "";
  const tone = anchorColor(cap.speaker);
  return (
    <div style={{ position: "absolute", left: 0, width: layout.width, bottom: layout.tickerH + 20, display: "flex",
                  justifyContent: "center", opacity }}>
      <div style={{ display: "flex", alignItems: "stretch", maxWidth: 1400, borderRadius: 14, overflow: "hidden",
                    background: "rgba(6,10,26,0.88)", border: `1.5px solid ${color.panelBorder}`,
                    boxShadow: "0 12px 40px rgba(0,0,0,0.45)" }}>
        <div style={{ background: tone, color: color.bg0, fontFamily: display, fontWeight: 700, fontSize: 24,
                      letterSpacing: 3, padding: "0 20px", display: "flex", alignItems: "center" }}>
          {name.toUpperCase()}
        </div>
        <div style={{ padding: "12px 24px", color: color.text, fontFamily: body, fontSize: 29, lineHeight: 1.3,
                      fontWeight: 500 }}>
          {cap.text}
        </div>
      </div>
    </div>
  );
};
