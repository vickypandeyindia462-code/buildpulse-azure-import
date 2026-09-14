from backend.orchestrator import orchestrator


def test_sme_discovery_orchestrator():
    resp = orchestrator.run_sme_discovery("Loan")
    assert "results" in resp
    assert any(r["owner_name"] == "Asha Patel" for r in resp["results"])
