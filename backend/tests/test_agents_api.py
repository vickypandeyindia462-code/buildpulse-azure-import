from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_agent_status_and_ci_analysis_endpoints():
    assert client.get("/api/agents/status").status_code == 200
    failures = client.get("/api/ci/failures")
    assert failures.status_code == 200
    assert failures.json()["items"]
    assert client.get("/api/ci/failures/demo-run-2431/analysis").status_code == 200
    assert client.get("/api/ci/runs").status_code == 200


def test_copilot_chat_endpoint():
    response = client.post("/api/copilot/chat", json={"question": "Why did Loan Service CI fail?"})
    assert response.status_code == 200
    assert response.json()["answer"]
    assert response.json()["security"]["redacted"] is False
    assert response.json()["audit_id"]
