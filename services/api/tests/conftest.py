import json

import pytest
from fastapi.testclient import TestClient
from newsroom_api.app import create_app
from newsroom_core.config import Settings
from newsroom_core.site import (
    Feature,
    FeatureSection,
    FeatureSource,
    GeneratedBy,
    GlossaryEntry,
    RelatedStory,
)

POST = {
    "title": "Bits & Bulls: chips rally", "date": "2026-11-20", "show": "Bits & Bulls",
    "summary": "Markets: chips lead. Top stories: one; two.",
    "sources": [{"title": "One", "publisher": "Wire", "url": "https://example.com/1"}],
    "chapters": [{"time": "0:00", "title": "Intro"}, {"time": "0:30", "title": "Markets"}],
    "quiz": {"question": "Which?", "options": ["A", "B", "C"], "reveal": "", "answer": "B"},
    "tags": ["ai", "markets"], "disclaimer": "Not advice.",
    "video": "../video.mp4", "short": None, "thumbnail": "../thumbnail.png",
}


def write_episode(out, day, media):
    folder = out / day
    (folder / "web").mkdir(parents=True)
    (folder / "web" / "post.json").write_text(json.dumps(POST | {"date": day}))
    (folder / "episode.json").write_text(json.dumps({
        "durationInFrames": 6900, "fps": 30,
        "scenes": [{"type": "intro"}, {"type": "news"}, {"type": "news"}]}))
    (folder / "script.md").write_text("# Script\n\nMAYA: Hello.\n")
    for name in media:
        (folder / name).write_bytes(b"data")


def write_feature(out):
    feature = Feature(
        slug="2026-w47-gpu", week="2026-W47", title="What is a GPU?", dek="Chips for AI.",
        topic="What is a GPU?", reading_minutes=4, published_at="2026-11-16T12:00:00+00:00",
        sections=[FeatureSection(heading=f"S{i}", body="Body.") for i in range(4)],
        takeaways=["One"], glossary=[GlossaryEntry(term="GPU", definition="A chip.")],
        related=[RelatedStory(title="T", url="https://example.com", source="Wire")],
        sources=[FeatureSource(title="T", url="https://example.com")],
        disclaimer="AI-written.", generated_by=GeneratedBy(agent="feature-writer", model="mock"))
    folder = out / "web" / "innovation"
    folder.mkdir(parents=True)
    (folder / "2026-w47-gpu.json").write_text(feature.model_dump_json(by_alias=True))
    (folder / "index.json").write_text(json.dumps([feature.summary().model_dump(by_alias=True)]))


@pytest.fixture(scope="module")
def out_dir(tmp_path_factory):
    out = tmp_path_factory.mktemp("out")
    write_episode(out, "2026-11-20", ["video.mp4", "thumbnail.png", "notes.txt"])
    write_episode(out, "2026-11-19", [])
    (out / "web").mkdir(exist_ok=True)
    (out / "web" / "index.json").write_text(json.dumps(
        [{"date": "2026-11-19"}, {"date": "2026-11-20"}]))
    write_feature(out)
    (out / "secret.txt").write_text("secret")
    return out


@pytest.fixture(scope="module")
def client(out_dir, tmp_path_factory):
    mp = pytest.MonkeyPatch()
    mp.setenv("NEWSROOM_OFFLINE", "1")
    mp.setenv("DATA_DIR", str(tmp_path_factory.mktemp("data")))
    mp.setenv("OUT_DIR", str(out_dir))
    mp.delenv("MCP_URL", raising=False)
    mp.setenv("WEB_ORIGIN", "http://localhost:3000")
    with TestClient(create_app(Settings())) as c:
        yield c
    mp.undo()
