import type { PriceHistory } from "./contract";
import { PUBLIC_API_URL } from "./env";

export type Range = "1mo" | "6mo" | "1y";

export async function fetchHistory(symbol: string, range: Range, signal?: AbortSignal) {
  const res = await fetch(
    `${PUBLIC_API_URL}/api/markets/history/${encodeURIComponent(symbol)}?range=${range}`,
    { signal },
  );
  if (!res.ok) throw new Error(`history ${res.status}`);
  return (await res.json()) as PriceHistory;
}
