import json
import re
from datetime import date
from pathlib import Path

import newsroom_mcp
import pytest
from newsroom_agents.agents.editor import check_text_grounding
from newsroom_agents.agents.feature import FeatureDraft, FeatureWriter
from newsroom_agents.guardrails import GuardrailLog, ScopedTools, ToolDenied
from newsroom_agents.llm import MockProvider
from newsroom_agents.weekly import produce_feature, week_monday
from newsroom_core.config import Settings
from newsroom_core.site import Feature
from newsroom_mcp.data.news import sample_site_news
from newsroom_mcp.rag.store import chunk_markdown

EXPLAINERS = Path(newsroom_mcp.__file__).parent / "rag" / "explainers.md"
KB = [
    {"key": k.partition("|")[0].strip(), "title": k.partition("|")[2].strip(),
     "text": " ".join(re.sub(r"^Track:.*$", "", t, flags=re.MULTILINE).split()),
     "tracks": [x.strip() for x in re.search(r"^Track:\s*(.+)$", t, re.MULTILINE)[1].split(",")]}
    for k, t in chunk_markdown(EXPLAINERS.read_text()) if k
]
AI_KEYS = {e["key"] for e in KB if "ai" in e["tracks"]}


class FakeTools:
    def __init__(self, recent=None):
        self.recent = recent or []

    async def call(self, name, **kw):
        if name == "search_explainers":
            track = kw.get("track")
            return [e | {"similarity": 0.5} for e in KB if not track or track in e["tracks"]]
        if name == "get_site_news":
            return [i.model_dump() for i in sample_site_news()]
        if name == "recent_segments":
            return self.recent
        raise AssertionError(name)


class ScriptedLlm:
    name = "scripted"

    def __init__(self, drafts):
        self.drafts = list(drafts)

    async def generate_json(self, system, user, schema):
        return self.drafts.pop(0)


def writer(llm=None, recent=None):
    return FeatureWriter(llm or MockProvider(), FakeTools(recent), "Bits & Bulls")


async def test_mock_feature_is_complete_and_grounded():
    w = writer()
    result = await w.run("2026-W48", date(2026, 11, 23))
    draft = result.draft
    assert result.used_fallback and len(draft.sections) >= 4 and 3 <= len(draft.takeaways) <= 5
    material = w.material(result.topic, result.sources)
    assert check_text_grounding(draft.text(), material, draft.title) == []
    assert w.check(draft, material, strict=False) == []


async def test_topic_rotation_skips_recent_and_local_topics():
    first = (await writer().run("2026-W48", date(2026, 11, 23))).topic["key"]
    again = (await writer(recent=[{"key": first}]).run("2026-W48", date(2026, 11, 23))).topic["key"]
    third = (await writer().run("2026-W48", date(2026, 11, 23), local_used={first, again})
             ).topic["key"]
    assert len({first, again, third}) == 3
    assert {first, again, third} <= AI_KEYS


async def test_rotation_only_picks_ai_topics():
    used: set[str] = set()
    for _ in range(len(AI_KEYS)):
        key = (await writer().run("2026-W48", date(2026, 11, 23), local_used=used)).topic["key"]
        assert key in AI_KEYS
        used.add(key)
    assert used == AI_KEYS


async def test_explicit_topic_override_and_unknown_topic():
    assert (await writer().run("2026-W48", date(2026, 11, 23), topic="rag")).topic["key"] == "rag"
    for bad in ("nope", "earnings", "crispr"):
        with pytest.raises(ValueError, match="not an AI topic"):
            await writer().run("2026-W48", date(2026, 11, 23), topic=bad)


def _long_draft(entry, extra=""):
    body = " ".join([entry["text"].partition("Keywords:")[0]] * 2) + extra
    return FeatureDraft(
        title=entry["title"], dek="A plain explainer.",
        sections=[{"heading": f"Part {i}", "body": body} for i in range(4)],
        takeaways=["One.", "Two.", "Three."],
        glossary=[{"term": "Term", "definition": "A definition."}])


async def test_grounded_llm_draft_is_accepted_and_ungrounded_falls_back():
    entry = next(e for e in KB if e["key"] == "rag")
    ok = await writer(ScriptedLlm([_long_draft(entry)])).run(
        "2026-W48", date(2026, 11, 23), topic="rag")
    assert not ok.used_fallback
    bad_llm = ScriptedLlm([_long_draft(entry, " Zorblax Corp raised 4,242 widgets."),
                           _long_draft(entry, " Zorblax Corp raised 4,242 widgets.")])
    w = writer(bad_llm)
    bad = await w.run("2026-W48", date(2026, 11, 23), topic="rag")
    assert bad.used_fallback and "Zorblax" not in bad.draft.text()
    assert w.guard.counts()["output.feature_fallback"] == 1


async def test_feature_writer_tool_policy():
    tools = ScopedTools(FakeTools(), "feature-writer", GuardrailLog())
    assert await tools.call("get_site_news")
    with pytest.raises(ToolDenied):
        await tools.call("record_segment")


async def test_weekly_cli_flow_writes_feature_and_index(tmp_path, monkeypatch):
    monkeypatch.setenv("NEWSROOM_OFFLINE", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    settings = Settings()
    settings.offline, settings.llm_provider = True, "mock"
    settings.out_dir, settings.data_dir = tmp_path / "out", tmp_path / "data"
    first = await produce_feature(settings, "2026-W47", record=False)
    second = await produce_feature(settings, "2026-W48", record=False)
    feature = Feature.model_validate_json(second.read_text())
    assert len(feature.sections) >= 4 and feature.generated_by.agent == "feature-writer"
    assert feature.slug == f"2026-w48-{feature.slug.split('-', 2)[2]}" and "advice" in feature.disclaimer
    index = json.loads((second.parent / "index.json").read_text())
    assert [e["week"] for e in index] == ["2026-W48", "2026-W47"]
    assert first.stem.split("-", 2)[2] != second.stem.split("-", 2)[2]
    assert (second.parent / "reports" / feature.slug / "guardrails.json").exists()
    await produce_feature(settings, "2026-W48", record=False)
    assert len(json.loads((second.parent / "index.json").read_text())) == 2


def test_week_monday():
    assert week_monday("2026-W48") == date(2026, 11, 23)
    with pytest.raises(ValueError):
        week_monday("2026-48")
