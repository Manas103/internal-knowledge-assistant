# Finds the single most distinctive short phrase in a passage, by corpus-wide idf: the
# window of 2-3 words whose lowercased tokens carry the most idf weight wins. This is what
# qagen.py quotes (a few words, not a paragraph) when it writes a question grounded in a
# real passage, which is why extracted phrases stay short regardless of how long the
# source passage is.
from __future__ import annotations

import re

_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9\-]*")


def extract_keyphrase(text: str, idf: dict[str, float], window: tuple[int, int] = (2, 3)) -> str:
    words = _WORD_RE.findall(text)
    if not words:
        return ""
    best_phrase, best_score = words[0], 0.0
    for size in window:
        for start in range(0, max(1, len(words) - size + 1)):
            span = words[start:start + size]
            if len(span) < size:
                continue
            score = sum(idf.get(w.lower(), 0.0) for w in span)
            if score > best_score:
                best_score = score
                best_phrase = " ".join(span)
    return best_phrase
