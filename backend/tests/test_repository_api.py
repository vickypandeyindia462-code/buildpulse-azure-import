from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_services_endpoint_returns_catalog():
    response = client.get("/api/services")

    assert response.status_code == 200
    assert response.json()["total"] == 4


def test_pull_request_risk_endpoint_returns_loan_analysis():
    response = client.get("/api/pull-requests/3/risk")

    assert response.status_code == 200
    assert response.json()["service"] == "Loan Service"
