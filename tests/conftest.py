# Unit tests (other than test_eval_gate_regressions.py and the benchmark scripts) run
# against a small synthetic fixture corpus, not the real downloaded PCIe/CXL documents, so
# this suite stays fast and fully offline; the real corpus is only required for the
# benchmark scripts and the eval-gate regression tests, which skip cleanly without it.
from __future__ import annotations

import pytest

from assistant.ingest import Passage

FIXTURE_PASSAGES = [
    Passage(doc_id="doc-a", title="Fixture Spec A", page_number=1, text="The retimer extends signal integrity across the PCIe link over long copper traces.", source_format="pdf"),
    Passage(doc_id="doc-a", title="Fixture Spec A", page_number=2, text="CXL memory pooling lets a host allocate capacity from a shared memory expansion device.", source_format="pdf"),
    Passage(doc_id="doc-b", title="Fixture Spec B", page_number=1, text="Flow control credits are returned to the transmitter once the receiver buffer drains.", source_format="pdf"),
    Passage(doc_id="doc-b", title="Fixture Spec B", page_number=2, text="A switch fans a single upstream port out to many downstream endpoints behind it.", source_format="pdf"),
    Passage(doc_id="doc-c", title="Fixture Spec C", page_number=1, text="Cache coherency protocols keep a host and device view of memory consistent under CXL.cache.", source_format="pdf"),
]


@pytest.fixture
def fixture_passages():
    return list(FIXTURE_PASSAGES)


@pytest.fixture
def pg_conn():
    """Real pgvector Postgres connection for assistant.vector_store and
    assistant.hybrid_answer tests; skips cleanly if unreachable, matching
    this portfolio's convention for a database not installed as an
    always-on service."""
    from assistant import vector_store

    if not vector_store.is_available():
        pytest.skip("pgvector Postgres unreachable")
    conn = vector_store.get_connection()
    vector_store.init_schema(conn)
    vector_store.reset(conn)
    yield conn
    conn.close()
