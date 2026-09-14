from backend.agents import ingestion, rag, security_check


def test_ingestion_agent():
    from backend.app.db.database import SessionLocal
    from backend.app.db.models import Base, Document

    # ensure tables exist
    Base.metadata.create_all(bind=SessionLocal().get_bind())

    docs = [{"content": "This is a test doc"}, {"content": "Another doc"}]
    db = SessionLocal()
    try:
        res = ingestion.run_sync(docs, {}, db)
        assert res["processed_count"] == 2
        assert len(res["documents"]) == 2
        # verify persisted
        stored = db.query(Document).count()
        assert stored >= 2
    finally:
        db.close()


def test_rag_agent():
    docs = [{"id": "1", "content": "The quick brown fox"}, {"id": "2", "content": "Loan service docs"}]
    res = rag.run_sync("Loan", {"documents": docs})
    assert res["query"] == "Loan"
    assert len(res["results"]) == 1


def test_security_check_agent():
    text = "Contact alice@example.com or use SSN 123-45-6789"
    res = security_check.run_sync(text, {})
    assert any(f["type"] == "EMAIL" for f in res["findings"]) 
    assert any(f["type"] == "SSN" for f in res["findings"]) 
