"""FastAPI app: JSON under /api and whitelisted episode media under /media."""

from __future__ import annotations

import logging
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException, Path, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from newsroom_core.config import Settings
from newsroom_core.site import (
    EpisodeDetail,
    EpisodeSummary,
    Feature,
    FeatureSummary,
    Health,
    HistoryRange,
    Home,
    MarketOverview,
    NewsFeed,
    PriceHistory,
    Tab,
)

from newsroom_api import content
from newsroom_api.service import SYMBOLS, Site

log = logging.getLogger("newsroom_api")
DATE = Path(pattern=content.DATE_RE.pattern)
SLUG = Path(pattern=content.SLUG_RE.pattern)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    site = Site(settings)
    app = FastAPI(title="Newsroom site API", version="0.2.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=[o.strip() for o in settings.web_origin.split(",") if o.strip()],
        allow_methods=["GET"], allow_headers=["*"])

    @app.exception_handler(Exception)
    async def upstream_error(request: Request, exc: Exception) -> JSONResponse:
        log.exception("request failed: %s", request.url.path)
        return JSONResponse({"detail": "upstream data unavailable"}, status_code=503)

    @app.get("/api/health", response_model=Health)
    async def health() -> Health:
        return Health(status="ok", offline=settings.offline)

    @app.get("/api/markets/overview", response_model=MarketOverview)
    async def markets_overview() -> MarketOverview:
        return await site.overview()

    @app.get("/api/markets/history/{symbol}", response_model=PriceHistory)
    async def markets_history(
        symbol: str, range_: Annotated[HistoryRange, Query(alias="range")] = "6mo",
    ) -> PriceHistory:
        symbol = symbol.upper()
        if symbol not in SYMBOLS:
            raise HTTPException(404, f"unknown symbol {symbol}")
        return await site.history(symbol, range_)

    @app.get("/api/news", response_model=NewsFeed)
    async def news(tab: Tab = "ai", limit: Annotated[int, Query(ge=1, le=100)] = 40) -> NewsFeed:
        return await site.feed(tab, limit)

    @app.get("/api/home", response_model=Home)
    async def home() -> Home:
        episodes, features = content.list_episodes(settings), content.list_features(settings)
        return Home(
            latest_episode=episodes[0] if episodes else None,
            markets=await site.overview(),
            top_stories=await site.top_stories(),
            feature=features[0] if features else None)

    @app.get("/api/episodes", response_model=list[EpisodeSummary])
    async def episodes() -> list[EpisodeSummary]:
        return content.list_episodes(settings)

    @app.get("/api/episodes/{day}", response_model=EpisodeDetail)
    async def episode(day: Annotated[str, DATE]) -> EpisodeDetail:
        if not (detail := content.get_episode(settings, day)):
            raise HTTPException(404, f"no episode for {day}")
        return detail

    @app.get("/api/innovation", response_model=list[FeatureSummary])
    async def innovation() -> list[FeatureSummary]:
        return content.list_features(settings)

    @app.get("/api/innovation/{slug}", response_model=Feature)
    async def innovation_feature(slug: Annotated[str, SLUG]) -> Feature:
        if not (feature := content.get_feature(settings, slug)):
            raise HTTPException(404, f"no feature {slug}")
        return feature

    @app.get("/media/{day}/{name}")
    async def media(day: str, name: str) -> FileResponse:
        if not (path := content.media_path(settings, day, name)):
            raise HTTPException(404, "not found")
        return FileResponse(path, media_type=content.MEDIA_FILES[name])

    return app


def main() -> None:
    settings = Settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)-22s %(message)s",
                        datefmt="%H:%M:%S")
    uvicorn.run(create_app(settings), host=settings.api_host, port=settings.api_port)


if __name__ == "__main__":
    main()
