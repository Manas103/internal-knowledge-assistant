# FastAPI wrapper around answer_question; the frontend (frontend/src) talks to this.
from __future__ import annotations

from functools import lru_cache

from fastapi import FastAPI
from pydantic import BaseModel

from .answer import answer_question
from .ingest import load_corpus
from .retrieval import BM25Index

app = FastAPI(title="Internal Knowledge Assistant")


@lru_cache(maxsize=1)
def _index() -> BM25Index:
    return BM25Index(load_corpus())


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer_text: str
    cited_doc_id: str
    cited_page_number: int
    confidence: float


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "passages": len(_index().passages)}


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    draft = answer_question(req.question, _index())
    return AskResponse(
        answer_text=draft.answer_text,
        cited_doc_id=draft.cited_doc_id,
        cited_page_number=draft.cited_page_number,
        confidence=draft.confidence,
    )
