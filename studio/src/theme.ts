import { loadFont as loadFredoka } from "@remotion/google-fonts/Fredoka";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";

export const display = loadFredoka("normal", { weights: ["500", "600", "700"], subsets: ["latin"] })
  .fontFamily;
export const body = loadInter("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] })
  .fontFamily;

export const color = {
  bg0: "#060A1A",
  bg1: "#0D1533",
  bg2: "#16224D",
  panel: "rgba(255,255,255,0.055)",
  panelBorder: "rgba(255,255,255,0.12)",
  text: "#F4F6FF",
  muted: "#A3ADD3",
  up: "#2BD97C",
  down: "#FF5C70",
  ai: "#22D3EE",
  tech: "#A78BFA",
  gold: "#FFC53D",
  suit: "#1E2B5C",
  tie: "#FF5C70",
} as const;

export const layout = {
  width: 1920,
  height: 1080,
  headerH: 96,
  tickerH: 72,
  contentW: 1240,
  contentH: 700,
  screen: { x: 462, y: 112, w: 996 },
} as const;

export const anchorColor = (id: "a" | "b") => (id === "a" ? color.ai : color.gold);

export const categoryColor = (c: "AI" | "Tech" | null) => (c === "AI" ? color.ai : color.tech);

const num = new Intl.NumberFormat("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
const whole = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });

export const fmtPrice = (v: number) => (v >= 10000 ? whole.format(v) : num.format(v));
export const fmtPct = (v: number) => `${v >= 0 ? "+" : "−"}${Math.abs(v).toFixed(2)}%`;
export const moveColor = (v: number) => (v >= 0 ? color.up : color.down);
export const arrow = (v: number) => (v >= 0 ? "▲" : "▼");

export const fmtDate = (iso: string, opts: Intl.DateTimeFormatOptions) =>
  new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-US", { timeZone: "UTC", ...opts });
