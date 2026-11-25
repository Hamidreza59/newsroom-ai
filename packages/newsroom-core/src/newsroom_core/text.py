import re

WORD_RE = re.compile(r"[a-z0-9]+")
STOP = {"the", "a", "an", "to", "of", "and", "in", "on", "for", "with", "is", "its", "as", "at",
        "by", "from", "new", "says", "after", "how", "why", "what", "it", "this", "that", "be"}


def tokens(text: str) -> set[str]:
    """Content words of a headline, for cheap de-duplication."""
    return {w for w in WORD_RE.findall(text.lower()) if w not in STOP and len(w) > 2}
