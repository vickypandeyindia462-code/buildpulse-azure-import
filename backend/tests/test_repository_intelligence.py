from backend.app.services.repository_intelligence import RepositoryIntelligence


def test_portfolio_overview_uses_synthetic_service_repository():
    overview = RepositoryIntelligence().portfolio_overview()

    assert overview["service_count"] == 4
    assert overview["open_change_count"] == 3
    assert any(change["service"] == "Loan Service" for change in overview["changes"])


def test_loan_pr_risk_is_explainable():
    result = RepositoryIntelligence().pull_request_risk(3)

    assert result["service"] == "Loan Service"
    assert result["risk_level"] == "high"
    assert "payments-api" in result["affected_dependencies"]
    assert any(driver["points"] > 0 for driver in result["drivers"])


def test_secret_in_pr_diff_blocks_merge(monkeypatch):
    repository = RepositoryIntelligence()
    monkeypatch.setattr(repository, "_git_diff_files", lambda branch: ["identity-service/src/demo_config.py"])
    monkeypatch.setattr(repository, "_git_diff_text", lambda branch: '+API_KEY="sk-synthetic-buildpulse-demo-1234567890"')

    result = repository.assess_change("feature/identity-synthetic-secret", pr_number=99)

    assert result["security"]["secret_detected"] is True
    assert result["risk_level"] == "high"
    assert any(driver["factor"] == "Secret detected in changed content" for driver in result["drivers"])
