from __future__ import annotations

import itertools
import re
from datetime import date

from newsroom_core.config import DISCLAIMER
from newsroom_core.models import Line, ShowScript

WORDS_PER_SECOND = 2.3
LEAD_IN_S = 1.2
SCENE_GAP_S = 0.55
ALERT_S = 1.75
TURN_GAP_S = 0.35
SENTENCE_GAP_S = 0.2
OUTRO_TAIL_S = 2.5

_SENTENCE = re.compile(r"[^.!?]+[.!?]*")


def _scenes(script: ShowScript) -> list[tuple[str, list[Line]]]:
    scenes: list[tuple[str, list[Line]]] = []
    if script.cold_open:
        scenes.append(("coldopen", script.cold_open))
    scenes += [("intro", script.intro), ("market", script.market.lines)]
    n = len(script.stories)
    for i, s in enumerate(script.stories, 1):
        scenes.append(("news", s.lines))
        if script.explainer and i == min(2, n):
            scenes.append(("explainer", script.explainer.lines))
    if script.quiz:
        scenes.append(("quiz", script.quiz.reveal_lines + script.quiz.lines))
    closer = script.outro[-1].speaker if script.outro else "a"
    scenes.append(("outro", [*script.outro, Line(speaker=closer, text=DISCLAIMER)]))
    return scenes


def estimate_seconds(script: ShowScript) -> float:
    """Deterministic runtime estimate that mirrors how the voice service lays out the show."""
    total = LEAD_IN_S
    for kind, lines in _scenes(script):
        words = sum(len(ln.text.split()) for ln in lines)
        sentences = sum(len([s for s in _SENTENCE.findall(ln.text) if s.strip()]) for ln in lines)
        turns = sum(1 for a, b in itertools.pairwise(lines) if a.speaker != b.speaker)
        total += words / WORDS_PER_SECOND + sentences * SENTENCE_GAP_S + turns * TURN_GAP_S
        if kind in {"market", "explainer", "quiz", "news"}:
            total += ALERT_S
        total += OUTRO_TAIL_S if kind == "outro" else SCENE_GAP_S
    return round(total, 1)


def script_markdown(script: ShowScript, names: dict[str, str], show_name: str, show_date: date | str,
                    ) -> str:
    def block(lines: list[Line]) -> list[str]:
        return [f"**{names[ln.speaker]}:** {ln.text}" for ln in lines]

    md = [f"# {show_name} — {show_date}", "", "## Cold open", *block(script.cold_open), "",
          "## Intro", *block(script.intro), "",
          f"## Markets — {script.market.headline}", *block(script.market.lines), ""]
    for s in script.stories:
        md += [f"## {s.headline} ({s.source})", *block(s.lines), f"<{s.url}>", ""]
    if script.explainer:
        md += [f"## AI in 30 seconds — {script.explainer.title}", *block(script.explainer.lines), ""]
    if script.quiz:
        q = script.quiz
        md += [f"## Quiz — {q.question}", *block(q.reveal_lines + q.lines),
               f"_Answer: {'ABC'[q.answer_index]}, {q.options[q.answer_index]}_", ""]
    md += ["## Outro", *block(script.outro), "", f"_{DISCLAIMER}_"]
    return "\n".join(md)
