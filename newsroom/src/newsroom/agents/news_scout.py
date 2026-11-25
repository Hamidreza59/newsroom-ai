from __future__ import annotations

from newsroom.agents.base import Agent
from newsroom.data.news import RSS_FEEDS, tokens
from newsroom.guardrails import UNTRUSTED_NOTICE, as_data, policy_violation, sanitize_untrusted
from newsroom.models import NewsItem, StoryPicks

REPEAT_THRESHOLD = 0.8
FOLLOW_UP_THRESHOLD = 0.55
RSS_SOURCES = set(RSS_FEEDS)


class NewsScout(Agent):
    """Pulls the news wire, filters repeats via the RAG archive, and picks the day's stories."""

    role = "news-scout"

    async def run(self, count: int, show_date: str) -> list[NewsItem]:
        raw = await self.tools.call("get_ai_tech_news", hours=30, limit=25)
        candidates = [c for c in (self.screen(NewsItem.model_validate(r)) for r in raw) if c]
        self.log.info("wire returned %d candidate stories after screening", len(candidates))

        fresh: list[NewsItem] = []
        for item in candidates:
            hits = await self.tools.call(
                "search_news_archive", query=f"{item.title}. {item.summary}", k=1, days=7,
                before=show_date,
            )
            best = hits[0]["similarity"] if hits else 0.0
            if best >= REPEAT_THRESHOLD:
                self.log.info("skip repeat (%.2f): %s", best, item.title)
                continue
            fresh.append(item.model_copy(update={"follow_up": best >= FOLLOW_UP_THRESHOLD}))

        pool = fresh[:15]
        listing = as_data("source", "\n".join(
            f"{i.id} | {i.category} | {i.source} | covered by {i.coverage} outlets | {i.title} — "
            f"{i.summary[:160]}"
            for i in pool
        ))
        system = (
            "You are the news editor of a daily markets and AI/tech news show for a general, "
            f"tech-curious audience. Choose the {count} most newsworthy stories. Prefer real news "
            "(launches, research results, regulation, business moves) over opinion pieces, guides "
            "and listicles. Never pick two stories about the same event or company. Include at "
            "least two AI stories. Return their ids, most important first. "
            + UNTRUSTED_NOTICE
        )
        picks = await self.ask(
            system, f"Candidate stories:\n{listing}", StoryPicks, lambda: self.fallback(pool, count)
        )
        by_id = {i.id: i for i in pool}
        chosen = [by_id[i] for i in dict.fromkeys(picks.ids) if i in by_id]
        chosen = self._dedupe(chosen)
        for extra in self._dedupe(pool):
            if len(chosen) >= count:
                break
            if extra not in chosen and not self._overlaps(extra, chosen):
                chosen.append(extra)
        chosen = [await self.enrich(c) for c in chosen[:count]]
        self.log.info("picked: %s", "; ".join(c.title[:50] for c in chosen))
        return chosen

    def screen(self, item: NewsItem) -> NewsItem | None:
        """Input guardrails: content policy and prompt-injection hygiene for untrusted web text."""
        if rule := policy_violation(f"{item.title} {item.summary}"):
            self.guard.add("policy", rule, "block", self.role, item.title)
            return None
        title, t_flag = sanitize_untrusted(item.title, 200)
        summary, s_flag = sanitize_untrusted(item.summary)
        if t_flag or s_flag:
            self.guard.add("input", "prompt_injection", "warn", self.role, item.title)
        return item.model_copy(update={"title": title, "summary": summary})

    async def enrich(self, item: NewsItem) -> NewsItem:
        details = await self.tools.call("get_article_details", url=item.url)
        update: dict = {}
        description, flagged = sanitize_untrusted(details.get("description", ""))
        if flagged:
            self.guard.add("input", "prompt_injection", "warn", self.role, item.url)
        if policy_violation(description):
            description = ""
        if len(description) > len(item.summary):
            update["summary"] = description
        site = details.get("site_name", "").strip()
        if site and 2 <= len(site) <= 40 and item.source not in RSS_SOURCES:
            update["source"] = site
        return item.model_copy(update=update) if update else item

    @staticmethod
    def _overlaps(item: NewsItem, others: list[NewsItem]) -> bool:
        t = tokens(item.title)
        return any(len(t & tokens(o.title)) >= 2 for o in others)

    def _dedupe(self, items: list[NewsItem]) -> list[NewsItem]:
        out: list[NewsItem] = []
        for item in items:
            if not self._overlaps(item, out):
                out.append(item)
        return out

    def fallback(self, pool: list[NewsItem], count: int) -> StoryPicks:
        return StoryPicks(ids=[i.id for i in self._dedupe(pool)[:count]])
