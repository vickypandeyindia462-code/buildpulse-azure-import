from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_get_existing_sme():
    r = client.get("/sme/Loan Service")
    assert r.status_code == 200
    data = r.json()
    assert data["owner_name"] == "Asha Patel"
    assert isinstance(data.get("expertise_tags"), list)


def test_get_missing_sme():
    r = client.get("/sme/Nonexistent System")
    assert r.status_code == 404
