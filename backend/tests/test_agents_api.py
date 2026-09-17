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


def test_copilot_accepts_recent_conversation_history():
    response = client.post("/api/copilot/chat", json={
        "question": "Who is the backup owner?",
        "history": [{"role": "user", "content": "Tell me about the Payments API"}],
    })
    assert response.status_code == 200
    assert response.json()["service_id"] == "payments-api"


def test_copilot_uses_structured_ci_page_context_without_reasking_for_job():
    response = client.post("/api/copilot/chat", json={
        "question": "Explain this failed job and give me the safest verified remediation steps.",
        "context": {
            "type": "ci_failure",
            "run_id": "demo-run-2431",
            "service_id": "loan-service",
            "job_name": "loan-service-tests",
        },
    })

    assert response.status_code == 200
    body = response.json()
    assert body["needs_clarification"] is False
    assert body["service_id"] == "loan-service"
    assert body["sources"][0]["title"] == "CI analysis — loan-service-tests"
