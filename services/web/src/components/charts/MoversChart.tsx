"use client";

import { fmtPct } from "@newsroom/brand";
import { Bar, BarChart, Cell, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Quote } from "@/lib/contract";
import { ChartTooltip } from "./ChartTooltip";
import { useThemeColors } from "./useThemeColors";

export function MoversChart({ quotes, title }: { quotes: Quote[]; title: string }) {
  const c = useThemeColors();
  const data = quotes.map((q) => ({ name: q.symbol, label: q.name, pct: Math.abs(q.changePct), signed: q.changePct }));
  const max = Math.max(...data.map((d) => d.pct), 0.1);
  return (
    <div
      className="h-44"
      role="img"
      aria-label={`${title}: ${data.map((d) => `${d.label} ${fmtPct(d.signed)}`).join(", ")}`}
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 56, left: 0, bottom: 0 }} accessibilityLayer={false}>
          <XAxis type="number" hide domain={[0, max * 1.05]} />
          <YAxis type="category" dataKey="name" tickLine={false} axisLine={false} width={52} tick={{ fill: c.text, fontSize: 12, fontWeight: 600 }} />
          <Tooltip cursor={{ fill: c.border }} content={<ChartTooltip format={(v) => `${title === "Top losers" ? "−" : "+"}${v.toFixed(2)}%`} />} />
          <Bar dataKey="pct" radius={4} barSize={20} isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.name} fill={d.signed >= 0 ? c.up : c.down} />
            ))}
            <LabelList dataKey="pct" position="right" formatter={(v) => fmtPct(Number(v) * (title === "Top losers" ? -1 : 1))} style={{ fill: c.text, fontSize: 12, fontFamily: "var(--font-jbmono), monospace" }} />
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
