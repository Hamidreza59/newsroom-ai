from newsroom.data.news import categorize, merge_duplicates, sample_news, source_from_domain
from newsroom.rag.embedder import HashingEmbedder
from newsroom.rag.store import VectorStore, chunk_markdown


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
    from newsroom.agents.news_scout import NewsScout
    from newsroom.llm import MockProvider

    items = sample_news()
    scout = NewsScout(MockProvider(), None, "Show")
    tech_only = [i for i in items if i.category != "Biotech"][:4]
    mixed = scout.ensure_mix(tech_only, items)
    assert any(i.category == "Biotech" for i in mixed) and len(mixed) == 4
