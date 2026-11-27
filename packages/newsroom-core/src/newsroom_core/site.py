"""Response models for the website API and the weekly feature (camelCase JSON)."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from newsroom_core.models import PricePoint, _Camel

Tab = Literal["markets", "ai", "ai-finance", "tech", "biotech"]
HistoryRange = Literal["1mo", "6mo", "1y"]

TAB_LABELS: dict[str, str] = {
    "markets": "Markets",
    "ai": "AI",
    "ai-finance": "AI in Finance",
    "tech": "Tech",
    "biotech": "Biotech",
}


class Health(_Camel):
    status: str
    offline: bool


class Quote(_Camel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    series: list[PricePoint] = Field(default_factory=list)


class SectorMember(_Camel):
    symbol: str
    name: str
    change_pct: float


class Sector(_Camel):
    name: str
    change_pct: float
    members: list[SectorMember]


class MarketOverview(_Camel):
    as_of: str
    sample_data: bool
    indices: list[Quote]
    watchlist: list[Quote]
    gainers: list[Quote]
    losers: list[Quote]
    sectors: list[Sector]


class PriceHistory(_Camel):
    symbol: str
    name: str
    range: HistoryRange
    points: list[PricePoint]


class SiteNewsItem(_Camel):
    id: str
    title: str
    url: str
    source: str
    published: str
    summary: str
    category: str
    tags: list[str]
    score: float


class VolumePoint(_Camel):
    date: str
    count: int


class SourceCount(_Camel):
    source: str
    count: int


class KeywordCount(_Camel):
    term: str
    count: int


class NewsFeed(_Camel):
    tab: Tab
    label: str
    updated_at: str
    items: list[SiteNewsItem]
    volume: list[VolumePoint]
    top_sources: list[SourceCount]
    keywords: list[KeywordCount]


class TopStories(_Camel):
    tab: Tab
    label: str
    items: list[SiteNewsItem]


class EpisodeSummary(_Camel):
    date: str
    title: str
    summary: str
    duration_seconds: int | None
    story_count: int
    thumbnail_url: str | None
    video_url: str | None
    short_url: str | None


class Chapter(_Camel):
    time: str
    title: str


class EpisodeSource(_Camel):
    title: str
    publisher: str
    url: str


class EpisodeQuiz(_Camel):
    question: str
    options: list[str]
    reveal: str = ""
    answer: str | None = None


class EpisodeDetail(EpisodeSummary):
    show: str
    tags: list[str]
    disclaimer: str
    chapters: list[Chapter]
    sources: list[EpisodeSource]
    quiz: EpisodeQuiz | None
    script_markdown: str | None


class FeatureSummary(_Camel):
    slug: str
    week: str
    title: str
    dek: str
    topic: str
    reading_minutes: int
    published_at: str


class FeatureSection(_Camel):
    heading: str
    body: str


class GlossaryEntry(_Camel):
    term: str
    definition: str


class RelatedStory(_Camel):
    title: str
    url: str
    source: str


class FeatureSource(_Camel):
    title: str
    url: str


class GeneratedBy(_Camel):
    agent: str
    model: str


class Feature(FeatureSummary):
    sections: list[FeatureSection]
    takeaways: list[str]
    glossary: list[GlossaryEntry]
    related: list[RelatedStory]
    sources: list[FeatureSource]
    disclaimer: str
    generated_by: GeneratedBy

    def summary(self) -> FeatureSummary:
        return FeatureSummary(**{k: getattr(self, k) for k in FeatureSummary.model_fields})


class Home(_Camel):
    latest_episode: EpisodeSummary | None
    markets: MarketOverview
    top_stories: list[TopStories]
    feature: FeatureSummary | None


SITE_MODELS = [
    Health, Quote, Sector, MarketOverview, PriceHistory, SiteNewsItem, NewsFeed, TopStories,
    EpisodeSummary, EpisodeDetail, FeatureSummary, Feature, Home,
]
