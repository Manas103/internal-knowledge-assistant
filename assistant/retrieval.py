# A hand-rolled BM25 index over the real passage corpus. PostgreSQL + pgvector is this
# project's named stack and gateway/state-style schema for it exists in assistant/db.py,
# but no embedding model or live Postgres is exercised this session (no network API key,
# no Postgres running as a service on this machine); BM25 is lexical, not a stand-in that
# pretends to be semantic search, and every number in this project's README is measured
# against it, not against pgvector.
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .ingest import Passage

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    "a an the of to in and is are was were be been being for on with as by at from this "
    "that these those it its into or not no if then than so such can may will would "
    "should could has have had do does did but about which who what when where how".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


@dataclass(frozen=True)
class ScoredPassage:
    passage: Passage
    score: float


class BM25Index:
    """Standard Robertson/Sparck-Jones BM25 (k1=1.5, b=0.75), built once over the whole
    corpus. No library dependency: the formula is 15 lines, and hand-rolling it keeps the
    scoring function auditable against the reference definition in search()'s docstring."""

    K1 = 1.5
    B = 0.75

    def __init__(self, passages: list[Passage]) -> None:
        self.passages = passages
        self._doc_tokens: list[list[str]] = [tokenize(p.text) for p in passages]
        self._doc_len = [len(toks) for toks in self._doc_tokens]
        self._avg_len = sum(self._doc_len) / len(self._doc_len) if self._doc_len else 0.0
        self._term_freqs: list[Counter] = [Counter(toks) for toks in self._doc_tokens]
        doc_freq: Counter = Counter()
        for tf in self._term_freqs:
            doc_freq.update(tf.keys())
        n = len(passages)
        self._idf: dict[str, float] = {
            term: math.log(1 + (n - df + 0.5) / (df + 0.5)) for term, df in doc_freq.items()
        }

    @property
    def idf(self) -> dict[str, float]:
        return self._idf

    def search(self, query: str, top_k: int = 5) -> list[ScoredPassage]:
        """score(doc, query) = sum over query terms t of
        idf(t) * tf(t, doc) * (k1 + 1) / (tf(t, doc) + k1 * (1 - b + b * len(doc) / avg_len))
        """
        q_terms = tokenize(query)
        scores = [0.0] * len(self.passages)
        for i, tf in enumerate(self._term_freqs):
            doc_len = self._doc_len[i]
            norm = self.K1 * (1 - self.B + self.B * (doc_len / self._avg_len if self._avg_len else 1))
            total = 0.0
            for term in q_terms:
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                idf = self._idf.get(term, 0.0)
                total += idf * freq * (self.K1 + 1) / (freq + norm)
            scores[i] = total
        ranked = sorted(range(len(self.passages)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [ScoredPassage(self.passages[i], scores[i]) for i in ranked]
