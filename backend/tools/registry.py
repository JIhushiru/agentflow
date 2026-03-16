from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    """Base class for all tools available to agents."""

    name: str
    description: str

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """Return the JSON schema for this tool's parameters (Claude tool_use format)."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> str:
        """Execute the tool and return a string result."""
        ...

    def to_claude_tool(self) -> dict[str, Any]:
        """Return the full tool definition for Claude's tool_use API."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.get_schema(),
        }


class ToolRegistry:
    """Central registry of tools that agents can invoke."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[Tool]:
        return list(self._tools.values())

    def get_schemas(self, tool_names: list[str] | None = None) -> list[dict[str, Any]]:
        """Return Claude tool_use schemas for the specified tools (or all if None)."""
        tools = self._tools.values() if tool_names is None else [
            self._tools[n] for n in tool_names if n in self._tools
        ]
        return [t.to_claude_tool() for t in tools]


# Global singleton
tool_registry = ToolRegistry()
