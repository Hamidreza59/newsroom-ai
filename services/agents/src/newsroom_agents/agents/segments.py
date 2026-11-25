"""Agents for the recurring segments: cold open, AI-in-30-seconds explainer, and the daily quiz."""

from __future__ import annotations

import re

from newsroom_core.models import (
    Explainer,
    ExplainerCopy,
    HookCopy,
    Line,
    MarketSnapshot,
    NewsSegment,
    Quiz,
    QuizDraft,
)

from newsroom_agents.agents.base import Agent
from newsroom_agents.agents.scriptwriter import first_sentences, lead_for
from newsroom_agents.guardrails import UNTRUSTED_NOTICE, as_data

LETTERS = "ABC"


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


class HookWriter(Agent):
    """Writes the 5-second cold open that hooks viewers before the intro. Cheap model."""

    role = "hook-writer"
    tier = "fast"

    async def run(self, stories: list[NewsSegment], snap: MarketSnapshot) -> list[Line]:
        top = stories[0]
        mover = max(snap.watchlist, key=lambda q: abs(q.change_pct), default=None)
        system = (
            f"You write the cold open of '{self.show_name}', the first five seconds of the video.\n"
            f"{self.cast()}\n"
            "Write 1 or 2 lines, at most 25 words in total, that make viewers want to keep watching. "
            "Lead with the top story, optionally add the biggest market move. Use only facts and "
            "numbers given. No questions, no clickbait, no hype words, no investment advice. "
            + UNTRUSTED_NOTICE
        )
        facts = f"Top story ({top.source}): {top.headline}. {top.narration}"
        if mover:
            facts += f"\nBiggest watchlist move: {mover.name} {mover.change_pct:+.1f} percent."
        self.log.info("writing cold open")
        copy = await self.ask(system, as_data("source", facts), HookCopy,
                              lambda: HookCopy(lines=self.fallback(top, snap)))
        return copy.lines[:2]

    def fallback(self, top: NewsSegment, snap: MarketSnapshot) -> list[Line]:
        lines = [Line(speaker="a", text=f"{top.headline}.")]
        mover = max(snap.watchlist, key=lambda q: abs(q.change_pct), default=None)
        if mover and abs(mover.change_pct) >= 2:
            verb = "jumped" if mover.change_pct > 0 else "slid"
            lines.append(Line(speaker="b", text=f"Plus, {mover.name} {verb} "
                                                f"{abs(mover.change_pct):.1f} percent. Stay with us."))
        return lines


class ExplainerAgent(Agent):
    """'AI in 30 seconds': picks a concept linked to today's news and explains it from vetted text."""

    role = "explainer"
    tier = "smart"

    async def run(self, stories: list[NewsSegment], show_date: str) -> tuple[Explainer, str] | None:
        used = {s["key"] for s in await self.tools.call(
            "recent_segments", kind="explainer", before=show_date, days=21)}
        query = " ".join(f"{s.headline}. {s.narration}" for s in stories[:3])
        hits = await self.tools.call("search_explainers", query=query, k=6)
        fresh = [h for h in hits if h["key"] not in used] or hits
        if not fresh:
            return None
        entry = fresh[0]
        material = f"{entry['title']}. {entry['text']}"
        a, b = self.anchors["a"], self.anchors["b"]
        system = (
            f"You write the 'AI in 30 seconds' explainer on '{self.show_name}'.\n{self.cast()}\n"
            f"Write 3 dialogue lines, 40 to 60 words in total: {a} introduces the segment and "
            f"the question, {b} explains in plain words, and one of them closes with why it matters. "
            "STRICT: use only facts from the reference text; do not add names, numbers or claims. "
            "Title: max 40 characters, phrased as a question. Steps: exactly 3 short on-screen "
            "points, max 60 characters each."
        )
        self.log.info("writing explainer: %s", entry["title"])
        copy = await self.ask(system, f"Reference text:\n{material}", ExplainerCopy,
                              lambda: self.fallback(entry))
        return Explainer(key=entry["key"], title=copy.title, steps=copy.steps[:3],
                         lines=copy.lines), material

    def fallback(self, entry: dict) -> ExplainerCopy:
        sentences = first_sentences(entry["text"].split("Keywords:")[0], 4)
        steps = [s if len(s) <= 60 else s[:57].rsplit(" ", 1)[0] + "…" for s in sentences[:3]]
        return ExplainerCopy(
            title=entry["title"][:40],
            steps=steps,
            lines=[
                Line(speaker="a", text=f"Time for A.I. in 30 seconds. {entry['title']}"),
                Line(speaker="b", text=" ".join(sentences[:2])),
                Line(speaker="a", text=" ".join(sentences[2:4]) or "Now you know."),
            ],
        )


