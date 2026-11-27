"""Weekly "AI Innovation" feature: an explainer article grounded in the knowledge base and the news."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date

from newsroom_core.models import NewsItem
from newsroom_core.text import tokens
from pydantic import BaseModel, Field

from newsroom_agents.agents.base import Agent
from newsroom_agents.agents.editor import check_language, check_text_grounding
from newsroom_agents.agents.scriptwriter import first_sentences
from newsroom_agents.guardrails import (
    UNTRUSTED_NOTICE,
    as_data,
    policy_violation,
    redact_pii,
    sanitize_untrusted,
)

GENERIC = {"what", "does", "work", "works", "how", "why", "company", "value", "data", "needs"}
SENTENCE_START = re.compile(r"(^|[.!?:]\s+|\n)([A-Z])")
TRACK = "ai"
MIN_WORDS, MAX_WORDS = 450, 1100


class DraftSection(BaseModel):
    heading: str = Field(description="Short section heading, max 60 characters")
    body: str = Field(description="One or two plain-language paragraphs, 120 to 200 words")


class DraftTerm(BaseModel):
    term: str
    definition: str = Field(description="One plain sentence")


class FeatureDraft(BaseModel):
    title: str = Field(description="Article title, max 90 characters")
    dek: str = Field(description="One-sentence subtitle, max 180 characters")
    sections: list[DraftSection] = Field(description="Exactly 4 or 5 sections")
    takeaways: list[str] = Field(description="3 to 5 short takeaways, one sentence each")
    glossary: list[DraftTerm] = Field(description="3 to 5 key terms with one-sentence definitions")

    def text(self) -> str:
        parts = [self.dek, *(s.body for s in self.sections), *self.takeaways,
                 *(g.definition for g in self.glossary)]
        return "\n".join(parts)

    def words(self) -> int:
        return sum(len(s.body.split()) for s in self.sections)


@dataclass
class FeatureResult:
    draft: FeatureDraft
    topic: dict
    related: list[NewsItem]
    sources: list[NewsItem]
    used_fallback: bool = False
    issues: list[str] = field(default_factory=list)


def _lenient(text: str) -> str:
    """Sentence-initial capitals are not proper nouns; lowercase them before the name check."""
    return SENTENCE_START.sub(lambda m: m.group(1) + m.group(2).lower(), text)


def _entry_tokens(entry: dict) -> set[str]:
    return (tokens(entry["title"]) | tokens(entry["text"].partition("Keywords:")[2])) - GENERIC


def _clip(text: str, limit: int) -> str:
    text = text.strip()
    return text if len(text) <= limit else text[:limit - 1].rsplit(" ", 1)[0].rstrip(",;:") + "…"


class FeatureWriter(Agent):
    """Picks the week's topic from the knowledge base and writes the explainer article."""

    role = "feature-writer"
    tier = "smart"

    async def recent_news(self) -> list[NewsItem]:
        raw = await self.tools.call("get_site_news", hours=168, limit=300)
        items = []
        for r in raw:
            item = NewsItem.model_validate(r)
            title, flagged = sanitize_untrusted(item.title, 200)
            summary, flagged_s = sanitize_untrusted(item.summary, 300)
            if flagged or flagged_s:
                self.guard.add("input", "injection", "warn", self.role, item.title)
            if rule := policy_violation(f"{title} {summary}"):
                self.guard.add("policy", rule, "info", self.role, f"excluded {item.title}")
                continue
            items.append(item.model_copy(update={"title": title, "summary": summary}))
        return items

    async def pick_topic(self, week: str, monday: date, override: str | None,
                         local_used: set[str], news: list[NewsItem]) -> dict:
        entries = [e for e in await self.tools.call(
            "search_explainers", query="AI technology markets biotech", k=60, track=TRACK)
            if TRACK in e.get("tracks", [])]
        if override:
            match = next((e for e in entries if e["key"] == override), None)
            if not match:
                raise ValueError(
                    f"topic {override!r} is not an AI topic; choose from "
                    f"{', '.join(e['key'] for e in entries)}")
            return match
        recent = await self.tools.call(
            "recent_segments", kind="feature", before=monday.isoformat(), days=180)
        used = {s["key"] for s in recent} | local_used
        fresh = [e for e in entries if e["key"] not in used] or entries
        seen = Counter(t for i in news for t in tokens(f"{i.title} {i.summary}"))

        def rank(entry: dict) -> tuple[int, str]:
            relevance = sum(min(seen[t], 3) for t in _entry_tokens(entry))
            return -relevance, hashlib.sha1(f"{week}:{entry['key']}".encode()).hexdigest()

        return min(fresh, key=rank)

    def related_news(self, entry: dict, news: list[NewsItem]) -> list[NewsItem]:
        topic = _entry_tokens(entry)
        scored = [(len(topic & tokens(f"{i.title} {i.summary}")), i) for i in news]
        scored = [(n, i) for n, i in scored if n]
        scored.sort(key=lambda p: (-p[0], -p[1].score))
        return [i for _, i in scored[:4]]

    async def run(self, week: str, monday: date, topic: str | None = None,
                  local_used: set[str] | None = None) -> FeatureResult:
        news = await self.recent_news()
        entry = await self.pick_topic(week, monday, topic, local_used or set(), news)
        related = self.related_news(entry, news)
        extra = [i for i in sorted(news, key=lambda i: -i.score) if i not in related]
        sources = related + extra[:max(0, 2 - len(related))]
        material = self.material(entry, sources)
        self.log.info("writing feature on '%s' with %d related stories", entry["title"], len(related))

        system, user = self.system_prompt(), self.user_prompt(entry, sources)
        template = self.fallback(entry, related, sources)
        draft = await self.ask(system, user, FeatureDraft, lambda: template)
        if draft == template:
            if issues := self.check(draft, material, strict=False):
                self.guard.add("output", "feature_template", "warn", self.role, "; ".join(issues))
            return FeatureResult(self.redact(draft), entry, related, sources, True)
        issues = self.check(draft, material)
        if issues:
            self.guard.add("output", "feature_revise", "warn", self.role, "; ".join(issues))
            draft = await self.ask(
                system, f"{user}\n\nYour previous draft had problems. Fix them:\n- "
                + "\n- ".join(issues), FeatureDraft, lambda: template)
            issues = [] if draft == template else self.check(draft, material)
        used_fallback = draft == template or bool(issues)
        if issues:
            self.guard.add("output", "feature_fallback", "block", self.role, "; ".join(issues))
            draft = template
        return FeatureResult(self.redact(draft), entry, related, sources, used_fallback, issues)

    def system_prompt(self) -> str:
        return (
            f"You write the weekly 'AI Innovation' feature for the '{self.show_name}' website, an "
            "explainer article for a general, tech-curious reader.\n"
            "Write 600 to 900 words: a title, a one-sentence dek, exactly 4 or 5 sections with "
            "short headings, 3 to 5 takeaways and a short glossary. Explain the concept in plain "
            "words and connect it to the related news stories, naming the outlet that reported "
            "each one.\nSTRICT: use only facts from the reference text and the news stories; do "
            "not add company names, people, numbers, dates or quotes that are not in them. No "
            "predictions, no investment advice, no medical advice, no hype words. "
            + UNTRUSTED_NOTICE
        )

    def user_prompt(self, entry: dict, sources: list[NewsItem]) -> str:
        stories = "\n".join(f"{i.source} | {i.title} — {i.summary}" for i in sources)
        return (f"Reference text (vetted):\n{entry['title']}. {entry['text']}\n\n"
                f"Related stories this week:\n{as_data('source', stories)}")

    @staticmethod
    def material(entry: dict, sources: list[NewsItem]) -> str:
        news = " ".join(f"{i.source}. {i.title}. {i.summary}" for i in sources)
        return f"{entry['title']}. {entry['text']} {news}"

    def check(self, draft: FeatureDraft, material: str, strict: bool = True) -> list[str]:
        issues = []
        if strict and not 4 <= len(draft.sections) <= 5:
            issues.append("write exactly 4 or 5 sections")
        if strict and not 3 <= len(draft.takeaways) <= 5:
            issues.append("give 3 to 5 takeaways")
        if strict and not draft.glossary:
            issues.append("add a short glossary")
        if strict and not MIN_WORDS <= draft.words() <= MAX_WORDS:
            issues.append(f"article is {draft.words()} words; aim for 600 to 900")
        text = f"{draft.title}. {draft.text()}"
        issues += check_language(text)
        if rule := policy_violation(text):
            issues.append(f"content policy: {rule}")
        issues += check_text_grounding(_lenient(text), material, draft.title)
        return issues

    def redact(self, draft: FeatureDraft) -> FeatureDraft:
        total = 0

        def clean(text: str) -> str:
            nonlocal total
            text, n = redact_pii(text)
            total += n
            return text

        out = FeatureDraft(
            title=clean(draft.title), dek=clean(draft.dek),
            sections=[DraftSection(heading=clean(s.heading), body=clean(s.body))
                      for s in draft.sections[:5]],
            takeaways=[clean(t) for t in draft.takeaways[:5]],
            glossary=[DraftTerm(term=g.term, definition=clean(g.definition))
                      for g in draft.glossary[:6]],
        )
        if total:
            self.guard.add("output", "pii_redacted", "warn", self.role, f"{total} item(s)")
        return out

    def fallback(self, entry: dict, related: list[NewsItem], sources: list[NewsItem]) -> FeatureDraft:
        main, _, kw = entry["text"].partition("Keywords:")
        sentences = first_sentences(main, 8) or [entry["title"]]
        keywords = kw.strip().rstrip(".") or entry["title"].rstrip("?")
        cut = max(1, len(sentences) // 2)
        why = " ".join(sentences[cut:]) or sentences[-1]
        news = related or sources
        reported = " ".join(
            f"{i.source} reported: {i.title.rstrip('.')}. "
            f"{first_sentences(i.summary, 1)[0] if i.summary else ''}".strip() for i in news[:3])
        sections = [
            DraftSection(heading="The short version", body=" ".join(sentences[:cut])),
            DraftSection(heading="Why it matters", body=why),
            DraftSection(
                heading="In the news this week" if related else "More from this week's news",
                body=reported or "There were no closely related stories this week."),
            DraftSection(heading="Related ideas",
                         body=f"Also, topics that often come up alongside this one: {keywords}."),
        ]
        takeaways = [_clip(s, 140) for s in sentences[:3]]
        takeaways += [_clip(i.title, 140) for i in news[:max(0, 3 - len(takeaways))]]
        term = re.sub(r"^(what is|what are) (an?|the )?", "", entry["title"], flags=re.IGNORECASE)
        return FeatureDraft(
            title=entry["title"],
            dek="A plain-language explainer from the newsroom's vetted knowledge base, with this "
                "week's related headlines.",
            sections=sections, takeaways=takeaways,
            glossary=[DraftTerm(term=term.rstrip("?"), definition=sentences[0])],
        )
