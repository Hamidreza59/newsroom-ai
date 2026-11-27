"""Published content on disk: episodes (out/<date>/web) and weekly features (out/web/innovation)."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

from newsroom_core.config import Settings
from newsroom_core.site import (
    EpisodeDetail,
    EpisodeSummary,
    Feature,
    FeatureSummary,
)
from pydantic import ValidationError

log = logging.getLogger("newsroom_api.content")

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,100}$")
MEDIA_FILES = {"video.mp4": "video/mp4", "short.mp4": "video/mp4", "thumbnail.png": "image/png"}


def _read_json(path: Path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        log.warning("cannot read %s: %s", path, exc)
        return None


def media_path(settings: Settings, day: str, name: str) -> Path | None:
    if not DATE_RE.match(day) or name not in MEDIA_FILES:
        return None
    path = settings.out_dir / day / name
    return path if path.is_file() else None


def _media_url(settings: Settings, day: str, name: str) -> str | None:
    return f"/media/{day}/{name}" if media_path(settings, day, name) else None


def episode_dates(settings: Settings) -> list[str]:
    index = settings.out_dir / "web" / "index.json"
    dates = [e.get("date", "") for e in _read_json(index) or []] if index.exists() else []
    if not dates and settings.out_dir.is_dir():
        dates = [p.name for p in settings.out_dir.iterdir() if (p / "web" / "post.json").exists()]
    return sorted({d for d in dates if DATE_RE.match(d)}, reverse=True)


def _summary_fields(settings: Settings, day: str, post: dict) -> dict:
    episode = _read_json(settings.out_dir / day / "episode.json") or {}
    scenes = episode.get("scenes", [])
    frames, fps = episode.get("durationInFrames"), episode.get("fps")
    stories = sum(1 for s in scenes if s.get("type") == "news") or len(post.get("sources", []))
    return {
        "date": day, "title": post.get("title", ""), "summary": post.get("summary", ""),
        "duration_seconds": round(frames / fps) if frames and fps else None,
        "story_count": stories,
        "thumbnail_url": _media_url(settings, day, "thumbnail.png"),
        "video_url": _media_url(settings, day, "video.mp4"),
        "short_url": _media_url(settings, day, "short.mp4"),
    }


def _post(settings: Settings, day: str) -> dict | None:
    if not DATE_RE.match(day):
        return None
    path = settings.out_dir / day / "web" / "post.json"
    return _read_json(path) if path.exists() else None


def list_episodes(settings: Settings) -> list[EpisodeSummary]:
    out = []
    for day in episode_dates(settings):
        if post := _post(settings, day):
            out.append(EpisodeSummary(**_summary_fields(settings, day, post)))
    return out


def get_episode(settings: Settings, day: str) -> EpisodeDetail | None:
    post = _post(settings, day)
    if post is None:
        return None
    script = settings.out_dir / day / "script.md"
    return EpisodeDetail(
        **_summary_fields(settings, day, post),
        show=post.get("show", settings.show_name),
        tags=post.get("tags", []),
        disclaimer=post.get("disclaimer", ""),
        chapters=post.get("chapters", []),
        sources=post.get("sources", []),
        quiz=post.get("quiz"),
        script_markdown=script.read_text() if script.exists() else None,
    )


def features_dir(settings: Settings) -> Path:
    return settings.out_dir / "web" / "innovation"


def _feature(path: Path) -> Feature | None:
    if not path.is_file():
        return None
    try:
        return Feature.model_validate_json(path.read_text())
    except (OSError, ValidationError) as exc:
        log.warning("invalid feature %s: %s", path, exc)
        return None


def list_features(settings: Settings) -> list[FeatureSummary]:
    directory = features_dir(settings)
    index = directory / "index.json"
    entries = _read_json(index) if index.exists() else None
    if entries is not None:
        try:
            summaries = [FeatureSummary.model_validate(e) for e in entries]
        except ValidationError as exc:
            log.warning("invalid feature index: %s", exc)
            summaries = []
    else:
        found = (_feature(p) for p in directory.glob("*.json")) if directory.is_dir() else []
        summaries = [f.summary() for f in found if f]
    return sorted(summaries, key=lambda s: (s.published_at, s.slug), reverse=True)


def get_feature(settings: Settings, slug: str) -> Feature | None:
    if not SLUG_RE.match(slug) or slug == "index":
        return None
    return _feature(features_dir(settings) / f"{slug}.json")
