from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models import AgentType
from backend.tools.registry import tool_registry


class ResearchAgent(BaseAgent):
    name = "ResearchAgent"
    agent_type = AgentType.RESEARCH

    def __init__(self) -> None:
        super().__init__()
        self.tools = tool_registry.get_schemas(["web_search", "fetch_url"])

    def get_system_prompt(self) -> str:
        return (
            "You are a research specialist agent. Your job is to find accurate, "
            "up-to-date information on any topic using web search and URL fetching.\n\n"
            "Guidelines:\n"
            "- Use the web_search tool to find relevant sources\n"
            "- Use fetch_url to read specific pages when needed\n"
            "- Synthesize findings into a clear, well-structured summary\n"
            "- Always cite your sources with URLs\n"
            "- Focus on factual accuracy and recency\n"
            "- If information is uncertain, say so explicitly"
        )
