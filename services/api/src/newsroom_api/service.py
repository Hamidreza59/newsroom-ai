"""Builds website responses from MCP tool results, with TTL caching."""

from __future__ import annotations

import re
from collections import Counter
from datetime import UTC, datetime, timedelta

from newsroom_core.config import INDICES, SECTORS, WATCHLIST, Settings
from newsroom_core.models import MarketSnapshot, NewsItem, PricePoint
from newsroom_core.site import (
    TAB_LABELS,
    HistoryRange,
    KeywordCount,
    MarketOverview,
    NewsFeed,
    PriceHistory,
    Quote,
    Sector,
    SectorMember,
    SiteNewsItem,
    SourceCount,
    Tab,
    TopStories,
    VolumePoint,
)
from newsroom_core.text import tokens

from newsroom_api.cache import TTLCache
from newsroom_api.mcp import call_tools

NEWS_TTL = 600
MARKET_TTL = 900
TABS: list[Tab] = ["markets", "ai", "ai-finance", "tech", "biotech"]
TAB_WORDS: dict[str, set[str]] = {
    "markets": {"stock", "stocks", "market", "markets", "shares", "wall", "street"},
    "ai": {"artificial", "intelligence"},
    "ai-finance": {"artificial", "intelligence", "finance", "financial", "banks", "banking"},
    "tech": {"tech", "technology"},
    "biotech": {"biotech", "biotechnology"},
}
SYMBOLS = {**INDICES, **WATCHLIST}
DIGITS = re.compile(r"^\d+$")


def _published(item: NewsItem) -> datetime:
    when = datetime.fromisoformat(item.published)
    return when if when.tzinfo else when.replace(tzinfo=UTC)


def rank(item: NewsItem, now: datetime) -> float:
    """Score weighted by recency: the weight halves every 48 hours."""
    age_hours = max(0.0, (now - _published(item)).total_seconds() / 3600)
    return (1 + item.score) * 0.5 ** (age_hours / 48)


def site_item(item: NewsItem) -> SiteNewsItem:
    return SiteNewsItem(
        id=item.id, title=item.title, url=item.url, source=item.source, published=item.published,
        summary=item.summary, category=item.category, tags=item.tags, score=round(item.score, 3))


def build_feed(tab: Tab, items: list[NewsItem], limit: int, updated: datetime,
               now: datetime | None = None) -> NewsFeed:
    now = now or datetime.now(UTC)
    tabbed = sorted((i for i in items if tab in i.tags), key=lambda i: -rank(i, now))
    today = now.date()
    days = [(today - timedelta(days=n)).isoformat() for n in range(6, -1, -1)]
    per_day = Counter(_published(i).astimezone(UTC).date().isoformat() for i in tabbed)
    skip = TAB_WORDS[tab] | tokens(TAB_LABELS[tab])
    words = Counter(t for i in tabbed for t in tokens(i.title)
                    if t not in skip and not DIGITS.match(t))
    return NewsFeed(
        tab=tab, label=TAB_LABELS[tab], updated_at=updated.isoformat(),
        items=[site_item(i) for i in tabbed[:limit]],
        volume=[VolumePoint(date=d, count=per_day.get(d, 0)) for d in days],
        top_sources=[SourceCount(source=s, count=n)
                     for s, n in sorted(Counter(i.source for i in tabbed).items(),
                                        key=lambda p: (-p[1], p[0]))[:6]],
        keywords=[KeywordCount(term=t, count=n)
                  for t, n in sorted(words.items(), key=lambda p: (-p[1], p[0]))[:12]],
    )


def build_overview(snap: MarketSnapshot) -> MarketOverview:
    def quote(q) -> Quote:
        return Quote(**q.model_dump())

    by_symbol = {q.symbol: q for q in snap.watchlist}
    sectors = []
    for name, symbols in SECTORS.items():
        members = [by_symbol[s] for s in symbols if s in by_symbol]
        if members:
            sectors.append(Sector(
                name=name,
                change_pct=round(sum(m.change_pct for m in members) / len(members), 2),
                members=[SectorMember(symbol=m.symbol, name=m.name, change_pct=m.change_pct)
                         for m in members]))
    return MarketOverview(
        as_of=snap.as_of, sample_data=snap.sample_data,
        indices=[quote(q) for q in snap.indices], watchlist=[quote(q) for q in snap.watchlist],
        gainers=[quote(q) for q in snap.gainers(3)], losers=[quote(q) for q in snap.losers(3)],
        sectors=sectors)


class Site:
    def __init__(self, settings: Settings, cache: TTLCache | None = None):
        self.settings = settings
        self.cache = cache or TTLCache()

    async def _call(self, name: str, **args):
        return (await call_tools(self.settings, [(name, args)]))[0]

    async def overview(self) -> MarketOverview:
        async def load() -> MarketOverview:
            return build_overview(MarketSnapshot.model_validate(await self._call(
                "get_market_snapshot")))
        return (await self.cache.get("overview", MARKET_TTL, load))[0]

    async def history(self, symbol: str, range_: HistoryRange) -> PriceHistory:
        async def load() -> PriceHistory:
            raw = await self._call("get_price_history", symbol=symbol, range=range_)
            return PriceHistory(symbol=symbol, name=SYMBOLS[symbol], range=range_,
                                points=[PricePoint.model_validate(p) for p in raw])
        return (await self.cache.get(f"history:{symbol}:{range_}", MARKET_TTL, load))[0]

    async def news(self) -> tuple[list[NewsItem], datetime]:
        async def load() -> list[NewsItem]:
            raw = await self._call("get_site_news", hours=168, limit=300)
            return [NewsItem.model_validate(r) for r in raw]
        return await self.cache.get("news", NEWS_TTL, load)

    async def feed(self, tab: Tab, limit: int) -> NewsFeed:
        items, updated = await self.news()
        return build_feed(tab, items, limit, updated)

    async def top_stories(self) -> list[TopStories]:
        items, updated = await self.news()
        feeds = [build_feed(tab, items, 3, updated) for tab in TABS]
        return [TopStories(tab=f.tab, label=f.label, items=f.items) for f in feeds]
