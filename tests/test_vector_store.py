from assistant.dense_embed import DIM
from assistant.retrieval import BM25Index
from assistant.vector_store import dense_search, upsert_passages


def test_upsert_and_dense_search_real_pgvector(pg_conn, fixture_passages):
    index = BM25Index(fixture_passages)
    n = upsert_passages(pg_conn, fixture_passages, index.idf)
    assert n == len(fixture_passages)

    results = dense_search(pg_conn, "CXL memory pooling and cache coherency", index.idf, top_k=3)
    assert len(results) == 3
    doc_ids = {(r["doc_id"], r["page_number"]) for r in results}
    # both CXL-themed passages (doc-a page 2, doc-c page 1) should outrank the
    # PCIe retimer passage on cosine distance to this CXL-themed query
    assert ("doc-a", 2) in doc_ids
    assert ("doc-c", 1) in doc_ids
    for r in results:
        assert 0.0 <= r["distance"] <= 2.0


def test_dense_search_is_a_real_vector_column_not_a_placeholder(pg_conn, fixture_passages):
    index = BM25Index(fixture_passages)
    upsert_passages(pg_conn, fixture_passages, index.idf)
    with pg_conn.cursor() as cur:
        cur.execute("SELECT pg_typeof(embedding)::text FROM passage_embeddings LIMIT 1")
        assert cur.fetchone()[0] == "vector"
        cur.execute("SELECT array_length(embedding::real[], 1) FROM passage_embeddings LIMIT 1")
        assert cur.fetchone()[0] == DIM
