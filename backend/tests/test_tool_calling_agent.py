from types import SimpleNamespace

import pytest

from backend.app.services.tool_calling_agent import AnthropicMessagesAgent, OpenAIResponsesAgent


class FakeResponses:
    def __init__(self):
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            tool_call = SimpleNamespace(type="function_call", name="get_service_ownership", arguments='{"service_id":"payments-api"}', call_id="call-1")
            return SimpleNamespace(id="response-1", output=[tool_call], output_text="")
        return SimpleNamespace(id="response-2", output=[], output_text="Payments API is owned by Dev Shah.")


def test_openai_agent_executes_tool_and_returns_final_answer():
    responses = FakeResponses()
    client = SimpleNamespace(responses=responses)
    executed = []
    agent = OpenAIResponsesAgent("key", "model", client=client)

    answer = agent.run("Who owns Payments API?", lambda name, args: executed.append((name, args)) or {"primary_owner": "Dev Shah"})

    assert answer == "Payments API is owned by Dev Shah."
    assert executed == [("get_service_ownership", {"service_id": "payments-api"})]
    assert responses.calls[1]["input"][0]["type"] == "function_call_output"


class FakeHTTPResponse:
    def __init__(self, body):
        self.body = body

    def raise_for_status(self):
        return None

    def json(self):
        return self.body


class FakeSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return FakeHTTPResponse({"content": [{"type": "tool_use", "id": "tool-1", "name": "get_service_ownership", "input": {"service_id": "payments-api"}}]})
        return FakeHTTPResponse({"content": [{"type": "text", "text": "Payments API is owned by Dev Shah."}]})


def test_anthropic_agent_returns_tool_result_to_model():
    session = FakeSession()
    agent = AnthropicMessagesAgent("key", "model", session=session)

    answer = agent.run("Who owns Payments API?", lambda name, args: {"primary_owner": "Dev Shah"})

    assert answer == "Payments API is owned by Dev Shah."
    second_messages = session.calls[1]["json"]["messages"]
    assert second_messages[-1]["content"][0]["type"] == "tool_result"


def test_openai_agent_stops_after_maximum_rounds():
    class LoopingResponses:
        def create(self, **kwargs):
            call = SimpleNamespace(type="function_call", name="get_service_ownership", arguments='{"service_id":"payments-api"}', call_id="same-call")
            return SimpleNamespace(id="response", output=[call], output_text="")

    agent = OpenAIResponsesAgent("key", "model", client=SimpleNamespace(responses=LoopingResponses()))
    with pytest.raises(RuntimeError, match="maximum"):
        agent.run("Loop", lambda name, args: {}, max_rounds=2)
