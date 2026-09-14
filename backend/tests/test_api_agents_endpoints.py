from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_ingest_endpoint():
    docs = [{"content": "API doc one"}, {"content": "API doc two"}]
    r = client.post("/ingest/", json=docs)
    assert r.status_code == 200
    data = r.json()
    assert data["processed_count"] == 2


def test_rag_endpoint():
    # ensure there is at least one document
    client.post("/ingest/", json=[{"content": "Loan service details"}])
    r = client.post("/rag/query", json={"query": "Loan", "use_db": True})
    assert r.status_code == 200
    data = r.json()
    assert data["query"] == "Loan"


def test_security_endpoint():
    r = client.post("/security/scan", json={"text": "call bob at bob@example.com"})
    assert r.status_code == 200
    data = r.json()
    assert "findings" in data
