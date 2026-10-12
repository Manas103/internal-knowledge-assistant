from assistant.db import PassageRow, load_passages_into_db, make_session_factory


def test_load_passages_into_sqlite(fixture_passages):
    session = make_session_factory("sqlite:///:memory:")()
    load_passages_into_db(session, fixture_passages)
    rows = session.query(PassageRow).all()
    assert len(rows) == len(fixture_passages)
    assert {r.doc_id for r in rows} == {p.doc_id for p in fixture_passages}
