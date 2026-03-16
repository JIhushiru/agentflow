from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models import AgentType


class ReportAgent(BaseAgent):
    name = "ReportAgent"
    agent_type = AgentType.REPORT

    def __init__(self) -> None:
        super().__init__()
        self.tools = []

    def get_system_prompt(self) -> str:
        return (
            "You are a report synthesis specialist agent. You take findings from other "
            "agents and produce clear, well-structured reports.\n\n"
            "Guidelines:\n"
            "- Organize information with clear headings and sections\n"
            "- Use markdown formatting for structure\n"
            "- Highlight key findings and insights prominently\n"
            "- Include executive summary at the top\n"
            "- Reference data and sources from input context\n"
            "- Keep language professional and concise\n"
            "- End with conclusions and recommendations when appropriate"
        )
