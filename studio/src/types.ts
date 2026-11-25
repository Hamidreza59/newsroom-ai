export type PricePoint = { date: string; close: number };

export type Quote = {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePct: number;
  series: PricePoint[];
};

export type Market = {
  asOf: string;
  indices: Quote[];
  gainers: Quote[];
  losers: Quote[];
  sampleData: boolean;
};

export type Caption = { text: string; speaker: "a" | "b"; startFrame: number; endFrame: number };

export type Anchor = { id: "a" | "b"; name: string };

export type SceneType = "coldopen" | "intro" | "market" | "explainer" | "news" | "quiz" | "outro";

export type Scene = {
  type: SceneType;
  startFrame: number;
  durationInFrames: number;
  narration: string;
  headline: string;
  bullets: string[];
  source: string;
  category: "AI" | "Tech" | "Biotech" | null;
  followUp: boolean;
  index: number;
  total: number;
  alert: string;
  alertFrames: number;
  options: string[];
  reveal: string;
};

export type Episode = {
  date: string;
  showName: string;
  fps: number;
  width: number;
  height: number;
  durationInFrames: number;
  audioFile: string | null;
  market: Market;
  ticker: Quote[];
  scenes: Scene[];
  captions: Caption[];
  youtube: { title: string; description: string; tags: string[] };
  disclaimer: string;
  anchors: Anchor[];
  mouths: Record<string, number[]>;
  short: { title: string; clips: { startFrame: number; endFrame: number }[]; durationInFrames: number } | null;
};
