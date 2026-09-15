from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_buildpulse_web_shell_is_served_at_root():
    response = client.get("/")

    assert response.status_code == 200
    assert "BuildPulse" in response.text
    assert 'href="styles.css"' in response.text
    assert 'id="ci-failure-card"' in response.text
    assert 'id="ci-failures"' in response.text
    assert 'id="ci-job-detail" hidden' in response.text
    assert 'id="jira-readiness"' in response.text
    assert 'id="jira-attention"' in response.text
    assert 'id="pr-list"' in response.text
    assert 'id="pr-risk-detail" hidden' in response.text
    assert 'id="knowledge-results"' in response.text
    assert 'id="knowledge-search"' in response.text
    assert 'id="ci-service-filter"' in response.text


def test_buildpulse_web_assets_are_served():
    response = client.get("/styles.css")

    assert response.status_code == 200
    assert "--nav" in response.text
