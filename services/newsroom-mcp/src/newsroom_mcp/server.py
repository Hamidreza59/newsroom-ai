"""Newsroom MCP server: market data, news wire and RAG tools for the newsroom agents."""

from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
from datetime import date, timedelta
from functools import cache
from pathlib import Path

import httpx
from mcp.server.mcpserver import MCPServer
from newsroom_core.config import Settings
from newsroom_core.models import ArchiveHit, CoveredStory, MarketSnapshot, NewsItem

from newsroom_mcp.data.market import get_snapshot
from newsroom_mcp.data.news import fetch_article_details, get_news
from newsroom_mcp.rag.embedder import make_embedder
from newsroom_mcp.rag.store import SegmentLog, VectorStore, chunk_markdown

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="[mcp] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("newsroom.mcp")

STYLE_GUIDE = Path(__file__).parent / "rag" / "style_guide.md"
EXPLAINERS = Path(__file__).parent / "rag" / "explainers.md"

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


_init_lock = threading.Lock()


@cache
def _store() -> VectorStore:
    s = settings()
    vs = VectorStore(s.db_path, make_embedder(s.embedder, s.ollama_url, s.ollama_embed_model))
    chunks = chunk_markdown(STYLE_GUIDE.read_text())
    vs.add("style", [(h, "", f"{h}: {b}", {"heading": h}) for h, b in chunks])
    entries = []
    for heading, text in chunk_markdown(EXPLAINERS.read_text()):
        key, _, title = (part.strip() for part in heading.partition("|"))
        text = " ".join(text.split())
        entries.append((key, "", f"{title}. {text}", {"key": key, "title": title, "text": text}))
    vs.add("explainers", entries)
    return vs


def store() -> VectorStore:
    with _init_lock:
        return _store()


@cache
def segments() -> SegmentLog:
    return SegmentLog(store())


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


@server.tool()
def search_explainers(query: str, k: int = 3) -> list[dict]:
    """Curated explainer entries (key, title, vetted text) most relevant to `query`."""
    return [h.meta | {"similarity": round(h.similarity, 3)}
            for h in store().search("explainers", query, k=k)]


@server.tool()
def record_segment(kind: str, key: str, show_date: str, payload: dict) -> bool:
    """Remember a recurring segment (e.g. kind="explainer" or "quiz") used on a show."""
    segments().record(kind, key, show_date, payload)
    return True


@server.tool()
def recent_segments(kind: str, before: str, days: int = 14) -> list[dict]:
    """Segments of `kind` recorded in the `days` before `before` (YYYY-MM-DD), newest first."""
    end = date.fromisoformat(before)
    return segments().recent(kind, (end - timedelta(days=days)).isoformat(), end.isoformat())


def main() -> None:
    parser = argparse.ArgumentParser(prog="newsroom-mcp", description=__doc__)
    parser.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    parser.add_argument("--host", default=os.environ.get("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("MCP_PORT", "8765")))
    args = parser.parse_args()
    if args.transport == "http":
        log.info("serving MCP over streamable HTTP on http://%s:%d/mcp", args.host, args.port)
        server.run(transport="streamable-http", host=args.host, port=args.port,
                   streamable_http_path="/mcp")
    else:
        server.run()


if __name__ == "__main__":
    main()
