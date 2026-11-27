"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { SourceCount } from "@/lib/contract";
import { ChartTooltip } from "./ChartTooltip";
import { useThemeColors } from "./useThemeColors";

export function SourceDonut({ data, accent }: { data: SourceCount[]; accent: string }) {
  const c = useThemeColors();
  const total = data.reduce((a, d) => a + d.count, 0);
  const shade = (i: number) => `color-mix(in srgb, ${accent} ${Math.max(100 - i * 14, 30)}%, ${c.surface})`;
  return (
    <div className="flex items-center gap-5">
      <div
        className="relative h-44 w-44 shrink-0"
        role="img"
        aria-label={`Top sources: ${data.map((d) => `${d.source} ${d.count}`).join(", ")}. Total ${total} stories.`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart accessibilityLayer={false}>
            <Pie data={data} dataKey="count" nameKey="source" innerRadius="64%" outerRadius="100%" paddingAngle={2} stroke="none" isAnimationActive={false}>
              {data.map((d, i) => (
                <Cell key={d.source} fill={shade(i)} />
              ))}
            </Pie>
            <Tooltip content={<ChartTooltip format={(v) => `${v} stories`} />} />
          </PieChart>
        </ResponsiveContainer>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
          <span className="num text-2xl font-bold">{total}</span>
          <span className="text-[0.65rem] uppercase tracking-wider text-muted">stories</span>
        </div>
      </div>
      <ul className="min-w-0 flex-1 space-y-2 text-sm">
        {data.map((d, i) => (
          <li key={d.source} className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 shrink-0 rounded-sm" style={{ background: shade(i) }} aria-hidden="true" />
            <span className="truncate">{d.source}</span>
            <span className="num ml-auto text-muted">{Math.round((d.count / total) * 100)}%</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
