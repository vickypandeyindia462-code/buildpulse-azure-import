import io
import zipfile

from backend.app.services.ci_intelligence import (
    GitHubActionsClient,
    classify_failure,
    extract_log_text,
    service_for_job,
)


class FakeResponse:
    def __init__(self, payload=None, content=b"", content_type="application/json", status_code=200):
        self._payload = payload or {}
        self.content = content
        self.headers = {"content-type": content_type}
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(self.status_code)


class FakeSession:
    def __init__(self, responses):
        self.responses = iter(responses)

    def get(self, *args, **kwargs):
        return next(self.responses)


def test_failed_job_collection_maps_service_and_step():
    runs = FakeResponse({"workflow_runs": [{
        "id": 7, "name": "Service CI", "status": "completed", "conclusion": "failure",
        "run_started_at": "2026-09-14T10:00:00Z", "html_url": "https://example/run",
        "head_branch": "feature/loan-pool-capacity", "pull_requests": [{"number": 3}],
    }]})
    jobs = FakeResponse({"jobs": [{
        "id": 9, "name": "Loan Service tests", "conclusion": "failure",
        "html_url": "https://example/job", "steps": [{"name": "pytest", "conclusion": "failure"}],
    }]})
    client = GitHubActionsClient("owner", "repo", "token", FakeSession([runs, jobs]))
    failure = client.failed_runs()[0]
    assert failure["service_id"] == "loan-service"
    assert failure["failed_step"] == "pytest"
    assert failure["log_available"] is True


def test_job_log_zip_is_bounded_and_redacted():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("job.txt", "FAILED test_pool\ncontact dev@example.com\ntoken sk-abcdefghijklmnopqrstuvwxyz123456")
    response = FakeResponse(content=buffer.getvalue(), content_type="application/zip")
    client = GitHubActionsClient("owner", "repo", "token", FakeSession([response]))
    result = client.sanitized_job_log("9")
    assert result["available"] is True
    assert result["redacted"] is True
    assert "dev@example.com" not in result["excerpt"]
    assert "abcdefghijklmnopqrstuvwxyz" not in result["excerpt"]


def test_failure_classifier_is_explainable():
    result = classify_failure("AssertionError: expected 30, got 45", "Run pytest")
    assert result["class"] == "test"
    assert result["confidence"]["score"] >= 80
    assert result["confidence"]["drivers"]


def test_public_access_does_not_claim_job_logs_are_available():
    assert service_for_job("API Gateway contract tests") == "api-gateway"
    client = GitHubActionsClient("owner", "repo")
    assert client.sanitized_job_log("9")["available"] is False
