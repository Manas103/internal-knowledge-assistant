# PostgreSQL + pgvector schema for the corpus and its session/adoption instrumentation.
# Plain SQLAlchemy so a real `postgresql+psycopg://...` DSN works unchanged; this session
# only ever runs against sqlite:///:memory:, matching this portfolio's convention for a
# database that is not installed as a running service on this machine. The pgvector
# EMBEDDING column is declared as Text (a JSON-encoded float list) rather than the real
# `vector` type, since no embedding model is exercised this session either; retrieval
# itself runs on the lexical BM25Index in retrieval.py, not on this column.
from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool


class Base(DeclarativeBase):
    pass


class PassageRow(Base):
    __tablename__ = "passages"
    id = Column(Integer, primary_key=True)
    doc_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    page_number = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Text, nullable=True)  # pgvector column target, unused this session


class SessionRecord(Base):
    """One row per simulated session: the question asked, the citation and draft the
    assistant produced, and the two adoption outcomes this project is instrumented for."""

    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    question = Column(Text, nullable=False)
    expected_doc_id = Column(String, nullable=False)
    expected_page_number = Column(Integer, nullable=False)
    cited_doc_id = Column(String, nullable=True)
    cited_page_number = Column(Integer, nullable=True)
    cited_supporting_passage = Column(Boolean, nullable=False)
    sent_unedited = Column(Boolean, nullable=False)
    confidence = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def make_session_factory(database_url: str | None = None) -> sessionmaker:
    url = database_url or os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    if url == "sqlite:///:memory:":
        engine = create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    else:
        engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


def load_passages_into_db(session: Session, passages) -> None:
    for p in passages:
        session.add(PassageRow(doc_id=p.doc_id, title=p.title, page_number=p.page_number, text=p.text))
    session.commit()
