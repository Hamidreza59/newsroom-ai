# newsroom-api

FastAPI service behind the website. It is an MCP client of `newsroom-mcp` (markets, tagged news,
price history) and reads published content from `OUT_DIR` (episodes written by the publisher,
weekly features written by `newsroom-agents weekly`). Responses are camelCase JSON; the models live
in `packages/newsroom-core/src/newsroom_core/site.py` and the JSON Schema in
`packages/contracts/site.schema.json` (regenerate with `make contracts`).

```bash
make api                                  # or: uv run --native-tls newsroom-api
NEWSROOM_OFFLINE=1 make api               # sample market data and news, no network
make site-data                            # offline sample episodes and features in out/
```

| Env | Default | Meaning |
|---|---|---|
| `API_HOST` / `API_PORT` | `127.0.0.1` / `8000` | Bind address |
| `WEB_ORIGIN` | `http://localhost:3000` | CORS origin(s), comma separated |
| `MCP_URL` | empty | Streamable HTTP MCP server (`http://127.0.0.1:8765/mcp`); empty spawns `newsroom_mcp.server` over stdio |
| `OUT_DIR`, `DATA_DIR` | `./out`, `./data` | Published content and state |
| `NEWSROOM_OFFLINE` | `0` | Sample market data and news |

Upstream data is cached in memory: news for 10 minutes, markets and price history for 15. If the
MCP server is unreachable, endpoints that need it return `503 {"detail": "upstream data
unavailable"}`; episodes and features keep working because they only read files.

## Endpoints

All JSON is camelCase. Errors: `404` unknown symbol, episode, feature or media file; `422` invalid
query or path value (bad `range`, `tab`, `limit`, date or slug format).

| Endpoint | Response model |
|---|---|
| `GET /api/health` | `Health` |
| `GET /api/markets/overview` | `MarketOverview` |
| `GET /api/markets/history/{symbol}?range=1mo\|6mo\|1y` (default `6mo`) | `PriceHistory` |
| `GET /api/news?tab=markets\|ai\|ai-finance\|tech\|biotech&limit=40` (`limit` 1-100) | `NewsFeed` |
| `GET /api/home` | `Home` |
| `GET /api/episodes` | `EpisodeSummary[]`, newest first |
| `GET /api/episodes/{date}` (`YYYY-MM-DD`) | `EpisodeDetail` |
| `GET /api/innovation` | `FeatureSummary[]`, newest first |
| `GET /api/innovation/{slug}` | `Feature` |
| `GET /media/{date}/{name}` | `video.mp4`, `short.mp4` or `thumbnail.png` only |

Types below are TypeScript-style; `?` is never used, optional values are `null`.

```ts
Health        { status: "ok"; offline: boolean }
PricePoint    { date: string; close: number }                         // date = YYYY-MM-DD
Quote         { symbol; name; price; change; changePct: number; series: PricePoint[] }
Sector        { name: string; changePct: number;                     // mean of members
                members: { symbol; name: string; changePct: number }[] }
MarketOverview{ asOf: string; sampleData: boolean; indices: Quote[];  // 1-month series each
                watchlist: Quote[]; gainers: Quote[]; losers: Quote[]; // 3 each
                sectors: Sector[] }                                    // AI & Chips, Big Tech, Biotech
PriceHistory  { symbol; name: string; range: "1mo"|"6mo"|"1y"; points: PricePoint[] }
SiteNewsItem  { id; title; url; source; published: string /*ISO*/; summary; category: string;
                tags: string[] /* ai|tech|biotech|markets|ai-finance */; score: number }
NewsFeed      { tab; label; updatedAt: string /*ISO*/; items: SiteNewsItem[];
                volume: { date: string; count: number }[];             // last 7 days, oldest first
                topSources: { source: string; count: number }[];       // top 6
                keywords: { term: string; count: number }[] }          // top 12 title words
Home          { latestEpisode: EpisodeSummary | null; markets: MarketOverview;
                topStories: { tab; label; items: SiteNewsItem[] }[];   // 5 tabs, 3 items each
                feature: FeatureSummary | null }
EpisodeSummary{ date; title; summary: string; durationSeconds: number | null; storyCount: number;
                thumbnailUrl; videoUrl; shortUrl: string | null }      // "/media/<date>/<file>"
EpisodeDetail = EpisodeSummary + { show; disclaimer: string; tags: string[];
                chapters: { time: string; title: string }[];
                sources: { title; publisher; url: string }[];
                quiz: { question: string; options: string[]; reveal: string; answer: string | null } | null;
                scriptMarkdown: string | null }
FeatureSummary{ slug; week /*2026-W48*/; title; dek; topic: string; readingMinutes: number;
                publishedAt: string /*ISO*/ }
Feature = FeatureSummary + { sections: { heading; body: string }[]; takeaways: string[];
                glossary: { term; definition: string }[];
                related: { title; url; source: string }[]; sources: { title; url: string }[];
                disclaimer: string; generatedBy: { agent; model: string } }
```

