import type {
  EpisodeDetail,
  EpisodeSummary,
  Feature,
  FeatureSummary,
  Home,
  MarketOverview,
  NewsFeed,
} from "./contract";
import { SERVER_API_URL } from "./env";

async function get<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${SERVER_API_URL}${path}`, { next: { revalidate: 300 } });
    if (!res.ok) return null;
    return (await res.json()) as T;
  } catch {
    return null;
  }
}

export const getHome = () => get<Home>("/api/home");
export const getMarkets = () => get<MarketOverview>("/api/markets/overview");
export const getNews = (tab: string, limit = 40) =>
  get<NewsFeed>(`/api/news?tab=${encodeURIComponent(tab)}&limit=${limit}`);
export const getEpisodes = () => get<EpisodeSummary[]>("/api/episodes");
export const getEpisode = (date: string) => get<EpisodeDetail>(`/api/episodes/${encodeURIComponent(date)}`);
export const getFeatures = () => get<FeatureSummary[]>("/api/innovation");
export const getFeature = (slug: string) => get<Feature>(`/api/innovation/${encodeURIComponent(slug)}`);
