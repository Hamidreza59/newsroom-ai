import { arrow, fmtPct } from "@newsroom/brand";

export function Delta({ value, className = "" }: { value: number; className?: string }) {
  return (
    <span className={`num whitespace-nowrap ${value >= 0 ? "up" : "down"} ${className}`}>
      <span aria-hidden="true" className="mr-0.5 text-[0.7em]">{arrow(value)}</span>
      {fmtPct(value)}
    </span>
  );
}
