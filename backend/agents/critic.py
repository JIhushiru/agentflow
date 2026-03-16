from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models import AgentType


class CriticAgent(BaseAgent):
    name = "CriticAgent"
    agent_type = AgentType.CRITIC

    def __init__(self) -> None:
        super().__init__()
        self.tools = []

    def get_system_prompt(self) -> str:
        return (
            "You are a critic agent. You review outputs from other agents for quality, "
            "accuracy, and completeness.\n\n"
            "Guidelines:\n"
            "- Check factual accuracy and logical consistency\n"
            "- Identify gaps, errors, or unsupported claims\n"
            "- Evaluate code for bugs, security issues, and best practices\n"
            "- Rate the output quality (excellent/good/needs improvement)\n"
            "- Provide specific, actionable feedback\n"
            "- Be constructive but thorough"
        )
