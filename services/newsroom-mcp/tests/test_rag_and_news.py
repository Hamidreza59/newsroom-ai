import pytest
from newsroom_mcp.data.market import get_history
from newsroom_mcp.data.news import (
    categorize,
    compute_tags,
    get_news,
    get_site_news,
    is_video_item,
    merge_duplicates,
    sample_news,
    source_from_domain,
)
from newsroom_mcp.rag.embedder import HashingEmbedder
from newsroom_mcp.rag.store import VectorStore, chunk_markdown


def test_vector_store_search_and_date_window():
    store = VectorStore(":memory:", HashingEmbedder())
    store.add("archive", [
        ("a", "2026-11-20", "Nvidia unveils new inference chip for data centers", {}),
        ("b", "2026-11-21", "Regulators propose app store payment rules", {}),
        ("c", "2026-11-23", "Nvidia inference chip ships to cloud providers", {}),
    ])
    hits = store.search("archive", "Nvidia inference chip", k=3)
    assert hits[0].id in {"a", "c"} and hits[0].similarity > hits[-1].similarity
    windowed = store.search("archive", "Nvidia inference chip", k=3, since="2026-11-19",
                            until="2026-11-23")
    assert {h.id for h in windowed} == {"a", "b"}


def test_chunk_markdown_splits_on_h2():
    chunks = chunk_markdown("# Title\n\n## One\nfirst\n\n## Two\nsecond\n")
    assert chunks == [("One", "first"), ("Two", "second")]


def test_merge_duplicates_boosts_coverage():
    items = sample_news()
    dupe = items[0].model_copy(update={"id": "dupe", "source": "Other", "url": "https://o"})
    merged = merge_duplicates([*items, dupe])
    top = next(m for m in merged if m.title == items[0].title)
    assert len(merged) == len(items) and top.coverage == 2


def test_categorize_and_source_names():
    assert categorize("OpenAI ships a new model") == "AI"
    assert categorize("Apple unveils a new iPhone") == "Tech"
    assert categorize("Local bakery wins award") is None
    assert categorize("AI-designed antibody enters clinical trial") == "Biotech"
    assert categorize("FDA approves new gene therapy") == "Biotech"
    assert source_from_domain("nvidianews.nvidia.com") == "Nvidia"
    assert source_from_domain("www.bbc.co.uk") == "bbc"
    assert source_from_domain("z.ai") == "z.ai"


def test_scout_balances_rundown_with_biotech():
    from newsroom_agents.agents.news_scout import NewsScout
    from newsroom_agents.llm import MockProvider

    items = sample_news()
    scout = NewsScout(MockProvider(), None, "Show")
    tech_only = [i for i in items if i.category != "Biotech"][:4]
    mixed = scout.ensure_mix(tech_only, items)
    assert any(i.category == "Biotech" for i in mixed) and len(mixed) == 4


def test_compute_tags_multi_label():
    assert compute_tags("Stocks rally as the Fed signals rate cuts") == ["markets"]
    assert compute_tags("Bank deploys an AI assistant for fraud checks") == [
        "ai", "markets", "ai-finance"]
    assert "biotech" in compute_tags("FDA approves new gene therapy")
    assert compute_tags("Local bakery wins award") == []
    assert "markets" not in compute_tags("Parents fed up with the new app")


def test_site_news_includes_markets_but_video_news_does_not():
    site = get_site_news(True, 168)
    tags = {t for i in site for t in i.tags}
    assert {"ai", "tech", "biotech", "markets", "ai-finance"} <= tags
    assert any(i.tags == ["markets"] for i in site)
    video = get_news(True, 30)
    assert [i.id for i in video] == [i.id for i in sample_news()] and all(is_video_item(i) for i in video)
    assert len(get_site_news(True, 24)) < len(site)


@pytest.mark.parametrize(("range_", "n"), [("1mo", 22), ("6mo", 126), ("1y", 252)])
def test_sample_history_length_and_validation(range_, n):
    points = get_history("NVDA", range_, True)
    assert len(points) == n and points == get_history("NVDA", range_, True)
    assert get_history("^GSPC", range_, True)[0].date < points[-1].date


def test_history_rejects_unknown_symbol_and_range():
    with pytest.raises(ValueError):
        get_history("ZZZZ", "1mo", True)
    with pytest.raises(ValueError):
        get_history("NVDA", "5y", True)


def test_search_explainers_track_filter(tmp_path, monkeypatch):
    from newsroom_mcp import server

    monkeypatch.setenv("NEWSROOM_OFFLINE", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    server.settings.cache_clear()
    server._store.cache_clear()
    ai = server.search_explainers("earnings reports", k=50, track="ai")
    assert ai and all("ai" in e["tracks"] for e in ai)
    assert "earnings" not in {e["key"] for e in ai} and len(ai) >= 18
    allk = server.search_explainers("earnings reports", k=50)
    assert "earnings" in {e["key"] for e in allk} and "Track:" not in allk[0]["text"]
    server.settings.cache_clear()
    server._store.cache_clear()
