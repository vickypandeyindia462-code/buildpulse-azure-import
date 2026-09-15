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
