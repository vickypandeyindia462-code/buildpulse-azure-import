from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_orchestrator_sme_api():
    r = client.get("/orchestrator/sme", params={"query": "Loan"})
    assert r.status_code == 200
    data = r.json()
    assert "results" in data
    assert any(item.get("owner_name") == "Asha Patel" for item in data["results"])
