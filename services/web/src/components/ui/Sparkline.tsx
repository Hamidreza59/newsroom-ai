import { useId } from "react";
import type { PricePoint } from "@/lib/contract";

interface Props {
  series: PricePoint[];
  width?: number;
  height?: number;
  className?: string;
  label?: string;
}

export function Sparkline({ series, width = 120, height = 36, className, label }: Props) {
  const id = useId();
  if (series.length < 2) return null;
  const closes = series.map((p) => p.close);
  const min = Math.min(...closes);
  const span = Math.max(...closes) - min || 1;
  const pad = 2;
  const pts = closes.map((c, i) => [
    (i / (closes.length - 1)) * width,
    pad + (1 - (c - min) / span) * (height - pad * 2),
  ]);
  const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const area = `${line} L${width} ${height} L0 ${height} Z`;
  const up = closes[closes.length - 1] >= closes[0];
  const stroke = up ? "var(--up)" : "var(--down)";
  const first = series[0];
  const last = series[series.length - 1];
  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width={width}
      height={height}
      className={className}
      role="img"
      aria-label={label ?? `Price trend from ${first.date} to ${last.date}, ${up ? "up" : "down"}`}
      preserveAspectRatio="none"
    >
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={stroke} stopOpacity="0.28" />
          <stop offset="100%" stopColor={stroke} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`} />
      <path d={line} fill="none" stroke={stroke} strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}
