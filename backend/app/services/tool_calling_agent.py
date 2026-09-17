"""Bounded provider adapters for BuildPulse's read-only agent tools."""

from __future__ import annotations

import json
from typing import Any, Callable

import requests

from .agent_tools import function_tool_schemas


SYSTEM_PROMPT = (
    "You are BuildPulse Copilot. Use the available read-only tools for factual engineering questions. "
    "Never invent operational facts. Cite tool evidence by its title when available, state uncertainty, "
    "and recommend safe reversible actions. Keep the answer concise and directly actionable."
)


class OpenAIResponsesAgent:
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "", client: Any = None) -> None:
        if client is None:
            from openai import OpenAI
            options: dict[str, str] = {"api_key": api_key}
            if base_url:
                options["base_url"] = base_url
            client = OpenAI(**options)
        self.client = client
        self.model = model

    def run(self, question: str, execute: Callable[[str, dict[str, Any]], Any], max_rounds: int = 4) -> str:
        response = self.client.responses.create(
            model=self.model, instructions=SYSTEM_PROMPT, input=question,
            tools=function_tool_schemas(), parallel_tool_calls=False, max_output_tokens=700,
        )
        for _ in range(max_rounds):
            calls = [item for item in response.output if getattr(item, "type", None) == "function_call"]
            if not calls:
                return (response.output_text or "No answer returned.").strip()
            outputs = []
            for call in calls:
                arguments = json.loads(call.arguments or "{}")
                result = execute(call.name, arguments)
                outputs.append({"type": "function_call_output", "call_id": call.call_id, "output": json.dumps(result, default=str)[:24000]})
            response = self.client.responses.create(
                model=self.model, instructions=SYSTEM_PROMPT, previous_response_id=response.id,
                input=outputs, tools=function_tool_schemas(), parallel_tool_calls=False, max_output_tokens=700,
            )
        raise RuntimeError("Agent exceeded the maximum tool-call rounds")


class AnthropicMessagesAgent:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com", session: Any = requests) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.session = session

    @staticmethod
    def _tools() -> list[dict[str, Any]]:
        return [{"name": tool["name"], "description": tool["description"], "input_schema": tool["parameters"]} for tool in function_tool_schemas()]

    def _create(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        response = self.session.post(
            f"{self.base_url}/v1/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": self.model, "system": SYSTEM_PROMPT, "messages": messages, "tools": self._tools(), "max_tokens": 700, "temperature": 0.1},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def run(self, question: str, execute: Callable[[str, dict[str, Any]], Any], max_rounds: int = 4) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
        for _ in range(max_rounds):
            response = self._create(messages)
            content = response.get("content", [])
            calls = [block for block in content if block.get("type") == "tool_use"]
            if not calls:
                answer = "\n".join(block.get("text", "") for block in content if block.get("type") == "text").strip()
                return answer or "No answer returned."
            messages.append({"role": "assistant", "content": content})
            results = []
            for call in calls:
                result = execute(call["name"], call.get("input", {}))
                results.append({"type": "tool_result", "tool_use_id": call["id"], "content": json.dumps(result, default=str)[:24000]})
            messages.append({"role": "user", "content": results})
        raise RuntimeError("Agent exceeded the maximum tool-call rounds")
