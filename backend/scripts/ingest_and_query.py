from backend.agents.ingestion import run_sync as ingest_run
from backend.agents.rag import run_sync as rag_run
from backend.app.db.database import SessionLocal


def main():
    db = SessionLocal()
    try:
        doc = {"content": "BuildPulse is a CI/CD observability tool that tracks builds and highlights flaky tests."}
        ingest_res = ingest_run([doc], context={}, db=db)
        print('ingest:', ingest_res)

        # run a RAG query for a keyword
        rag_res = rag_run('flaky tests', context={}, db=db)
        print('rag:', rag_res)
    finally:
        db.close()


if __name__ == '__main__':
    main()
