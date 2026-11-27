"use client";

interface Payload {
  value?: number | string;
  name?: string | number;
  color?: string;
}

interface Props {
  active?: boolean;
  label?: string | number;
  payload?: Payload[];
  title?: (label: string | number) => string;
  format?: (value: number) => string;
}

export function ChartTooltip({ active, payload, label, title, format }: Props) {
  if (!active || !payload?.length) return null;
  const item = payload[0];
  const heading = title && label !== undefined ? title(label) : (item.name ?? label);
  return (
    <div className="rounded-lg border border-line-strong bg-surface px-3 py-2 text-xs" style={{ boxShadow: "var(--shadow)" }}>
      <div className="text-muted">{heading}</div>
      <div className="num mt-0.5 text-sm font-semibold">
        {format ? format(Number(item.value)) : item.value}
      </div>
    </div>
  );
}
