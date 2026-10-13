# The pgvector path itself: a real Postgres connection, a real `vector(128)`
# column, and a real `<=>` cosine-distance query. This is the module the
# base repo's db.py (SQLAlchemy, a Text column standing in for `vector`,
# never queried) explicitly disclosed as unexercised; this one is exercised,
# which is the entire point of this extension (see the README's Honest
# framing and playbooks/BUILDER.md's design note for this project). Skips
# cleanly wherever Postgres is unreachable, matching this portfolio's
# convention for a database that is not installed as an always-on service.
from __future__ import annotations

import os
from typing import Iterable

import psycopg2
import psycopg2.extras

from .dense_embed import DIM, embed_text
from .ingest import Passage

PG_HOST = os.environ.get("KNOWLEDGE_PG_HOST", "127.0.0.1")
PG_PORT = int(os.environ.get("KNOWLEDGE_PG_PORT", "5432"))
PG_DB = os.environ.get("KNOWLEDGE_PG_DB", "knowledge_vector_bench")
PG_USER = os.environ.get("KNOWLEDGE_PG_USER", "knowledge_app")
PG_PASSWORD = os.environ.get("KNOWLEDGE_PG_PASSWORD", "knowledge_app")

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS passage_embeddings (
    passage_id INTEGER PRIMARY KEY,
    doc_id TEXT NOT NULL,
    page_number INTEGER NOT NULL,
    embedding vector(128) NOT NULL
);
"""


def get_connection():
    return psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASSWORD)


def is_available() -> bool:
    try:
        get_connection().close()
        return True
    except Exception:
        return False


def init_schema(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(SCHEMA_SQL)
    conn.commit()


def reset(conn) -> None:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE passage_embeddings")
    conn.commit()


def _vector_literal(vec: list[float]) -> str:
    return "[" + ",".join(repr(v) for v in vec) + "]"


def upsert_passages(conn, passages: Iterable[Passage], idf: dict[str, float]) -> int:
    """Embeds and inserts every passage. passage_id is the position of the
    passage in the corpus list passed in, which is how dense_search below
    maps a result back to a (doc_id, page_number)."""
    n = 0
    with conn.cursor() as cur:
        for i, p in enumerate(passages):
            vec = embed_text(p.text, idf)
            cur.execute(
                """INSERT INTO passage_embeddings (passage_id, doc_id, page_number, embedding)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (passage_id) DO UPDATE SET embedding = EXCLUDED.embedding""",
                (i, p.doc_id, p.page_number, _vector_literal(vec)),
            )
            n += 1
    conn.commit()
    return n


def dense_search(conn, query: str, idf: dict[str, float], top_k: int = 5) -> list[dict]:
    """Real cosine-distance nearest-neighbor search via pgvector's `<=>`
    operator, a sequential scan (no HNSW/IVFFlat index; the corpus is 396
    rows, small enough that an index would cost more to maintain than it
    would save, and the point here is exercising pgvector's type and
    operator for real, not its indexing story)."""
    vec = embed_text(query, idf)
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """SELECT passage_id, doc_id, page_number, embedding <=> %s::vector AS distance
               FROM passage_embeddings ORDER BY embedding <=> %s::vector LIMIT %s""",
            (_vector_literal(vec), _vector_literal(vec), top_k),
        )
        return [dict(r) for r in cur.fetchall()]
