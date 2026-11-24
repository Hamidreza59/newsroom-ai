from newsroom.agents.editor import Editor, check_grounding, check_language, check_numbers
from newsroom.data.market import sample_snapshot
from newsroom.models import Line, MarketBrief, NewsSegment, ShowScript


def seg(narration: str, source: str = "The Verge") -> NewsSegment:
    return NewsSegment(story_id="s1", headline="A headline", points=["a", "b", "c"],
                       lines=[Line(speaker="a", text=narration)], source=source, url="https://x",
                       category="AI")


def say(text: str) -> list[Line]:
    return [Line(speaker="a", text=text)]


def test_numbers_must_match_fact_sheet():
    snap = sample_snapshot()
    sp = snap.indices[0]
    good = f"The S&P 500 moved {abs(sp.change_pct):.1f} percent to {sp.price:,.0f}."
    assert check_numbers(good, snap) == []
    assert check_numbers("The S&P 500 jumped 42.3 percent.", snap)
    assert check_numbers("It closed at 1,234,567.", snap)


def test_advice_and_hype_are_flagged():
    assert check_language("You should buy Nvidia now.")
    assert check_language("A revolutionary chip.")
    assert check_language("Nvidia rose after earnings.") == []


def test_grounding_flags_invented_details():
    material = "Jensen Huang Reinstated as Nvidia CEO. The board reinstated Jensen Huang as CEO."
    story = seg("According to The Verge, Nvidia reinstated Jensen Huang. He testified before "
                "Congress about China.")
    issues = check_grounding(story, material)
    assert issues and "congress" in issues[0] and "china" in issues[0]
    assert check_grounding(seg("The Verge reports Nvidia reinstated Jensen Huang as CEO."),
                           material) == []


def test_review_requires_attribution_and_enforce_adds_it():
    snap = sample_snapshot()
    script = ShowScript(
        intro=say("Hello."), outro=say("Bye."),
        market=MarketBrief(headline="Stocks", lines=say("Stocks were mixed."), bullets=["a", "b", "c"]),
        stories=[seg("Nvidia reinstated its CEO.")],
    )
    review = Editor().review(script, snap)
    assert any("attribute" in i for i in review.stories["s1"])
    fixed = Editor().enforce(script)
    assert fixed.stories[0].narration.startswith("According to The Verge, Nvidia")


def test_anchor_names_are_not_flagged_as_invented():
    material = "Nvidia reinstated Jensen Huang as CEO."
    story = seg("The Verge reports Nvidia reinstated Jensen Huang as CEO. Thanks, Leo.")
    assert check_grounding(story, material) and check_grounding(story, material, "Maya Leo") == []


def test_enforce_clips_on_screen_text():
    script = ShowScript(
        intro=say("Hi."), outro=say("Bye."),
        market=MarketBrief(headline="x" * 80, lines=say("n"), bullets=["y" * 100, "b", "c"]),
        stories=[seg("The Verge reports it.").model_copy(update={"headline": "word " * 20})],
    )
    out = Editor().enforce(script)
    assert len(out.market.headline) <= 50
    assert len(out.market.bullets[0]) <= 64
    assert len(out.stories[0].headline) <= 60
