from __future__ import annotations

import re
from datetime import date

from newsroom.agents.base import Agent
from newsroom.guardrails import UNTRUSTED_NOTICE, as_data
from newsroom.models import (
    BookendCopy,
    Line,
    MarketBrief,
    NewsItem,
    NewsSegment,
    ShowScript,
    StoryCopy,
)

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")


def first_sentences(text: str, n: int) -> list[str]:
    return [s for s in SENTENCE_RE.split(text.strip()) if s][:n]


def lead_for(index: int) -> str:
    """Stories alternate between the anchors, starting with anchor "a"."""
    return "a" if index % 2 == 0 else "b"


class Scriptwriter(Agent):
    role = "scriptwriter"

    async def write_story(self, item: NewsItem, index: int, feedback: str = "") -> NewsSegment:
        guide = await self.style("story length attribution follow-up on-screen text", k=3)
        lead = lead_for(index)
        co = "b" if lead == "a" else "a"
        lead_name, co_name = self.anchors[lead], self.anchors[co]
        system = (
            f"You write news copy for '{self.show_name}'.\n{self.cast()}\n"
            f"Style rules:\n{guide}\n"
            f"Write 2 or 3 dialogue lines, 35 to 55 words in total. {lead_name} (speaker "
            f"\"{lead}\") reports the story and names the outlet. {co_name} (speaker \"{co}\") "
            "adds one short reaction or question, at most 12 words, with no new facts. "
            f"{lead_name} may answer in one short line, only from the material. "
            "STRICT: every fact must come from the title or summary given. Do not add "
            "background, dates, people, reasons or numbers that are not in the material; if the "
            "material is thin, write less. Headline: max 55 characters. Points: exactly 3 short "
            "fragments, max 70 characters each, also only from the material. " + UNTRUSTED_NOTICE
        )
        user = as_data("source", (
            f"Outlet: {item.source}\nCategory: {item.category}\nTitle: {item.title}\n"
            f"Summary: {item.summary or '(no summary, use the title only)'}"
        )) + f"\nFollow-up to a story covered earlier this week: {'yes' if item.follow_up else 'no'}"
        if feedback:
            user += f"\n\nThe editor rejected your previous draft. Fix these issues:\n{feedback}"
        copy = await self.ask(system, user, StoryCopy, lambda: self.fallback_story(item, index))
        return self.segment(item, copy)

    @staticmethod
    def segment(item: NewsItem, copy: StoryCopy) -> NewsSegment:
        return NewsSegment(
            story_id=item.id, headline=copy.headline, points=copy.points, lines=copy.lines,
            source=item.source, url=item.url, category=item.category, follow_up=item.follow_up,
        )

    async def write_bookends(self, market: MarketBrief, stories: list[NewsSegment],
                             show_date: date) -> BookendCopy:
        guide = await self.style("voice tone sign-off subscribe", k=2)
        a, b = self.anchors["a"], self.anchors["b"]
        system = (
            f"You write the opening and closing of '{self.show_name}', a daily show about markets "
            f"and AI/tech news.\n{self.cast()}\nStyle rules:\n{guide}\n"
            f"Intro: 2 lines, 20 to 35 words in total. {a} greets viewers, names the show "
            f"and the date and gives their name; {b} gives their name and teases the top two "
            "items. Outro: 2 lines, 12 to 20 words in total, a friendly sign-off from both "
            "inviting viewers to subscribe for tomorrow. Do not write a disclaimer."
        )
        rundown = "\n".join(f"- {s.headline}" for s in stories)
        user = (
            f"Date: {show_date.strftime('%A, %B %-d')}\nMarket headline: {market.headline}\n"
            f"Stories:\n{rundown}"
        )
        return await self.ask(
            system, user, BookendCopy, lambda: self.fallback_bookends(market, stories, show_date)
        )

    async def run(self, market: MarketBrief, items: list[NewsItem], show_date: date) -> ShowScript:
        stories = []
        for i, item in enumerate(items):
            self.log.info("writing story: %s", item.title[:60])
            stories.append(await self.write_story(item, i))
        bookends = await self.write_bookends(market, stories, show_date)
        return ShowScript(intro=bookends.intro, market=market, stories=stories,
                          outro=bookends.outro)

    def fallback_story(self, item: NewsItem, index: int) -> StoryCopy:
        lead = lead_for(index)
        co = "b" if lead == "a" else "a"
        summary = first_sentences(item.summary, 2)
        opener = "In an update on a story we've been following, " if item.follow_up else ""
        lines = [Line(speaker=lead,
                      text=f"{opener}{item.source} reports: {item.title}. " + " ".join(summary))]
        lines.append(Line(speaker=co, text="That's one to watch."))
        points = list(summary) or [item.title]
        while len(points) < 3:
            points.append(f"Source: {item.source}" if len(points) == 1 else item.category + " news")
        return StoryCopy(headline=item.title[:55], points=points[:3], lines=lines)

    def fallback_bookends(self, market: MarketBrief, stories: list[NewsSegment],
                          show_date: date) -> BookendCopy:
        a, b = self.anchors["a"], self.anchors["b"]
        top = stories[0].headline if stories else "the latest in AI"
        return BookendCopy(
            intro=[
                Line(speaker="a", text=f"Hello and welcome to {self.show_name} for "
                                       f"{show_date.strftime('%A, %B %-d')}. I'm {a}."),
                Line(speaker="b", text=f"And I'm {b}. Today: {market.headline}, and {top}."),
            ],
            outro=[
                Line(speaker="a", text=f"That's {self.show_name} for today."),
                Line(speaker="b", text="Subscribe so you don't miss tomorrow's update. "
                                       "See you then!"),
            ],
        )
