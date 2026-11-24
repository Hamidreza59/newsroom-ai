from __future__ import annotations

import re

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")

_REPLACEMENTS = [
    (re.compile(r"\bS&P\b"), "S and P"),
    (re.compile(r"(\d)\s*%"), r"\1 percent"),
    (re.compile(r"&"), " and "),
    (re.compile(r"\bAI\b"), "A.I."),
    (re.compile(r"\bCEO\b"), "C.E.O."),
    (re.compile(r"\bvs\.?\b", re.IGNORECASE), "versus"),
    (re.compile(r"\be\.g\.", re.IGNORECASE), "for example"),
    (re.compile(r"[“”]"), '"'),
    (re.compile(r"[‘’]"), "'"),
    (re.compile(r"—|–"), ", "),
    (re.compile(r"\s{2,}"), " "),
]


def normalize_for_speech(text: str) -> str:
    for pattern, repl in _REPLACEMENTS:
        text = pattern.sub(repl, text)
    return text.strip()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_RE.split(text.strip()) if s.strip()]
