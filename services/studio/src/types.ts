import type { Episode as EpisodeContract, EpMarket, EpQuote } from "./contract";

export type { Anchor, Caption, PricePoint, Scene } from "./contract";

// Mapped so Remotion's Record<string, unknown> prop constraint accepts the generated interface.
export type Episode = { [K in keyof EpisodeContract]: EpisodeContract[K] };
export type Quote = EpQuote;
export type Market = EpMarket;
export type SceneType = EpisodeContract["scenes"][number]["type"];
