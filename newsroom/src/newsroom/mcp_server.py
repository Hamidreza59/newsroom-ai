"""Newsroom MCP server: market data, news wire and RAG tools for the newsroom agents."""

from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from functools import cache
from pathlib import Path

import httpx
from mcp.server.mcpserver import MCPServer

from newsroom.config import Settings
from newsroom.data.market import get_snapshot
from newsroom.data.news import fetch_article_details, get_news
from newsroom.models import ArchiveHit, CoveredStory, MarketSnapshot, NewsItem
from newsroom.rag.embedder import make_embedder
from newsroom.rag.store import VectorStore, chunk_markdown

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[mcp] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("newsroom.mcp")

STYLE_GUIDE = Path(__file__).parent / "rag" / "style_guide.md"

server = MCPServer(
    "newsroom",
    instructions=(
        "Tools for an AI newsroom producing a daily markets and AI/tech news show. Market and "
        "news tools return today's raw material; archive and style-guide tools are RAG lookups."
    ),
    version="0.1.0",
)


@cache
def settings() -> Settings:
    return Settings()


@cache
def store() -> VectorStore:
    s = settings()
    vs = VectorStore(s.db_path, make_embedder(s.embedder, s.ollama_url, s.ollama_embed_model))
    chunks = chunk_markdown(STYLE_GUIDE.read_text())
    vs.add("style", [(h, "", f"{h}: {b}", {"heading": h}) for h, b in chunks])
    return vs


@server.tool()
def get_market_snapshot() -> MarketSnapshot:
    """Latest close for the major US indices plus an AI/big-tech watchlist, with 1-month history."""
    return get_snapshot(settings().offline)


@server.tool()
def get_ai_tech_news(hours: int = 30, limit: int = 20) -> list[NewsItem]:
    """AI and technology stories from the last `hours`, de-duplicated and ranked by importance."""
    return get_news(settings().offline, hours)[:limit]


@server.tool()
def get_article_details(url: str) -> dict[str, str]:
    """Publisher name and official description of an article, read from its page metadata."""
    if settings().offline:
        return {"site_name": "", "description": ""}
    try:
        return fetch_article_details(url)
    except (httpx.HTTPError, ValueError) as exc:
        log.warning("article details failed for %s: %s", url, exc)
        return {"site_name": "", "description": ""}


@server.tool()
def search_news_archive(
    query: str, k: int = 3, days: int = 14, before: str | None = None
) -> list[ArchiveHit]:
    """Semantic search over stories covered on shows in the `days` before `before` (YYYY-MM-DD)."""
    end = date.fromisoformat(before) if before else date.today() + timedelta(days=1)
    since = (end - timedelta(days=days)).isoformat()
    return [
        ArchiveHit(id=h.id, title=h.meta.get("title", ""), date=h.date, similarity=h.similarity)
        for h in store().search("archive", query, k=k, since=since, until=end.isoformat())
    ]


@server.tool()
def search_style_guide(query: str, k: int = 3) -> list[str]:
    """Retrieve the newsroom style-guide sections most relevant to `query`."""
    return [h.text for h in store().search("style", query, k=k)]


@server.tool()
def record_coverage(show_date: str, stories: list[CoveredStory]) -> int:
    """Save the stories covered on a show so future shows can avoid repeats and spot follow-ups."""
    return store().add(
        "archive",
        [(s.id, show_date, f"{s.title}. {s.summary}", {"title": s.title, "url": s.url})
         for s in stories],
    )


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()
