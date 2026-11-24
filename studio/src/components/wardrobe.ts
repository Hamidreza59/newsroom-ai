export type Outfit = {
  style: "blazer" | "blouse" | "tie" | "open-collar" | "turtleneck";
  jacket: string;
  top: string;
  accent: string;
  pattern: boolean;
};

const MAYA_JACKETS = ["#14858A", "#8C2F45", "#22336E", "#C7922E", "#2F6B4F", "#6B3E8C", "#3A3F4B", "#D9654B"];
const MAYA_TOPS = ["#F5ECDF", "#FFFFFF", "#1A1A22", "#F2C9C4", "#D8E4F2"];
const JEWELRY = ["#E9B949", "#D7DCE6", "#F4F1EA"];
const LEO_SUITS = ["#1E2B5C", "#3A3F4B", "#5F6672", "#5B4636", "#1C1F2A", "#2E5AA8", "#2F5446"];
const LEO_SHIRTS = ["#F4F6FF", "#CFE0F5", "#F3D6DD", "#E9E4D8"];
const TIES = ["#FF5C70", "#E0A73A", "#1CA3A8", "#7C5CC4", "#1A2550", "#B33A3A"];

const hash = (s: string) => {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
};

const rng = (seed: string) => {
  let t = hash(seed);
  return () => {
    t = (t + 0x6d2b79f5) >>> 0;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r = (r + Math.imul(r ^ (r >>> 7), 61 | r)) ^ r;
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
};

const pick = <T,>(r: () => number, items: T[]) => items[Math.floor(r() * items.length)];

/** Deterministic per-episode outfit: same date → same clothes in video and thumbnail. */
export const outfitFor = (id: "a" | "b", seed: string): Outfit => {
  const r = rng(`${seed}:${id}`);
  if (id === "a") {
    const style = pick(r, ["blazer", "blazer", "blouse", "turtleneck"] as const);
    const jacket = pick(r, MAYA_JACKETS);
    let top = pick(r, MAYA_TOPS);
    if (style === "turtleneck" && top === "#FFFFFF") top = "#1A1A22";
    return { style, jacket, top, accent: pick(r, JEWELRY), pattern: false };
  }
  const style = pick(r, ["tie", "tie", "tie", "open-collar", "turtleneck"] as const);
  return {
    style,
    jacket: pick(r, LEO_SUITS),
    top: style === "turtleneck" ? pick(r, ["#1A1A22", "#E9E4D8", "#3A3F4B"]) : pick(r, LEO_SHIRTS),
    accent: pick(r, TIES),
    pattern: r() < 0.35,
  };
};

export const lighten = (hex: string, amount: number) => {
  const n = parseInt(hex.slice(1), 16);
  const ch = (shift: number) => Math.min(255, Math.round(((n >> shift) & 255) + (255 - ((n >> shift) & 255)) * amount));
  return `#${[16, 8, 0].map((s) => ch(s).toString(16).padStart(2, "0")).join("")}`;
};
