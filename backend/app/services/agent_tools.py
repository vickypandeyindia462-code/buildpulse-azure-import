"""Provider-neutral, read-only tool contracts for the BuildPulse Copilot.

The schemas intentionally match common function-calling APIs without coupling
the domain layer to a specific model vendor.  Execution remains inside trusted
BuildPulse services; models receive only the declared inputs and safe outputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolContract:
    name: str
    description: str
    parameters: dict[str, Any]

    def as_function_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "strict": True,
            "parameters": self.parameters,
        }


READ_ONLY_TOOLS = (
    ToolContract(
        "get_ci_failure_analysis",
        "Load the sanitized evidence-backed analysis for one exact CI run.",
        {
            "type": "object",
            "properties": {"run_id": {"type": "string", "description": "Exact CI run identifier."}},
            "required": ["run_id"],
            "additionalProperties": False,
        },
    ),
    ToolContract(
        "get_pull_request_risk",
        "Load deterministic risk, ownership, dependencies, and incident matches for one pull request.",
        {
            "type": "object",
            "properties": {"pr_number": {"type": "integer", "minimum": 1}},
            "required": ["pr_number"],
            "additionalProperties": False,
        },
    ),
    ToolContract(
        "search_engineering_knowledge",
        "Search approved repository and Confluence knowledge for operational evidence.",
        {
            "type": "object",
            "properties": {
                "query": {"type": "string", "minLength": 2},
                "service_id": {"type": ["string", "null"]},
            },
            "required": ["query", "service_id"],
            "additionalProperties": False,
        },
    ),
    ToolContract(
        "get_service_ownership",
        "Load the accountable team, primary owner, and backup owner for one catalogued service.",
        {
            "type": "object",
            "properties": {"service_id": {"type": "string"}},
            "required": ["service_id"],
            "additionalProperties": False,
        },
    ),
)


def function_tool_schemas() -> list[dict[str, Any]]:
    return [tool.as_function_tool() for tool in READ_ONLY_TOOLS]


class BuildPulseToolExecutor:
    """Allowlisted bridge from model tool calls to trusted read-only services."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def execute(self, name: str, arguments: dict[str, Any]) -> Any:
        if name == "get_ci_failure_analysis":
            result = self.runtime.analyse_failure(str(arguments["run_id"]))
            return {
                key: result[key]
                for key in ("diagnosis", "recommended_fix", "failure_class", "confidence", "risk", "owners", "evidence")
            }
        if name == "get_pull_request_risk":
            return self.runtime.repository.pull_request_risk(int(arguments["pr_number"]))
        if name == "search_engineering_knowledge":
            return self.runtime._documents(arguments.get("service_id"), str(arguments["query"]))
        if name == "get_service_ownership":
            service = self.runtime.repository.service(str(arguments["service_id"]))
            return {
                "service_id": service["id"],
                "service_name": service["name"],
                "primary_owner": service["primary_owner"],
                "backup_owner": service["backup_owner"],
                "team": service["team"],
            }
        raise ValueError(f"Tool is not allowlisted: {name}")
