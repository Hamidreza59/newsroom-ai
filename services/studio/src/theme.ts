import { loadFont as loadFredoka } from "@remotion/google-fonts/Fredoka";
import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { color } from "@newsroom/brand";

export { arrow, color, fmtDate, fmtPct, fmtPrice, moveColor } from "@newsroom/brand";

export const display = loadFredoka("normal", { weights: ["500", "600", "700"], subsets: ["latin"] })
  .fontFamily;
export const body = loadInter("normal", { weights: ["400", "500", "600", "700"], subsets: ["latin"] })
  .fontFamily;

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

export const categoryColor = (c: "AI" | "Tech" | "Biotech" | null) =>
  c === "AI" ? color.ai : c === "Biotech" ? color.bio : color.tech;
