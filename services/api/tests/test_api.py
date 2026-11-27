import pytest
from fastapi.testclient import TestClient
from newsroom_api.app import create_app
from newsroom_core.config import Settings
from newsroom_core.site import Feature, MarketOverview, NewsFeed

TABS = ["markets", "ai", "ai-finance", "tech", "biotech"]


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "offline": True}


def test_cors_allows_the_web_origin(client):
    ok = client.get("/api/health", headers={"Origin": "http://localhost:3000"})
    assert ok.headers["access-control-allow-origin"] == "http://localhost:3000"
    other = client.get("/api/health", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in other.headers


def test_markets_overview(client):
    body = client.get("/api/markets/overview").json()
    overview = MarketOverview.model_validate(body)
    assert body["sampleData"] is True and "changePct" in body["indices"][0]
    assert len(overview.indices) == 3 and len(overview.indices[0].series) >= 20
    assert len(overview.watchlist) == 16 and len(overview.watchlist[0].series) >= 20
    assert len(overview.gainers) <= 3 and len(overview.losers) <= 3
    assert [s.name for s in overview.sectors] == ["AI & Chips", "Big Tech", "Biotech"]
    chips = overview.sectors[0]
    assert [m.symbol for m in chips.members] == ["NVDA", "AMD", "AVGO", "TSM"]
    assert chips.change_pct == pytest.approx(sum(m.change_pct for m in chips.members) / 4, abs=0.01)


@pytest.mark.parametrize(("range_", "n"), [("1mo", 22), ("6mo", 126), ("1y", 252)])
def test_history_ranges(client, range_, n):
    body = client.get("/api/markets/history/NVDA", params={"range": range_}).json()
    assert body["symbol"] == "NVDA" and body["name"] == "Nvidia" and body["range"] == range_
    assert len(body["points"]) == n and set(body["points"][0]) == {"date", "close"}


def test_history_defaults_index_symbols_and_errors(client):
    assert client.get("/api/markets/history/nvda").json()["range"] == "6mo"
    assert client.get("/api/markets/history/%5EGSPC?range=1mo").json()["name"] == "S&P 500"
    assert client.get("/api/markets/history/ZZZZ").status_code == 404
    assert client.get("/api/markets/history/NVDA?range=5y").status_code == 422


@pytest.mark.parametrize("tab", TABS)
def test_news_tabs_are_filtered_and_complete(client, tab):
    feed = NewsFeed.model_validate(client.get("/api/news", params={"tab": tab}).json())
    assert feed.tab == tab and feed.items
    assert all(tab in i.tags for i in feed.items)
    assert len(feed.volume) == 7 and sum(v.count for v in feed.volume) >= len(feed.items)
    assert feed.volume[-1].date > feed.volume[0].date
    assert 0 < len(feed.top_sources) <= 6 and 0 < len(feed.keywords) <= 12


def test_news_markets_only_items_are_website_only_and_limit_applies(client):
    markets = client.get("/api/news?tab=markets&limit=2").json()
    assert len(markets["items"]) == 2 and markets["label"] == "Markets"
    ai = client.get("/api/news?tab=ai").json()
    assert not {i["id"] for i in ai["items"]} & {
        i["id"] for i in client.get("/api/news?tab=markets").json()["items"]
        if i["tags"] == ["markets"]}
    keywords = {k["term"] for k in client.get("/api/news?tab=markets").json()["keywords"]}
    assert not keywords & {"stocks", "market", "markets"}


def test_news_validation(client):
    assert client.get("/api/news?tab=sports").status_code == 422
    assert client.get("/api/news?tab=ai&limit=0").status_code == 422
    assert client.get("/api/news?tab=ai&limit=101").status_code == 422


def test_home(client):
    body = client.get("/api/home").json()
    assert body["latestEpisode"]["date"] == "2026-11-20"
    assert body["feature"]["slug"] == "2026-w47-gpu"
    assert [t["tab"] for t in body["topStories"]] == TABS
    assert all(1 <= len(t["items"]) <= 3 for t in body["topStories"])
    assert body["markets"]["indices"]


def test_episode_list_and_detail(client):
    listing = client.get("/api/episodes").json()
    assert [e["date"] for e in listing] == ["2026-11-20", "2026-11-19"]
    first = listing[0]
    assert first["durationSeconds"] == 230 and first["storyCount"] == 2
    assert first["videoUrl"] == "/media/2026-11-20/video.mp4"
    assert first["thumbnailUrl"] == "/media/2026-11-20/thumbnail.png" and first["shortUrl"] is None
    assert listing[1]["videoUrl"] is None
    detail = client.get("/api/episodes/2026-11-20").json()
    assert detail["chapters"][1] == {"time": "0:30", "title": "Markets"}
    assert detail["sources"][0]["publisher"] == "Wire" and detail["quiz"]["answer"] == "B"
    assert detail["scriptMarkdown"].startswith("# Script") and detail["tags"] == ["ai", "markets"]
    assert client.get("/api/episodes/2026-11-19").json()["scriptMarkdown"].startswith("# Script")


def test_episode_errors(client):
    assert client.get("/api/episodes/2026-01-01").status_code == 404
    assert client.get("/api/episodes/not-a-date").status_code == 422
    assert client.get("/api/episodes/..%2F..%2Fetc").status_code in {404, 422}


def test_innovation(client):
    assert [f["slug"] for f in client.get("/api/innovation").json()] == ["2026-w47-gpu"]
    feature = Feature.model_validate(client.get("/api/innovation/2026-w47-gpu").json())
    assert len(feature.sections) == 4 and feature.generated_by.agent == "feature-writer"
    assert client.get("/api/innovation/missing").status_code == 404
    assert client.get("/api/innovation/index").status_code == 404
    assert client.get("/api/innovation/Bad_Slug").status_code == 422


def test_media_whitelist(client, out_dir):
    ok = client.get("/media/2026-11-20/video.mp4")
    assert ok.status_code == 200 and ok.content == b"data"
    assert ok.headers["content-type"] == "video/mp4"
    assert client.get("/media/2026-11-20/thumbnail.png").headers["content-type"] == "image/png"
    assert client.get("/media/2026-11-20/short.mp4").status_code == 404
    assert client.get("/media/2026-11-20/notes.txt").status_code == 404
    assert client.get("/media/2026-11-20/post.json").status_code == 404
    assert client.get("/media/2026-11-20/..%2F..%2Fsecret.txt").status_code == 404
    assert client.get("/media/..%2F/video.mp4").status_code == 404
    assert client.get("/media/2026-11-2/video.mp4").status_code == 404
    assert client.get("/media/%2e%2e/secret.txt").status_code == 404


def test_upstream_failure_returns_503(out_dir, monkeypatch):
    monkeypatch.setenv("OUT_DIR", str(out_dir))
    monkeypatch.setenv("MCP_URL", "http://127.0.0.1:9/mcp")
    with TestClient(create_app(Settings()), raise_server_exceptions=False) as c:
        assert c.get("/api/news?tab=ai").status_code == 503
        assert c.get("/api/health").status_code == 200
