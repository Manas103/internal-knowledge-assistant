from fastapi.testclient import TestClient

from assistant import app as app_module
from assistant.retrieval import BM25Index


def test_ask_endpoint_returns_a_citation(fixture_passages, monkeypatch):
    monkeypatch.setattr(app_module, "_index", lambda: BM25Index(fixture_passages))
    client = TestClient(app_module.app)
    resp = client.post("/ask", json={"question": "CXL memory pooling expansion device"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["cited_doc_id"] == "doc-a"
    assert body["cited_page_number"] == 2


def test_health_endpoint_reports_passage_count(fixture_passages, monkeypatch):
    monkeypatch.setattr(app_module, "_index", lambda: BM25Index(fixture_passages))
    client = TestClient(app_module.app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "passages": len(fixture_passages)}
