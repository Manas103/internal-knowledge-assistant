# Reciprocal rank fusion (Cormack, Clarke & Buettcher, "Reciprocal Rank
# Fusion Outperforms Condorcet and Individual Rank Learning Methods", 2009):
# combines two independently-ranked result lists by rank position alone, not
# by trying to make BM25 scores and cosine distances commensurate, which
# they are not (one is unbounded and higher-is-better, the other is bounded
# in [0, 2] and lower-is-better).
from __future__ import annotations

from dataclasses import dataclass

K = 60  # the constant from the paper; large enough that rank 1 vs rank 2 is a small
         # relative difference, so one list's top hit does not automatically dominate


@dataclass(frozen=True)
class FusedResult:
    doc_id: str
    page_number: int
    score: float
    bm25_rank: int | None
    dense_rank: int | None


def fuse(
    bm25_ranked: list[tuple[str, int]],
    dense_ranked: list[tuple[str, int]],
    k: int = K,
    bm25_weight: float = 1.0,
    dense_weight: float = 1.0,
) -> list[FusedResult]:
    """Both inputs are already-ranked lists of (doc_id, page_number), best
    first. A passage appearing in only one list still gets a fused score
    from that list alone; the other rank is reported as None in the result,
    not silently treated as missing-from-contention.

    `bm25_weight` / `dense_weight` are not part of the original Cormack et
    al. formula, which weights both lists equally; they exist because this
    project's dense signal (feature-hashed TF-IDF, not a trained embedding)
    turned out measurably weaker than BM25 on this corpus (see the README's
    Findings): unweighted fusion dropped citation accuracy by demoting BM25's
    own correct top hit more often than it rescued a BM25 miss. Giving BM25
    a larger weight is a standard, documented mitigation for exactly this
    failure mode in hybrid search, not a parameter tuned until a target
    number appeared."""
    bm25_rank_of = {key: i + 1 for i, key in enumerate(bm25_ranked)}
    dense_rank_of = {key: i + 1 for i, key in enumerate(dense_ranked)}

    keys = set(bm25_rank_of) | set(dense_rank_of)
    results = []
    for key in keys:
        br = bm25_rank_of.get(key)
        dr = dense_rank_of.get(key)
        score = (bm25_weight / (k + br) if br else 0.0) + (dense_weight / (k + dr) if dr else 0.0)
        results.append(FusedResult(doc_id=key[0], page_number=key[1], score=score, bm25_rank=br, dense_rank=dr))

    results.sort(key=lambda r: (-r.score, r.doc_id, r.page_number))
    return results
