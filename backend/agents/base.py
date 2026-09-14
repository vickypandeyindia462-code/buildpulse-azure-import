from typing import Any, Dict, Protocol, Optional


class Tool(Protocol):
    """A minimal protocol for tools an agent might call."""

    def run(self, *args, **kwargs) -> Any:
        ...


class AgentProtocol(Protocol):
    """Protocol for agents. Prefer implementing an async `run` coroutine."""

    name: str

    async def run(self, query: str, context: Dict[str, Any], db, tools: Optional[Dict[str, Tool]] = None) -> Dict[str, Any]:
        ...

