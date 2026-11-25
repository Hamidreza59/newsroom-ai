from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from newsroom.guardrails import GuardrailLog, redact_pii
from newsroom.models import Line, MarketSnapshot, NewsSegment, ShowScript, spoken

log = logging.getLogger("newsroom.editor")

PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:percent|per cent|%)", re.IGNORECASE)
LEVEL_RE = re.compile(r"\b(\d{1,3}(?:,\d{3})+|\d{4,6})(?:\.\d+)?\b")
ADVICE_RE = re.compile(
    r"\b(you should (?:buy|sell|invest)|time to (?:buy|sell)|buy now|sell now|guaranteed returns?|"
    r"can't lose|cannot lose|sure thing|price target|we recommend)\b",
    re.IGNORECASE,
)
MEDICAL_RE = re.compile(
    r"\b(cures? (?:cancer|diabetes|alzheimer'?s|aging)|miracle (?:drug|cure|treatment)|"
    r"guaranteed to (?:cure|work|heal)|you should (?:take|stop taking|try)|stop taking your|"
    r"instead of (?:seeing|asking) (?:a|your) doctor|proven to cure)\b",
    re.IGNORECASE,
)
HYPE_RE = re.compile(r"\b(game[- ]changer|revolutionary|insane|mind[- ]blowing)\b", re.IGNORECASE)

HEADLINE_MAX, POINT_MAX, BULLET_MAX = 60, 75, 64
STORY_MAX_WORDS = 85


@dataclass
class Review:
    market: list[str] = field(default_factory=list)
    stories: dict[str, list[str]] = field(default_factory=dict)

    @property
    def clean(self) -> bool:
        return not self.market and not any(self.stories.values())

    def summary(self) -> str:
        parts = [f"market: {m}" for m in self.market]
        parts += [f"story {sid}: {i}" for sid, issues in self.stories.items() for i in issues]
        return "; ".join(parts) or "no issues"


def allowed_percents(snap: MarketSnapshot) -> list[float]:
    vals = [abs(q.change_pct) for q in snap.indices + snap.watchlist]
    vals += [abs((q.price / q.series[0].close - 1) * 100) for q in snap.indices if q.series]
    return vals


def check_numbers(text: str, snap: MarketSnapshot) -> list[str]:
    issues = []
    allowed = allowed_percents(snap)
    for m in PERCENT_RE.finditer(text):
        val = float(m.group(1))
        if not any(abs(val - a) <= 0.06 for a in allowed):
            issues.append(f"'{m.group(0)}' does not match any figure in the fact sheet")
    levels = [q.price for q in snap.indices + snap.watchlist]
    for m in LEVEL_RE.finditer(text):
        val = float(m.group(1).replace(",", ""))
        if 1900 <= val <= 2100:
            continue
        if not any(abs(val - lv) / lv <= 0.01 for lv in levels):
            issues.append(f"level '{m.group(0)}' does not match any price in the fact sheet")
    for m in PRICE_RE.finditer(PERCENT_RE.sub("", text)):
        val = float(m.group(1))
        if not any(abs(val - lv) / lv <= 0.005 for lv in levels):
            issues.append(f"price '{m.group(0)}' does not match any price in the fact sheet")
    return issues


def check_language(text: str) -> list[str]:
    issues = []
    if m := ADVICE_RE.search(text):
        issues.append(f"remove investment-advice language: '{m.group(0)}'")
    if m := MEDICAL_RE.search(text):
        issues.append(f"remove medical-advice or cure claim: '{m.group(0)}'")
    if m := HYPE_RE.search(text):
        issues.append(f"remove hype word '{m.group(0)}'")
    return issues


PRICE_RE = re.compile(r"\b(\d{1,4}\.\d{2})\b")
PROPER_RE = re.compile(r"\b[A-Z][\w'-]*(?:\s+[A-Z][\w'-]*)*")
NUMBER_RE = re.compile(r"\b\d+(?:[.,]\d+)*\b")
COMMON = {
    "the", "this", "that", "these", "it", "in", "on", "according", "today", "meanwhile", "plus",
    "also", "however", "and", "but", "a", "an", "as", "with", "for", "after", "now", "its",
    "their", "they", "he", "she", "we", "our", "here", "there", "what", "why", "how", "while",
    "in an update on a story we've been following", "update", "reports", "said", "says", "if",
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "ai", "a.i",
    "so", "still", "both", "new", "next", "last", "first", "one", "two", "three", "stay",
    "thanks", "thank", "great", "wow", "interesting", "good", "right", "yes", "exactly", "indeed",
    "absolutely", "sounds", "that's", "it's", "let's", "i'm", "you", "your", "well", "big", "huge",
    "hello", "welcome", "see", "subscribe", "turning", "speaking", "over", "back", "up", "and i'm", "i", "fascinating", "wild", "really", "do", "does", "is", "are", "will", "could",
    "they're", "we're", "you're", "there's", "what's", "here's", "experts", "people",
}


SOURCE_STOP = {"the", "and", "news", "newsroom", "daily", "com", "org", "net", "blog", "review"}


