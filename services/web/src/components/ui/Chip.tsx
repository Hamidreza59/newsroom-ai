export function Chip({ children, color, className = "" }: { children: React.ReactNode; color?: string; className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[0.68rem] font-semibold uppercase tracking-wider ${className}`}
      style={{
        ["--cat" as string]: color ?? "var(--muted)",
        borderColor: "color-mix(in srgb, var(--cat) 45%, transparent)",
        background: "color-mix(in srgb, var(--cat) 12%, transparent)",
      }}
    >
      <span className="cat-text">{children}</span>
    </span>
  );
}
