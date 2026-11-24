import React from "react";
import { Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { body, color, display, fmtDate, fmtPct, fmtPrice, moveColor } from "../theme";
import type { PricePoint, Quote } from "../types";

const toPoints = (series: PricePoint[], w: number, h: number, pad = 0) => {
  const closes = series.map((p) => p.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const span = max - min || 1;
  return {
    min,
    max,
    pts: closes.map((c, i) => ({
      x: (i / Math.max(1, closes.length - 1)) * w,
      y: pad + (1 - (c - min) / span) * (h - pad * 2),
    })),
  };
};

const pathOf = (pts: { x: number; y: number }[]) =>
  pts.map((p, i) => `${i ? "L" : "M"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(" ");

const lengthOf = (pts: { x: number; y: number }[]) =>
  pts.slice(1).reduce((acc, p, i) => acc + Math.hypot(p.x - pts[i].x, p.y - pts[i].y), 0);

export const LineChart: React.FC<{ quote: Quote; width: number; height: number; delay?: number }> = ({
  quote,
  width,
  height,
  delay = 0,
}) => {
  const frame = useCurrentFrame() - delay;
  const padL = 24;
  const padR = 170;
  const w = width - padL - padR;
  const h = height - 70;
  const { pts, min, max } = toPoints(quote.series, w, h, 16);
  const len = lengthOf(pts);
  const progress = interpolate(frame, [0, 50], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic),
  });
  const monthPct = (quote.price / quote.series[0].close - 1) * 100;
  const tone = moveColor(monthPct);
  const last = pts[pts.length - 1];
  const pulse = 1 + 0.25 * Math.sin(frame / 6);
  const area = `${pathOf(pts)} L${w} ${h} L0 ${h} Z`;
  const gridYs = [0.15, 0.5, 0.85];

  return (
    <svg width={width} height={height} style={{ overflow: "visible", fontFamily: body }}>
      <defs>
        <linearGradient id={`area-${quote.symbol}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor={tone} stopOpacity="0.38" />
          <stop offset="1" stopColor={tone} stopOpacity="0" />
        </linearGradient>
        <clipPath id={`reveal-${quote.symbol}`}>
          <rect x="0" y="-20" width={w * progress + 2} height={h + 40} />
        </clipPath>
      </defs>
      <g transform={`translate(${padL} 10)`}>
        {gridYs.map((g) => (
          <g key={g}>
            <line x1="0" x2={w} y1={h * g} y2={h * g} stroke="rgba(255,255,255,0.08)" strokeDasharray="6 10" />
            <text x={w + 14} y={h * g + 8} fill={color.muted} fontSize="22">
              {fmtPrice(max - (max - min) * g)}
            </text>
          </g>
        ))}
        <path d={area} fill={`url(#area-${quote.symbol})`} clipPath={`url(#reveal-${quote.symbol})`} />
        <path d={pathOf(pts)} fill="none" stroke={tone} strokeWidth="6" strokeLinejoin="round"
              strokeLinecap="round" strokeDasharray={len} strokeDashoffset={len * (1 - progress)} />
        {progress > 0.98 && (
          <g>
            <circle cx={last.x} cy={last.y} r={16 * pulse} fill={tone} opacity="0.25" />
            <circle cx={last.x} cy={last.y} r="9" fill={tone} />
          </g>
        )}
        <text x="0" y={h + 46} fill={color.muted} fontSize="22">
          {fmtDate(quote.series[0].date, { month: "short", day: "numeric" })}
        </text>
        <text x={w} y={h + 46} fill={color.muted} fontSize="22" textAnchor="end">
          {fmtDate(quote.series[quote.series.length - 1].date, { month: "short", day: "numeric" })}
        </text>
        <text x={w / 2} y={h + 46} fill={tone} fontSize="24" fontWeight="700" textAnchor="middle"
              opacity={progress}>
          1 month: {fmtPct(monthPct)}
        </text>
      </g>
    </svg>
  );
};

export const Sparkline: React.FC<{ series: PricePoint[]; width: number; height: number; tone: string }> = ({
  series,
  width,
  height,
  tone,
}) => {
  const { pts } = toPoints(series, width, height, 4);
  return (
    <svg width={width} height={height}>
      <path d={pathOf(pts)} fill="none" stroke={tone} strokeWidth="3.5" strokeLinejoin="round"
            strokeLinecap="round" opacity="0.9" />
    </svg>
  );
};

export const CountUp: React.FC<{ value: number; delay?: number; style?: React.CSSProperties }> = ({
  value,
  delay = 0,
  style,
}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame - delay, [0, 30], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.quad),
  });
  return <span style={style}>{fmtPrice(value * (0.96 + 0.04 * t))}</span>;
};

export const MoverBars: React.FC<{
  title: string;
  quotes: Quote[];
  tone: string;
  width: number;
  delay: number;
  emptyText: string;
}> = ({ title, quotes, tone, width, delay, emptyText }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const maxPct = Math.max(1, ...quotes.map((q) => Math.abs(q.changePct)));
  const barMax = width - 330;
  return (
    <div style={{ width, fontFamily: body }}>
      <div style={{ fontFamily: display, fontSize: 34, fontWeight: 600, color: tone, marginBottom: 22,
                    letterSpacing: 1 }}>
        {title}
      </div>
      {quotes.length === 0 && (
        <div style={{ color: color.muted, fontSize: 28 }}>{emptyText}</div>
      )}
      {quotes.map((q, i) => {
        const s = spring({ frame: frame - delay - i * 8, fps, config: { damping: 16 } });
        return (
          <div key={q.symbol} style={{ display: "flex", alignItems: "center", gap: 18, marginBottom: 22,
                                       opacity: s, transform: `translateX(${(1 - s) * -40}px)` }}>
            <div style={{ width: 170, color: color.text, fontSize: 30, fontWeight: 600 }}>{q.name}</div>
            <div style={{ height: 44, width: (Math.abs(q.changePct) / maxPct) * barMax * s,
                          borderRadius: 12, background: `linear-gradient(90deg, ${tone}AA, ${tone})`,
                          boxShadow: `0 0 24px ${tone}55` }} />
            <div style={{ color: tone, fontSize: 30, fontWeight: 700, minWidth: 130 }}>
              {fmtPct(q.changePct)}
            </div>
          </div>
        );
      })}
    </div>
  );
};
