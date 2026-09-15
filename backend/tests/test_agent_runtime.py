from backend.app.services.agent_runtime import AgentSettings, BuildPulseAgentRuntime
from backend.app.services.repository_intelligence import RepositoryIntelligence


def runtime():
    return BuildPulseAgentRuntime(repository=RepositoryIntelligence(), settings=AgentSettings(ci_source="fixture"))


def test_mock_runtime_reports_failed_ci_fixture():
    status = runtime().status()
    assert status["mode"] == "demo"
    failures = runtime().failed_runs()
    assert failures[0]["conclusion"] == "failure"


def test_failure_analysis_has_safe_fix_and_agent_trace():
    result = runtime().analyse_failure("demo-run-2431")
    assert "safe value (30)" in result["recommended_fix"]
    assert len(result["agent_trace"]) == 4
    assert result["failure_class"] == "configuration"
    assert result["confidence"]["score"] >= 80
    assert result["owners"]["primary"] == "Meera Kulkarni"
    assert result["audit_id"]


def test_mock_chat_returns_sources():
    result = runtime().chat("Why did the Loan Service CI build fail?")
    assert result["mode"] == "demo"
    assert result["sources"]


def test_chat_redacts_sensitive_input_before_provider_use():
    result = runtime().chat("Why did the loan build fail? Contact dev@example.com")
    assert result["security"] == {"findings_count": 1, "redacted": True}
    assert "dev@example.com" not in result["answer"]
    assert result["audit_id"]


def test_gemini_provider_is_ready_only_with_key_and_model():
    configured = AgentSettings(provider="gemini", gemini_api_key="test-key", gemini_model="test-model")
    missing_key = AgentSettings(provider="gemini", gemini_model="test-model")
    assert configured.live_ready is True
    assert missing_key.live_ready is False


def test_unrelated_question_refuses_without_kb_evidence():
    result = runtime().chat("Explain quantum astronomy nebula")
    assert "does not contain enough evidence" in result["answer"]
    assert result["sources"] == []
