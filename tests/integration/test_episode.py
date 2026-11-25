import argparse
import asyncio
import itertools
import json
import os
import socket
import subprocess
import sys
import time
from datetime import date

import pytest
from mcp import Client
from newsroom_agents.estimate import estimate_seconds
from newsroom_agents.pipeline import produce_episode
from newsroom_core.config import Settings
from newsroom_core.models import ShowPackage
from newsroom_publisher import cli as publisher
from newsroom_voice import cli as voice


@pytest.fixture
def offline_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWSROOM_OFFLINE", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("OUT_DIR", str(tmp_path / "out"))
    settings = Settings()
    settings.offline = True
    settings.llm_provider = "mock"
    settings.out_dir = tmp_path / "out"
    settings.data_dir = tmp_path / "data"
    return settings


async def test_mcp_server_tools_in_process(offline_settings):
    from newsroom_mcp import server as mcp_server

    mcp_server.settings.cache_clear()
    mcp_server._store.cache_clear()
    mcp_server.segments.cache_clear()
    async with Client(mcp_server.server) as client:
        names = {t.name for t in (await client.list_tools()).tools}
        assert {"get_market_snapshot", "get_ai_tech_news", "search_news_archive",
                "search_style_guide", "record_coverage", "get_article_details",
                "search_explainers", "record_segment", "recent_segments"} <= names
        result = await client.call_tool("search_style_guide", {"query": "percent", "k": 1})
        assert "percent" in json.dumps(result.structured_content).lower()


async def test_offline_pipeline_end_to_end(offline_settings):
    day = date(2026, 11, 23)
    out = await produce_episode(offline_settings, day, record=False)

    pkg = ShowPackage.model_validate_json((out / "package.json").read_text())
    assert pkg.approved and not pkg.needs_review
    assert pkg.estimated_seconds <= offline_settings.max_seconds
    assert (out / "script.md").read_text().startswith("# ")

    voice.cmd_build(argparse.Namespace(date=day.isoformat(), tts="silent"))
    episode = json.loads((out / "episode.json").read_text())

    assert episode["durationInFrames"] / episode["fps"] <= offline_settings.max_seconds
    scenes = episode["scenes"]
    types = [s["type"] for s in scenes]
    assert types[:3] == ["coldopen", "intro", "market"] and types[-2:] == ["quiz", "outro"]
    assert "explainer" in types
    for prev, nxt in itertools.pairwise(scenes):
        assert prev["startFrame"] + prev["durationInFrames"] == nxt["startFrame"]
    assert all(c["endFrame"] <= episode["durationInFrames"] for c in episode["captions"])
    assert "not financial or medical advice" in scenes[-1]["narration"]
    assert {c["speaker"] for c in episode["captions"]} == {"a", "b"}
    assert [a["name"] for a in episode["anchors"]] == ["Maya", "Leo"]
    assert episode["short"]["durationInFrames"] <= 58 * episode["fps"]

    report = json.loads((out / "run_report.json").read_text())
    assert report["models"] == {"fast": "mock", "smart": "mock"}
    assert {"market", "scout", "editor", "package", "publish"} <= {
        s["name"] for s in map(json.loads, (out / "trace.jsonl").read_text().splitlines())}
    assert json.loads((out / "guardrails.json").read_text())["needs_review"] is False
    yt = json.loads((out / "youtube.json").read_text())
    assert "0:00 Intro" in yt["description"] and len(yt["title"]) <= 100
    assert (out / "captions.srt").read_text().startswith("1\n00:00:")

    publisher.cmd_build(argparse.Namespace(date=day.isoformat()))
    post = json.loads((out / "web" / "post.json").read_text())
    assert post["sources"] and all(s["url"].startswith("http") for s in post["sources"])
    assert post["quiz"]["answer"] and post["chapters"][0]["title"] == "Intro"
    assert (out / "web" / "post.md").read_text().startswith("# ")
    feed = json.loads((offline_settings.out_dir / "web" / "index.json").read_text())
    assert [e["date"] for e in feed] == ["2026-11-23"]


def test_voice_refuses_unapproved_package(offline_settings):
    out = offline_settings.out_dir / "2026-11-23"
    out.mkdir(parents=True)
    pkg = ShowPackage.model_validate_json(_package_json())
    (out / "package.json").write_text(pkg.model_copy(update={"approved": False}).model_dump_json())
    with pytest.raises(SystemExit, match="not approved"):
        voice.cmd_build(argparse.Namespace(date="2026-11-23", tts="silent"))


def _package_json() -> str:
    from newsroom_core.models import MarketBrief, MarketSnapshot, ShowScript

    line = {"speaker": "a", "text": "Hello there."}
    script = ShowScript(intro=[line], market=MarketBrief(headline="h", lines=[line], bullets=[]),
                        stories=[], outro=[line])
    snap = MarketSnapshot(as_of="2026-11-23", indices=[], watchlist=[])
    return ShowPackage(date="2026-11-23", script=script, snapshot=snap,
                       estimated_seconds=1.0).model_dump_json()


def test_estimate_seconds_grows_with_content():
    script = ShowPackage.model_validate_json(_package_json()).script
    longer = script.model_copy(update={"intro": script.intro * 5})
    longer_outro = script.model_copy(update={"outro": script.outro + script.outro})
    assert estimate_seconds(script) < estimate_seconds(longer_outro) < estimate_seconds(longer)
    assert estimate_seconds(script) == estimate_seconds(script)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def test_mcp_over_http(offline_settings):
    port = _free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "newsroom_mcp.server", "--transport", "http", "--port", str(port)],
        env={**os.environ, **offline_settings.server_env()},
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    async def list_tools() -> set[str]:
        async with Client(f"http://127.0.0.1:{port}/mcp") as client:
            return {t.name for t in (await client.list_tools()).tools}

    try:
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            time.sleep(0.2)
        assert "get_market_snapshot" in asyncio.run(list_tools())
    finally:
        proc.terminate()
        proc.wait(timeout=10)