def _norm(word: str) -> str:
    return word.lower().strip(".,;:!?\"()").removesuffix("'s")


def _attributed(seg: NewsSegment) -> bool:
    text = seg.narration.lower()
    words = [w for w in re.findall(r"[a-z0-9]+", seg.source.lower())
             if len(w) > 2 and w not in SOURCE_STOP]
    return any(w in text for w in words) or seg.source.lower() in text


def check_grounding(seg: NewsSegment, material: str, extra_known: str = "") -> list[str]:
    """Flag numbers and proper nouns in the narration that the source material never mentions."""
    return check_text_grounding(seg.narration, f"{material} {seg.source}", extra_known)


def check_text_grounding(text: str, material: str, extra_known: str = "") -> list[str]:
    known = f"{material} {extra_known}".lower().replace("’", "'")
    unsupported = []
    for m in PROPER_RE.finditer(text.replace("’", "'")):
        words = [_norm(w) for w in m.group(0).split()]
        missing = [w for w in words if w and w not in COMMON and w not in known]
        if missing:
            unsupported.append(" ".join(missing))
    for m in NUMBER_RE.finditer(text):
        if m.group(0) not in material:
            unsupported.append(m.group(0))
    unsupported = list(dict.fromkeys(unsupported))
    return [f"remove details not in the source material: {', '.join(unsupported)}"] if unsupported \
        else []


def check_story(seg: NewsSegment, material: str = "", extra_known: str = "") -> list[str]:
    issues = check_language(seg.narration)
    words = len(seg.narration.split())
    if words > STORY_MAX_WORDS:
        issues.append(f"narration is {words} words; keep it under 65")
    if not _attributed(seg):
        issues.append(f"attribute the story to {seg.source} by name")
    if material:
        issues += check_grounding(seg, material, extra_known)
    return issues


def _clip(text: str, limit: int) -> str:
    text = text.strip().rstrip(".")
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return cut.rstrip(",;:-") + "…"


class Editor:
    """Rule-based standards desk: fact-checks numbers, enforces compliance and on-screen limits."""

    role = "editor"

    def __init__(self, anchor_names: list[str] | None = None, show_name: str = ""):
        self.extra_known = " ".join([*(anchor_names or []), show_name])

    def review(self, script: ShowScript, snap: MarketSnapshot,
               materials: dict[str, str] | None = None) -> Review:
        materials = materials or {}
        review = Review()
        review.market = check_numbers(script.market.narration, snap) + check_language(
            script.market.narration
        )
        for seg in script.stories:
            review.stories[seg.story_id] = check_story(
                seg, materials.get(seg.story_id, ""), self.extra_known)
        for text in (spoken(script.intro), spoken(script.outro)):
            review.market += [f"bookend: {i}" for i in check_language(text)]
        log.info("review: %s", review.summary())
        return review

    def check_segment(self, lines: list[Line], material: str,
                      snap: MarketSnapshot | None = None) -> list[str]:
        """Checks for the cold open and explainer: language, grounding and, if given, numbers."""
        text = spoken(lines)
        issues = check_language(text) + check_text_grounding(text, material, self.extra_known)
        if snap is not None:
            issues += check_numbers(text, snap)
        return issues

    def redact(self, script: ShowScript, guard: GuardrailLog) -> ShowScript:
        """Output guardrail: no personal contact details on air."""
        def clean(lines: list[Line]) -> list[Line]:
            out = []
            for ln in lines:
                text, n = redact_pii(ln.text)
                if n:
                    guard.add("output", "pii_redacted", "warn", "editor", ln.text)
                out.append(Line(speaker=ln.speaker, text=text))
            return out

        update: dict = {"intro": clean(script.intro), "outro": clean(script.outro),
                        "cold_open": clean(script.cold_open),
                        "market": script.market.model_copy(update={"lines": clean(script.market.lines)}),
                        "stories": [s.model_copy(update={"lines": clean(s.lines)}) for s in script.stories]}
        if script.explainer:
            update["explainer"] = script.explainer.model_copy(
                update={"lines": clean(script.explainer.lines)})
        return script.model_copy(update=update)

    def enforce(self, script: ShowScript) -> ShowScript:
        market = script.market.model_copy(
            update={
                "headline": _clip(script.market.headline, 50),
                "bullets": [_clip(b, BULLET_MAX) for b in script.market.bullets[:3]],
            }
        )
        stories = []
        for seg in script.stories:
            lines = list(seg.lines)
            if lines and not _attributed(seg):
                first, _, rest = lines[0].text.partition(" ")
                if first.lower() in {"the", "a", "an", "this", "today", "in"}:
                    first = first.lower()
                lines[0] = Line(speaker=lines[0].speaker,
                                text=f"According to {seg.source}, {first} {rest}".strip())
            points = [_clip(p, POINT_MAX) for p in seg.points if p.strip()][:3]
            stories.append(
                seg.model_copy(
                    update={"headline": _clip(seg.headline, HEADLINE_MAX), "points": points,
                            "lines": lines}
                )
            )
        return script.model_copy(update={"market": market, "stories": stories})
