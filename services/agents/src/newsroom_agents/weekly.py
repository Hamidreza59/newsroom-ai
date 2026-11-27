"""Weekly "AI Innovation" feature: pick a topic, write the article, publish JSON for the site."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, date, datetime
from pathlib import Path

from newsroom_core.config import Settings
from newsroom_core.site import (
    Feature,
    FeatureSection,
    FeatureSource,
        GeneratedBy,
    GlossaryEntry,
    RelatedStory,
)

from newsroom_agents.agents.base import ToolClient, TracedTools
from newsroom_agents.agents.feature import FeatureResult, FeatureWriter
from newsroom_agents.guardrails import GuardrailLog, ScopedTools
from newsroom_agents.llm import LlmRouter
from newsroom_agents.observability import Tracer
from newsroom_agents.pipeline import mcp_client

log = logging.getLogger("newsroom_agents.weekly")

WEEK_RE = re.compile(r"^(\d{4})-W(\d{2})$")
DISCLAIMER = (
    "This article was written by an AI agent for educational purposes. It is not financial or "
    "medical advice. Facts come from the newsroom's vetted knowledge base and the linked news "
    "reports, so check the sources before relying on it."
)


def week_monday(week: str) -> date:
    m = WEEK_RE.match(week)
    if not m:
        raise ValueError(f"week must look like 2026-W48, got {week!r}")
    return date.fromisocalendar(int(m.group(1)), int(m.group(2)), 1)


def iso_week(day: date) -> str:
    year, number, _ = day.isocalendar()
    return f"{year}-W{number:02d}"


def feature_slug(week: str, key: str) -> str:
    return f"{week[:4]}-w{week[-2:]}-{key}"


def features_dir(settings: Settings) -> Path:
    return settings.out_dir / "web" / "innovation"


def read_index(directory: Path) -> list[dict]:
    path = directory / "index.json"
    return json.loads(path.read_text()) if path.exists() else []


def used_topics(directory: Path, week: str) -> set[str]:
    """Topics already published in other weeks, so rotation works without the archive."""
    return {e["slug"].split("-", 2)[2] for e in read_index(directory) if e["week"] != week}


def build_feature(week: str, monday: date, result: FeatureResult, model: str) -> Feature:
    draft, key = result.draft, result.topic["key"]
    words = sum(len(s.body.split()) for s in draft.sections)
    return Feature(
        slug=feature_slug(week, key), week=week, title=draft.title, dek=draft.dek,
        topic=result.topic["title"], reading_minutes=max(1, round(words / 200)),
        published_at=datetime.combine(monday, datetime.min.time(), UTC).replace(hour=12).isoformat(),
        sections=[FeatureSection(heading=s.heading, body=s.body) for s in draft.sections],
        takeaways=draft.takeaways,
        glossary=[GlossaryEntry(term=g.term, definition=g.definition) for g in draft.glossary],
        related=[RelatedStory(title=i.title, url=i.url, source=i.source) for i in result.related],
        sources=[FeatureSource(title=i.title, url=i.url) for i in result.sources],
        disclaimer=DISCLAIMER,
        generated_by=GeneratedBy(agent=FeatureWriter.role,
                                 model="template-fallback" if result.used_fallback else model),
    )


def publish_feature(directory: Path, feature: Feature) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    existing = read_index(directory)
    index = [e for e in existing if e["week"] != feature.week]
    for stale in (e for e in existing if e["week"] == feature.week):
        if stale["slug"] != feature.slug:
            (directory / f"{stale['slug']}.json").unlink(missing_ok=True)
    path = directory / f"{feature.slug}.json"
    path.write_text(feature.model_dump_json(by_alias=True, indent=2))
    index.append(feature.summary().model_dump(by_alias=True))
    index.sort(key=lambda e: (e["publishedAt"], e["slug"]), reverse=True)
    (directory / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))
    return path


async def produce_feature(settings: Settings, week: str, topic: str | None = None,
                          record: bool = True) -> Path:
    monday = week_monday(week)
    directory = features_dir(settings)
    guard, tracer = GuardrailLog(), Tracer()
    router = LlmRouter(settings, guard)
    anchors = settings.anchor_names
    async with mcp_client(settings) as client:
        tools = ToolClient(client, tracer)

        def scoped(role: str) -> TracedTools:
            return TracedTools(ScopedTools(tools, role, guard), tracer)

        writer = FeatureWriter(router.for_agent(FeatureWriter.role, FeatureWriter.tier),
                               scoped(FeatureWriter.role), settings.show_name, anchors, guard, tracer)
        with tracer.span("graph", "node", "feature"):
            result = await writer.run(week, monday, topic, used_topics(directory, week))
        feature = build_feature(week, monday, result, router.providers["smart"].name)
        path = publish_feature(directory, feature)
        if record and not settings.offline:
            await scoped("orchestrator").call(
                "record_segment", kind="feature", key=result.topic["key"],
                show_date=monday.isoformat(), payload={"title": feature.title, "slug": feature.slug})

    reports = directory / "reports" / feature.slug
    reports.mkdir(parents=True, exist_ok=True)
    guard.write(reports / "guardrails.json")
    tracer.write(reports)
    (reports / "run_report.json").write_text(json.dumps({
        "week": week, "topic": result.topic["key"], "slug": feature.slug,
        "model": feature.generated_by.model, "used_fallback": result.used_fallback,
        "related_stories": len(result.related),
        "llm_calls": {"used": router.calls, "budget": router.budget,
                      "circuit_breaker_open": router.open},
        "agents": router.report(), "trace": tracer.summary(),
        "guardrails": {"needs_review": guard.needs_review, "counts": guard.counts()},
    }, indent=2))
    log.info("feature ready: %s (%d min read, fallback=%s)", path, feature.reading_minutes,
             result.used_fallback)
    return path
