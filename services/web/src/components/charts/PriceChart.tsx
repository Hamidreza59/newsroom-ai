"use client";

import { fmtPrice } from "@newsroom/brand";
import {
  AreaSeries,
  ColorType,
  CrosshairMode,
  createChart,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";
import type { PricePoint } from "@/lib/contract";
import { useThemeColors } from "./useThemeColors";

interface Props {
  points: PricePoint[];
  name: string;
  height?: number;
}

const toTime = (date: string) => (Date.parse(`${date}T00:00:00Z`) / 1000) as UTCTimestamp;
const withAlpha = (hex: string, a: number) => `color-mix(in srgb, ${hex} ${a * 100}%, transparent)`;

export default function PriceChart({ points, name, height = 420 }: Props) {
  const colors = useThemeColors();
  const host = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);
  const seriesRef = useRef<ISeriesApi<"Area"> | null>(null);
  const tip = useRef<HTMLDivElement>(null);
  const byTimeRef = useRef(new Map<number, PricePoint>());
  const [hover, setHover] = useState<PricePoint | null>(null);

  const first = points[0]?.close ?? 0;
  const last = points[points.length - 1]?.close ?? 0;
  const up = last >= first;
  const line = up ? colors.up : colors.down;
  const byTime = useMemo(() => new Map<number, PricePoint>(points.map((p) => [toTime(p.date), p])), [points]);
  byTimeRef.current = byTime;

  useEffect(() => {
    if (!host.current) return;
    const chart = createChart(host.current, {
      autoSize: true,
      layout: { background: { type: ColorType.Solid, color: "transparent" }, fontFamily: "var(--font-jbmono), monospace", fontSize: 11, attributionLogo: false },
      grid: { vertLines: { visible: false }, horzLines: { color: "rgba(128,140,180,0.15)" } },
      rightPriceScale: { borderVisible: false, scaleMargins: { top: 0.12, bottom: 0.08 } },
      timeScale: { borderVisible: false, fixLeftEdge: true, fixRightEdge: true },
      crosshair: { mode: CrosshairMode.Magnet, vertLine: { labelVisible: false }, horzLine: { visible: false, labelVisible: false } },
      handleScale: false,
      handleScroll: false,
    });
    const series = chart.addSeries(AreaSeries, { lineWidth: 2, priceLineVisible: false, crosshairMarkerRadius: 5 });
    chartRef.current = chart;
    seriesRef.current = series;

    chart.subscribeCrosshairMove((param) => {
      const el = tip.current;
      const t = param.time as UTCTimestamp | undefined;
      const p = t ? byTimeRef.current.get(t) : undefined;
      if (!el || !p || !param.point) {
        if (el) el.style.opacity = "0";
        setHover(null);
        return;
      }
      setHover(p);
      const w = host.current?.clientWidth ?? 0;
      el.style.opacity = "1";
      el.style.transform = `translate(${Math.min(Math.max(param.point.x - 70, 4), w - 150)}px, 8px)`;
    });

    return () => {
      chart.remove();
      chartRef.current = null;
      seriesRef.current = null;
    };
  }, []);

  useEffect(() => {
    const series = seriesRef.current;
    if (!series) return;
    series.setData(points.map((p) => ({ time: toTime(p.date), value: p.close })));
    chartRef.current?.timeScale().fitContent();
  }, [points]);

  useEffect(() => {
    chartRef.current?.applyOptions({
      layout: { textColor: colors.muted },
      grid: { horzLines: { color: colors.border } },
      crosshair: { vertLine: { color: colors.muted, labelBackgroundColor: colors["surface-2"] } },
    });
    seriesRef.current?.applyOptions({
      lineColor: line,
      topColor: withAlpha(line, 0.32),
      bottomColor: withAlpha(line, 0),
      crosshairMarkerBackgroundColor: line,
    });
  }, [colors, line]);

  const pct = first ? ((last - first) / first) * 100 : 0;
  const summary = `${name} price chart, ${points[0]?.date ?? ""} to ${points[points.length - 1]?.date ?? ""}. Opened at ${fmtPrice(first)}, closed at ${fmtPrice(last)}, ${pct >= 0 ? "up" : "down"} ${Math.abs(pct).toFixed(2)} percent.`;

  return (
    <div className="relative" role="img" aria-label={summary} style={{ height }}>
      <div ref={host} className="absolute inset-0" />
      <div
        ref={tip}
        className="pointer-events-none absolute left-0 top-0 z-10 w-[140px] rounded-lg border border-line-strong bg-surface px-3 py-2 text-xs opacity-0 shadow-lg transition-opacity"
        style={{ boxShadow: "var(--shadow)" }}
      >
        {hover && (
          <>
            <div className="text-muted">{new Date(`${hover.date}T12:00:00Z`).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })}</div>
            <div className="num mt-0.5 text-sm font-semibold">{fmtPrice(hover.close)}</div>
          </>
        )}
      </div>
    </div>
  );
}
