from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PricePoint(BaseModel):
    date: str
    close: float


class Quote(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    series: list[PricePoint] = Field(default_factory=list)


class MarketSnapshot(BaseModel):
    as_of: str
    indices: list[Quote]
    watchlist: list[Quote]
    sample_data: bool = False

    def gainers(self, n: int = 3) -> list[Quote]:
        return [q for q in sorted(self.watchlist, key=lambda q: -q.change_pct) if q.change_pct > 0][:n]

    def losers(self, n: int = 3) -> list[Quote]:
        return [q for q in sorted(self.watchlist, key=lambda q: q.change_pct) if q.change_pct < 0][:n]


Category = Literal["AI", "Tech"]


class NewsItem(BaseModel):
    id: str
    title: str
    url: str
    source: str
    published: str
    summary: str = ""
    score: float = 0.0
    category: Category = "Tech"
    coverage: int = 1
    follow_up: bool = False


class ArchiveHit(BaseModel):
    id: str
    title: str
    date: str
    similarity: float


class CoveredStory(BaseModel):
    id: str
    title: str
    summary: str
    url: str


# ---- agent outputs ---------------------------------------------------------


Speaker = Literal["a", "b"]


class Line(BaseModel):
    speaker: Speaker = Field(description='"a" or "b", the anchor speaking this line')
    text: str = Field(description="What the anchor says")


def spoken(lines: list[Line]) -> str:
    return " ".join(line.text.strip() for line in lines)


class MarketBrief(BaseModel):
    headline: str = Field(description="On-screen market headline, max 50 characters")
    lines: list[Line] = Field(description="The anchors' dialogue for the market segment")
    bullets: list[str] = Field(description="Exactly 3 short on-screen takeaways, max 60 chars each")

    @property
    def narration(self) -> str:
        return spoken(self.lines)


class StoryPicks(BaseModel):
    ids: list[str] = Field(description="Chosen story ids, most important first")


class StoryCopy(BaseModel):
    headline: str = Field(description="On-screen headline, max 55 characters")
    points: list[str] = Field(description="Exactly 3 on-screen key points, max 70 chars each")
    lines: list[Line] = Field(description="The anchors' dialogue for this story")


class BookendCopy(BaseModel):
    intro: list[Line] = Field(description="Opening dialogue")
    outro: list[Line] = Field(description="Sign-off dialogue, before the disclaimer")


class NewsSegment(BaseModel):
    story_id: str
    headline: str
    points: list[str]
    lines: list[Line]
    source: str
    url: str
    category: Category
    follow_up: bool = False

    @property
    def narration(self) -> str:
        return spoken(self.lines)


class ShowScript(BaseModel):
    intro: list[Line]
    market: MarketBrief
    stories: list[NewsSegment]
    outro: list[Line]

    def word_count(self) -> int:
        parts = [spoken(self.intro), self.market.narration, spoken(self.outro),
                 *(s.narration for s in self.stories)]
        return sum(len(p.split()) for p in parts)


# ---- episode contract consumed by the Remotion studio (camelCase JSON) -----


class _Camel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EpQuote(_Camel):
    symbol: str
    name: str
    price: float
    change: float
    change_pct: float
    series: list[PricePoint] = Field(default_factory=list)


class EpMarket(_Camel):
    as_of: str
    indices: list[EpQuote]
    gainers: list[EpQuote]
    losers: list[EpQuote]
    sample_data: bool = False


class Caption(_Camel):
    text: str
    speaker: Speaker
    start_frame: int
    end_frame: int


class Anchor(_Camel):
    id: Speaker
    name: str


SceneType = Literal["intro", "market", "news", "outro"]


class Scene(_Camel):
    type: SceneType
    start_frame: int
    duration_in_frames: int
    narration: str
    headline: str = ""
    bullets: list[str] = Field(default_factory=list)
    source: str = ""
    category: Category | None = None
    follow_up: bool = False
    index: int = 0
    total: int = 0
    alert: str = ""
    alert_frames: int = 0


class YouTubeMeta(_Camel):
    title: str
    description: str
    tags: list[str]


class Episode(_Camel):
    date: str
    show_name: str
    fps: int
    width: int = 1920
    height: int = 1080
    duration_in_frames: int
    audio_file: str | None
    market: EpMarket
    ticker: list[EpQuote]
    scenes: list[Scene]
    captions: list[Caption]
    youtube: YouTubeMeta
    disclaimer: str
    anchors: list[Anchor]
    mouths: dict[str, list[float]] = Field(default_factory=dict)
