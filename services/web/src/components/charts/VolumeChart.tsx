"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { VolumePoint } from "@/lib/contract";
import { ChartTooltip } from "./ChartTooltip";
import { useThemeColors } from "./useThemeColors";

const day = (iso: string) => new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-US", { weekday: "short", timeZone: "UTC" });

export function VolumeChart({ data, color }: { data: VolumePoint[]; color: string }) {
  const c = useThemeColors();
  const total = data.reduce((a, d) => a + d.count, 0);
  const peak = Math.max(...data.map((d) => d.count), 0);
  return (
    <div role="img" aria-label={`Stories per day over the last 7 days: ${data.map((d) => `${day(d.date)} ${d.count}`).join(", ")}. Total ${total}.`} className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 4, left: -20, bottom: 0 }} accessibilityLayer={false}>
          <CartesianGrid vertical={false} stroke={c.border} />
          <XAxis dataKey="date" tickFormatter={day} tickLine={false} axisLine={false} tick={{ fill: c.muted, fontSize: 11 }} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fill: c.muted, fontSize: 11 }} width={40} />
          <Tooltip
            cursor={{ fill: c.border }}
            content={<ChartTooltip title={(p) => day(String(p))} format={(v) => `${v} ${v === 1 ? "story" : "stories"}`} />}
          />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={36} isAnimationActive={false}>
            {data.map((d) => (
              <Cell key={d.date} fill={color} fillOpacity={d.count === peak ? 1 : 0.55} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
