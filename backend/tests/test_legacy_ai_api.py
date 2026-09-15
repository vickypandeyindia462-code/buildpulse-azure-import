from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_legacy_ai_route_uses_canonical_copilot_contract():
    response = client.post("/ai/chat", json={"query": "Why did Loan Service CI fail?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"]
    assert body["audit_id"]
    assert "/api/copilot/chat" in body["deprecated"]


def test_legacy_ai_route_preserves_validation_status():
    response = client.post("/ai/chat", json={"query": ""})
    assert response.status_code == 422
