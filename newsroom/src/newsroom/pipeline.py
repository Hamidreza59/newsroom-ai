from __future__ import annotations

import logging
import os
import sys
import time
from datetime import date
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from newsroom.agents.base import ToolClient
from newsroom.agents.editor import Editor
from newsroom.agents.market_analyst import MarketAnalyst
from newsroom.agents.news_scout import NewsScout
from newsroom.agents.producer import Producer, TooLong
from newsroom.agents.scriptwriter import Scriptwriter
from newsroom.config import Settings
from newsroom.llm import make_llm
from newsroom.models import CoveredStory, Episode, MarketSnapshot, NewsItem
from newsroom.tts import make_tts

log = logging.getLogger("newsroom.pipeline")
MAX_REVISIONS = 2


def server_params(settings: Settings) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "newsroom.mcp_server"],
        env={**os.environ, **settings.server_env()},
    )


async def produce_episode(settings: Settings, show_date: date, record: bool = True) -> Path:
    started = time.monotonic()
    llm = make_llm(settings)
    tts = make_tts(settings)
    log.info("LLM=%s  TTS=%s  offline=%s", llm.name, tts.name, settings.offline)
    out_dir = settings.out_dir / show_date.isoformat()

    async with Client(server_params(settings), read_timeout_seconds=120) as client:
        tools = ToolClient(client)
        anchors = settings.anchor_names
        analyst = MarketAnalyst(llm, tools, settings.show_name, anchors)
        scout = NewsScout(llm, tools, settings.show_name, anchors)
        writer = Scriptwriter(llm, tools, settings.show_name, anchors)
        editor = Editor(list(anchors.values()), settings.show_name)
        producer = Producer(settings, tts)

        snap = MarketSnapshot.model_validate(await tools.call("get_market_snapshot"))
        log.info("market snapshot as of %s (sample=%s)", snap.as_of, snap.sample_data)

        items: list[NewsItem] = await scout.run(settings.stories_per_show, show_date.isoformat())
        brief = await analyst.run(snap)
        script = await writer.run(brief, items, show_date)

        materials = {i.id: f"{i.title}. {i.summary}" for i in items}
        for round_no in range(1, MAX_REVISIONS + 1):
            review = editor.review(script, snap, materials)
            if review.clean:
                break
            log.info("revision round %d", round_no)
            if review.market:
                brief = await analyst.run(snap, feedback="\n".join(review.market))
            stories = []
            for i, (item, seg) in enumerate(zip(items, script.stories, strict=True)):
                issues = review.stories.get(seg.story_id)
                stories.append(
                    await writer.write_story(item, i, "\n".join(issues)) if issues else seg)
            script = script.model_copy(update={"market": brief, "stories": stories})

        review = editor.review(script, snap, materials)
        if review.market:
            log.warning("market copy still failing checks; using fact-sheet template")
            script = script.model_copy(update={"market": analyst.fallback(snap)})
        stories = []
        for i, (item, seg) in enumerate(zip(items, script.stories, strict=True)):
            if any(x.startswith("remove") for x in review.stories.get(seg.story_id, [])):
                log.warning("story '%s' still failing checks; using source-only copy", seg.headline)
                seg = writer.segment(item, writer.fallback_story(item, i))
            stories.append(seg)
        script = editor.enforce(script.model_copy(update={"stories": stories}))

        while True:
            try:
                episode: Episode = producer.build(script, snap, show_date)
                break
            except TooLong as exc:
                if len(script.stories) <= 2:
                    raise
                dropped = script.stories[-1]
                log.info("%s; dropping story '%s'", exc, dropped.headline)
                script = script.model_copy(update={"stories": script.stories[:-1]})
                bookends = await writer.write_bookends(script.market, script.stories, show_date)
                script = script.model_copy(update={"intro": bookends.intro,
                                                   "outro": bookends.outro})

        producer.write(episode, script, out_dir)
        if record and not settings.offline:
            by_id = {i.id: i for i in items}
            await tools.call("record_coverage", show_date=show_date.isoformat(), stories=[
                CoveredStory(id=s.story_id, title=by_id[s.story_id].title,
                             summary=by_id[s.story_id].summary, url=s.url).model_dump()
                for s in script.stories
            ])

    log.info("episode ready: %s (%.1fs of video, %d stories) in %.0fs",
             out_dir, episode.duration_in_frames / episode.fps, len(script.stories),
             time.monotonic() - started)
    return out_dir
