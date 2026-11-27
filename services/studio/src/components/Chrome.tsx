import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Logo as BrandLogo } from "@newsroom/brand";
import { body, color, display, fmtDate, layout } from "../theme";

export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const a = frame / 240;
  const x1 = 30 + Math.sin(a) * 12;
  const y1 = 25 + Math.cos(a * 0.8) * 10;
  const x2 = 75 + Math.cos(a * 0.6) * 12;
  const y2 = 80 + Math.sin(a * 0.9) * 8;
  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(900px 700px at ${x1}% ${y1}%, rgba(34,211,238,0.16), transparent 60%),
          radial-gradient(1000px 800px at ${x2}% ${y2}%, rgba(167,139,250,0.16), transparent 60%),
          linear-gradient(160deg, ${color.bg1} 0%, ${color.bg0} 70%)`,
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          backgroundPosition: `${(frame * 0.4) % 64}px 0px`,
          maskImage: "linear-gradient(180deg, transparent 0%, black 30%, black 70%, transparent 100%)",
        }}
      />
    </AbsoluteFill>
  );
};

export const Logo: React.FC<{ size?: number; name: string }> = ({ size, name }) => (
  <BrandLogo name={name} size={size} fontFamily={display} />
);

export const Header: React.FC<{ showName: string; date: string; label: string }> = ({
  showName,
  date,
  label,
}) => (
  <div
    style={{
      position: "absolute", left: 0, top: 0, width: layout.width, height: layout.headerH,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      padding: "0 56px", boxSizing: "border-box",
      background: "linear-gradient(180deg, rgba(6,10,26,0.85), rgba(6,10,26,0))",
    }}
  >
    <Logo name={showName} size={34} />
    <div style={{ display: "flex", gap: 16, alignItems: "center", fontFamily: body }}>
      <div style={{ padding: "8px 18px", borderRadius: 999, border: `2px solid ${color.panelBorder}`,
                    color: color.text, fontWeight: 600, fontSize: 22, letterSpacing: 2 }}>
        {label}
      </div>
      <div style={{ color: color.muted, fontSize: 24, fontWeight: 500 }}>
        {fmtDate(date, { weekday: "long", month: "long", day: "numeric", year: "numeric" })}
      </div>
    </div>
  </div>
);

export const Panel: React.FC<{ children: React.ReactNode; style?: React.CSSProperties }> = ({
  children,
  style,
}) => (
  <div
    style={{
      background: color.panel, border: `1.5px solid ${color.panelBorder}`, borderRadius: 28,
      boxShadow: "0 30px 80px rgba(0,0,0,0.35)", backdropFilter: "blur(8px)", ...style,
    }}
  >
    {children}
  </div>
);

export const Pill: React.FC<{ text: string; fg: string; bg?: string; size?: number }> = ({
  text,
  fg,
  bg,
  size = 22,
}) => (
  <div
    style={{
      display: "inline-flex", alignItems: "center", gap: 10, padding: `${size * 0.35}px ${size * 0.8}px`,
      borderRadius: 999, background: bg ?? `${fg}22`, border: `2px solid ${fg}`, color: fg,
      fontFamily: body, fontWeight: 700, fontSize: size, letterSpacing: 2, textTransform: "uppercase",
    }}
  >
    {text}
  </div>
);
