from backend.app.services.agent_runtime import AgentSettings, BuildPulseAgentRuntime, GeminiProvider
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
    assert "BuildPulse mock analysis" not in result["answer"]
    assert "[Source " in result["answer"]


def test_greeting_is_natural_and_does_not_trigger_retrieval():
    for greeting in ("Hello", "Hello.", "Hi!", "  good morning!  "):
        result = runtime().chat(greeting)
        assert result["answer"].startswith("Hello!")
        assert "BuildPulse mock analysis" not in result["answer"]
        assert result["sources"] == []


def test_social_follow_up_does_not_trigger_knowledge_retrieval():
    result = runtime().chat("How are you?", history=[{"role": "assistant", "content": "Hello!"}])
    assert result["answer"].startswith("I’m ready to help")
    assert result["sources"] == []


def test_live_gemini_handles_social_conversation(monkeypatch):
    configured = AgentSettings(provider="gemini", gemini_api_key="test-key", gemini_model="test-model")
    active_runtime = BuildPulseAgentRuntime(repository=RepositoryIntelligence(), settings=configured)
    monkeypatch.setattr(GeminiProvider, "complete", lambda self, **kwargs: "I’m doing well—what are we investigating today?")

    result = active_runtime.chat("How are you?")

    assert result["answer"].startswith("I’m doing well")
    assert result["provider_used"] == "gemini"
    assert result["sources"] == []


def test_service_owner_answer_is_grounded_in_catalog():
    result = runtime().chat("Who owns the Payments API?")
    assert "Dev Shah" in result["answer"]
    assert result["sources"][0]["title"] == "Service catalog — Payments API"


def test_live_provider_failure_returns_grounded_local_answer(monkeypatch):
    configured = AgentSettings(provider="gemini", gemini_api_key="test-key", gemini_model="test-model")
    active_runtime = BuildPulseAgentRuntime(repository=RepositoryIntelligence(), settings=configured)
    monkeypatch.setattr(GeminiProvider, "complete", lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError("temporary outage")))

    result = active_runtime.chat("Who owns the Payments API?")

    assert "Dev Shah" in result["answer"]
    assert result["provider_fallback"] == "RuntimeError"
    assert result["sources"]


def test_vague_request_asks_for_requirement_details():
    result = runtime().chat("I have an issue")
    assert result["needs_clarification"] is True
    assert "Which service" in result["answer"]
    assert result["sources"] == []


def test_follow_up_resolves_service_from_conversation_history():
    result = runtime().chat(
        "Who is the backup owner?",
        history=[{"role": "user", "content": "Tell me about the Payments API"}],
    )
    assert result["service_id"] == "payments-api"
    assert "Kavya Thomas" in result["answer"]


def test_follow_up_prefers_most_recent_service_over_clarification_list():
    result = runtime().chat(
        "Who owns it?",
        history=[
            {"role": "assistant", "content": "Which service: Loan Service, Payments API, API Gateway, or Identity Service?"},
            {"role": "user", "content": "The Payments API is timing out"},
        ],
    )
    assert result["service_id"] == "payments-api"
    assert "Dev Shah" in result["answer"]


def test_unknown_owner_target_does_not_leak_previous_service_context():
    result = runtime().chat("Who owns Ferrari?", service_id="loan-service")
    assert result["needs_clarification"] is True
    assert "don’t have a BuildPulse service" in result["answer"]
    assert "Meera Kulkarni" not in result["answer"]
    assert result["sources"] == []


def test_owner_request_uses_only_catalog_evidence():
    result = runtime().chat("Who owns the Payments API?")
    assert len(result["sources"]) == 1
    assert result["sources"][0]["title"] == "Service catalog — Payments API"
    assert "Dev Shah" in result["answer"]
    assert "direct email" in result["answer"]


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