News items are ordered by `(1 + score)` weighted by recency (the weight halves every 48 hours). A
story can carry several tags and appears in every matching tab; items tagged only `markets` come
from finance feeds and never reach the daily video. `tab` defaults to `ai`.

Media URLs are `null` when the file was not rendered. Serve them from the API origin (for example
`<video src="http://localhost:8000/media/2026-11-26/video.mp4">`).

### Examples

`GET /api/health`

```json
{"status": "ok", "offline": false}
```

`GET /api/markets/overview` (series shortened)

```json
{
  "asOf": "2026-11-26", "sampleData": false,
  "indices": [{"symbol": "^GSPC", "name": "S&P 500", "price": 6097.64, "change": 49.83,
               "changePct": 0.82, "series": [{"date": "2026-10-29", "close": 5980.1}]}],
  "watchlist": [], "gainers": [], "losers": [],
  "sectors": [{"name": "AI & Chips", "changePct": 1.24,
               "members": [{"symbol": "NVDA", "name": "Nvidia", "changePct": 2.1}]}]
}
```

`GET /api/news?tab=ai-finance&limit=1`

```json
{
  "tab": "ai-finance", "label": "AI in Finance", "updatedAt": "2026-11-27T14:47:00+00:00",
  "items": [{"id": "017432f1728c", "title": "Bank rolls out AI assistant to speed up fraud investigations",
             "url": "https://example.com/sample/10", "source": "Sample Fintech Review",
             "published": "2026-11-27T08:47:00+00:00", "summary": "Analysts at the bank use the assistant ...",
             "category": "AI", "tags": ["ai", "markets", "ai-finance"], "score": 1.9}],
  "volume": [{"date": "2026-11-21", "count": 0}, {"date": "2026-11-27", "count": 3}],
  "topSources": [{"source": "Sample Fintech Review", "count": 3}],
  "keywords": [{"term": "assistant", "count": 2}]
}
```

`GET /api/episodes`

```json
[{"date": "2026-11-26", "title": "S&P 500 up 0.8% ... | Bits & Bulls Nov 26",
  "summary": "Markets: ... Top stories: ...", "durationSeconds": 197, "storyCount": 5,
  "thumbnailUrl": "/media/2026-11-26/thumbnail.png", "videoUrl": "/media/2026-11-26/video.mp4",
  "shortUrl": null}]
```

`GET /api/innovation/2026-w48-earnings` (shortened)

```json
{
  "slug": "2026-w48-earnings", "week": "2026-W48", "title": "What are earnings reports?",
  "dek": "A plain-language explainer ...", "topic": "What are earnings reports?",
  "readingMinutes": 1, "publishedAt": "2026-11-23T12:00:00+00:00",
  "sections": [{"heading": "The short version", "body": "..."}],
  "takeaways": ["..."], "glossary": [{"term": "earnings reports", "definition": "..."}],
  "related": [{"title": "...", "url": "https://...", "source": "..."}],
  "sources": [{"title": "...", "url": "https://..."}],
  "disclaimer": "This article was written by an AI agent ...",
  "generatedBy": {"agent": "feature-writer", "model": "template-fallback"}
}
```

`generatedBy.model` is the LLM that wrote the article, or `template-fallback` when the guardrails
rejected the draft (or no model was available) and the article was built from the knowledge base.

## Deploy

The service is stateless apart from its cache. Build with `docker build -f services/api/Dockerfile .`
(context = repo root), set `MCP_URL` to the MCP service and mount or sync `OUT_DIR`. It fits
Lambda behind API Gateway (with a Lambda web adapter) or App Runner.
