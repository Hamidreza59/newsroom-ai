import itertools
import json
from datetime import date

import numpy as np
import pytest
from mcp import Client

from newsroom.agents.producer import mouth_envelope
from newsroom.config import Settings
from newsroom.pipeline import produce_episode


@pytest.fixture
def offline_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWSROOM_OFFLINE", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    settings = Settings()
    settings.offline = True
    settings.llm_provider = "mock"
    settings.tts_provider = "silent"
    settings.out_dir = tmp_path / "out"
    settings.data_dir = tmp_path / "data"
    return settings


async def test_mcp_server_tools_in_process(offline_settings):
    from newsroom import mcp_server

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


async def test_offline_episode_end_to_end(offline_settings):
    out = await produce_episode(offline_settings, date(2026, 11, 23), record=False)
    episode = json.loads((out / "episode.json").read_text())

    assert episode["durationInFrames"] / episode["fps"] <= offline_settings.max_seconds
    scenes = episode["scenes"]
    types = [s["type"] for s in scenes]
    assert types[:3] == ["coldopen", "intro", "market"] and types[-2:] == ["quiz", "outro"]
    assert "explainer" in types
    for prev, nxt in itertools.pairwise(scenes):
        assert prev["startFrame"] + prev["durationInFrames"] == nxt["startFrame"]
    assert all(c["endFrame"] <= episode["durationInFrames"] for c in episode["captions"])
    assert "not financial advice" in scenes[-1]["narration"]
    assert {c["speaker"] for c in episode["captions"]} == {"a", "b"}
    assert [a["name"] for a in episode["anchors"]] == ["Maya", "Leo"]
    assert episode["short"]["durationInFrames"] <= 58 * episode["fps"]

    report = json.loads((out / "run_report.json").read_text())
    assert report["models"] == {"fast": "mock", "smart": "mock"}
    assert {"market", "scout", "editor", "produce", "publish"} <= {
        s["name"] for s in map(json.loads, (out / "trace.jsonl").read_text().splitlines())}
    assert json.loads((out / "guardrails.json").read_text())["needs_review"] is False


    yt = json.loads((out / "youtube.json").read_text())
    assert "0:00 Intro" in yt["description"] and len(yt["title"]) <= 100
    assert (out / "captions.srt").read_text().startswith("1\n00:00:")


def test_mouth_envelope_tracks_loudness():
    rate, fps = 24000, 30
    audio = np.concatenate([np.zeros(rate), 0.3 * np.sin(np.linspace(0, 2000, rate))])
    env = mouth_envelope(audio.astype(np.float32), rate, fps, 2 * fps)
    assert len(env) == 2 * fps
    assert max(env[:fps]) == 0 and max(env[fps:]) > 0.5


def test_graph_shape():
    from newsroom.pipeline import mermaid

    graph = mermaid()
    for edge in ("market --> scout", "market --> analyst", "writer --> quiz", "editor -.-> revise",
                 "revise --> editor", "produce --> review_gate"):
        assert edge in graph
