import pytest

from backend.app.services.agent_runtime import AgentSettings, BuildPulseAgentRuntime
from backend.app.services.agent_tools import BuildPulseToolExecutor, READ_ONLY_TOOLS, function_tool_schemas
from backend.app.services.repository_intelligence import RepositoryIntelligence


def test_read_only_tool_contracts_are_strict_and_unique():
    schemas = function_tool_schemas()

    assert len(schemas) == len(READ_ONLY_TOOLS)
    assert len({schema["name"] for schema in schemas}) == len(schemas)
    assert all(schema["type"] == "function" for schema in schemas)
    assert all(schema["strict"] is True for schema in schemas)
    assert all(schema["parameters"]["additionalProperties"] is False for schema in schemas)


def test_tool_executor_returns_bounded_ownership_and_rejects_unknown_tools():
    runtime = BuildPulseAgentRuntime(repository=RepositoryIntelligence(), settings=AgentSettings())
    executor = BuildPulseToolExecutor(runtime)

    ownership = executor.execute("get_service_ownership", {"service_id": "payments-api"})

    assert ownership == {
        "service_id": "payments-api",
        "service_name": "Payments API",
        "primary_owner": "Dev Shah",
        "backup_owner": "Kavya Thomas",
        "team": "Payments Platform",
    }
    with pytest.raises(ValueError, match="not allowlisted"):
        executor.execute("delete_deployment", {})
