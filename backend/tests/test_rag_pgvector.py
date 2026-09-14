import os
import pytest
from backend.agents.ingestion import run_sync as ingest_run
from backend.agents.rag import run_sync as rag_run
from backend.app.db.database import SessionLocal
from backend.app import embeddings

DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./dev.db')

postgres_available = DATABASE_URL.startswith('postgres') or DATABASE_URL.startswith('postgresql')
provider_available = embeddings.get_embedding is not None and embeddings.provider is not None

skip_reason = 'Postgres+pgvector and embedding provider required for this test'

@pytest.mark.skipif(not (postgres_available and provider_available), reason=skip_reason)
def test_rag_pgvector_returns_results():
    db = SessionLocal()
    inserted_id = None
    try:
        doc = {"content": "Test RAG vector search for flaky tests unique-marker-xyz"}
        res = ingest_run([doc], context={}, db=db)
        assert res['processed_count'] == 1
        inserted_id = res['documents'][0]['id']

        out = rag_run('flaky tests unique-marker-xyz', context={}, db=db)
        assert out['method'] == 'pgvector'
        assert isinstance(out['results'], list)
        # ensure our inserted doc appears in results
        ids = [r['id'] for r in out['results']]
        assert inserted_id in ids
    finally:
        # cleanup
        try:
            from backend.app.db.models import Document
            if inserted_id:
                session = db
                doc = session.query(Document).get(inserted_id)
                if doc:
                    session.delete(doc)
                    session.commit()
        except Exception:
            pass
        db.close()
