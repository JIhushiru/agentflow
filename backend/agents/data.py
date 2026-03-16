from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models import AgentType
from backend.tools.registry import tool_registry


class DataAgent(BaseAgent):
    name = "DataAgent"
    agent_type = AgentType.DATA

    def __init__(self) -> None:
        super().__init__()
        self.tools = tool_registry.get_schemas(["execute_python"])

    def get_system_prompt(self) -> str:
        return (
            "You are a data analysis specialist agent. You analyze data, compute "
            "statistics, and generate visualizations.\n\n"
            "Guidelines:\n"
            "- Use pandas for data manipulation and analysis\n"
            "- Use matplotlib or seaborn for chart generation\n"
            "- Use the execute_python tool to run your analysis code\n"
            "- Present findings with clear numerical summaries\n"
            "- When creating charts, save them and describe them textually\n"
            "- Handle missing data and edge cases gracefully"
        )