class QuizMaster(Agent):
    """Daily quiz about today's stories; yesterday's answer is revealed from memory. Cheap model."""

    role = "quiz-master"
    tier = "fast"

    async def run(self, stories: list[NewsSegment], materials: dict[str, str],
                  snap: MarketSnapshot, show_date: str) -> Quiz:
        reveal, reveal_lines = await self.yesterday(show_date)
        listing = "\n".join(f"{s.story_id} | {s.headline} | {s.narration}" for s in stories)
        system = (
            f"You write the daily quiz for '{self.show_name}'. Ask one multiple-choice question "
            "about a fact stated in one of today's stories. Give exactly 3 short options; exactly "
            "one is correct and must appear word for word in that story. The question must not "
            "contain the answer. Max 90 characters. " + UNTRUSTED_NOTICE
        )
        draft = await self.ask(system, as_data("source", listing), QuizDraft,
                               lambda: self.market_quiz(snap))
        problem = None if draft.story_id == "market" else self.validate(draft, materials)
        if problem:
            self.guard.add("output", "quiz_invalid", "warn", self.role, problem)
            draft = self.market_quiz(snap)
        lead = lead_for(0)
        co = "b" if lead == "a" else "a"
        options = "; ".join(f"{LETTERS[i]}, {o}" for i, o in enumerate(draft.options))
        lines = [
            Line(speaker=co, text=f"Quiz time! {draft.question}"),
            Line(speaker=lead, text=f"Is it {options}? Tell us in the comments, and we'll reveal "
                                    "the answer on tomorrow's show."),
        ]
        return Quiz(question=draft.question, options=draft.options,
                    answer_index=draft.answer_index, lines=lines, reveal=reveal,
                    reveal_lines=reveal_lines)

    @staticmethod
    def validate(draft: QuizDraft, materials: dict[str, str]) -> str | None:
        """Deterministic guardrail: the correct answer must be stated in the cited story."""
        if len(draft.options) != 3 or len({_norm(o) for o in draft.options}) != 3:
            return "needs exactly 3 distinct options"
        if not 0 <= draft.answer_index < 3:
            return "answer index out of range"
        if draft.story_id not in materials:
            return f"unknown story id {draft.story_id}"
        answer = _norm(draft.options[draft.answer_index])
        if not answer or answer not in _norm(materials[draft.story_id]):
            return f"answer '{draft.options[draft.answer_index]}' is not stated in the story"
        if answer in _norm(draft.question):
            return "question gives away the answer"
        if len(draft.question) > 120 or any(len(o) > 40 for o in draft.options):
            return "question or options too long"
        return None

    @staticmethod
    def market_quiz(snap: MarketSnapshot) -> QuizDraft:
        ranked = sorted(snap.watchlist, key=lambda q: -abs(q.change_pct))
        if len(ranked) < 3:
            ranked = (ranked * 3)[:3]
        top, others = ranked[0], [ranked[len(ranked) // 2], ranked[-1]]
        order = sorted([top, *others], key=lambda q: q.symbol)
        return QuizDraft(question="Which stock on our watchlist moved the most today?",
                         options=[q.name for q in order], answer_index=order.index(top),
                         story_id="market")

    async def yesterday(self, show_date: str) -> tuple[str, list[Line]]:
        prev = await self.tools.call("recent_segments", kind="quiz", before=show_date, days=7)
        if not prev:
            return "", []
        p = prev[0]["payload"]
        letter = LETTERS[p["answer_index"]]
        answer = p["options"][p["answer_index"]]
        text = f"{letter}: {answer}"
        lines = [Line(speaker="a", text=f"First, last show's quiz: {p['question']}"),
                 Line(speaker="b", text=f"The answer was {letter}, {answer}. Well done if you got it!")]
        return text, lines

