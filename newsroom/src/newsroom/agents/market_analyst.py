from __future__ import annotations

from datetime import date

from newsroom.agents.base import Agent
from newsroom.models import Line, MarketBrief, MarketSnapshot, Quote


def _move(q: Quote) -> str:
    verb = "rose" if q.change_pct > 0 else "fell" if q.change_pct < 0 else "was flat"
    return f"{q.name} {verb} {abs(q.change_pct):.1f} percent"


def fact_sheet(snap: MarketSnapshot) -> str:
    lines = [f"Session date: {snap.as_of}", "Indices:"]
    for q in snap.indices:
        month = (q.price / q.series[0].close - 1) * 100 if q.series else 0
        lines.append(
            f"- {q.name}: closed at {q.price:,.0f}, {q.change_pct:+.1f} percent on the day, "
            f"{month:+.1f} percent over the past month"
        )
    lines.append("Biggest gainers in the AI and big-tech watchlist:")
    lines += [f"- {q.name}: {q.change_pct:+.1f} percent to {q.price:,.2f}" for q in snap.gainers()]
    lines.append("Biggest decliners in the watchlist:")
    lines += [f"- {q.name}: {q.change_pct:+.1f} percent to {q.price:,.2f}" for q in snap.losers()]
    if not snap.losers():
        lines.append("- none, every watchlist stock rose")
    return "\n".join(lines)


def session_label(as_of: str) -> str:
    d = date.fromisoformat(as_of)
    return f"{d.strftime('%A')}'s session" if d != date.today() else "today"


class MarketAnalyst(Agent):
    role = "market-analyst"

    async def run(self, snap: MarketSnapshot, feedback: str = "") -> MarketBrief:
        guide = await self.style("numbers markets percent rounding tone")
        a, b = self.anchors["a"], self.anchors["b"]
        system = (
            f"You write the market segment of '{self.show_name}', a daily markets and AI news "
            f"show.\n{self.cast()}\n"
            f"Style rules:\n{guide}\n"
            f"Write 3 dialogue lines, 45 to 70 words in total. {b} leads the markets: the "
            f"first line is {a} handing over to {b} in a few words, then {b} covers the three "
            f"indices, the standout AI and tech movers and the one-month trend. {a} may add one "
            "short reaction or question. Use only numbers from the fact sheet. "
            "Headline: max 50 characters. Bullets: exactly 3, max 60 characters each."
        )
        user = f"Fact sheet ({session_label(snap.as_of)}):\n{fact_sheet(snap)}"
        if feedback:
            user += f"\n\nThe editor rejected your previous draft. Fix these issues:\n{feedback}"
        self.log.info("writing market segment")
        return await self.ask(system, user, MarketBrief, lambda: self.fallback(snap))

    def fallback(self, snap: MarketSnapshot) -> MarketBrief:
        idx = snap.indices
        lead = idx[0]
        mood = "a strong day" if lead.change_pct > 0.5 else "a rough day" if lead.change_pct < -0.5 \
            else "a quiet day"
        lines = [
            Line(speaker="a", text=f"Let's start with the markets. {self.anchors['b']}?"),
            Line(speaker="b", text=f"It was {mood} on Wall Street. "
                                   + ", ".join(_move(q) for q in idx) + "."),
        ]
        tech = []
        if g := snap.gainers():
            tech.append("In tech, " + " and ".join(_move(q) for q in g[:2]) + ".")
        if lo := snap.losers():
            tech.append("On the downside, " + _move(lo[0]) + ".")
        if tech:
            lines.append(Line(speaker="b", text=" ".join(tech)))
        return MarketBrief(
            headline=f"{lead.name} {'up' if lead.change_pct >= 0 else 'down'} "
                     f"{abs(lead.change_pct):.1f}%",
            lines=lines,
            bullets=[f"{q.name} {q.change_pct:+.1f}%" for q in idx][:3],
        )
