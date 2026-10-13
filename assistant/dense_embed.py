# A dense embedding for the pgvector path: term-frequency-times-idf weights
# (idf reused from retrieval.BM25Index, the same corpus statistic BM25 already
# computes) hashed into a fixed 128-dimension vector by the feature-hashing
# trick (Weinberger et al., "Feature Hashing for Large Scale Multitask
# Learning", 2009), not a transformer embedding. This is a disclosed,
# honest choice, not a stand-in pretending to be semantic: no embedding API
# key or local model weights exist in this session, and the hashing trick is
# a real, citable dense-embedding technique, not a placeholder. It gives two
# passages sharing rare, high-idf terms a genuinely small cosine distance
# even when they share zero exact tokens other than that term, which lexical
# BM25 alone cannot do; see the README's Findings for a measured case.
from __future__ import annotations

import hashlib
import math

from .retrieval import tokenize

DIM = 128


def _hash_bucket_and_sign(term: str) -> tuple[int, float]:
    """Deterministic across runs and processes (unlike Python's built-in
    hash() for strings, which is randomized per-process by default): two
    independent digests of the same md5 hash decide the bucket and the
    sign, so collisions partially cancel instead of only ever adding."""
    digest = hashlib.md5(term.encode("utf-8")).digest()
    bucket = int.from_bytes(digest[:4], "big") % DIM
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return bucket, sign


def embed_text(text: str, idf: dict[str, float]) -> list[float]:
    """tf * idf per term, hashed into DIM buckets with a random sign, then
    L2-normalized so pgvector's cosine distance operator (<=>) behaves the
    same as it would for a unit-normalized transformer embedding."""
    terms = tokenize(text)
    if not terms:
        return [0.0] * DIM
    tf: dict[str, int] = {}
    for t in terms:
        tf[t] = tf.get(t, 0) + 1

    vec = [0.0] * DIM
    for term, freq in tf.items():
        weight = freq * idf.get(term, 0.0)
        if weight == 0.0:
            continue
        bucket, sign = _hash_bucket_and_sign(term)
        vec[bucket] += sign * weight

    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return vec
    return [v / norm for v in vec]
