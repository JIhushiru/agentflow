from __future__ import annotations

from backend.agents.base import BaseAgent
from backend.models import AgentType
from backend.tools.registry import tool_registry


class CodeAgent(BaseAgent):
    name = "CodeAgent"
    agent_type = AgentType.CODE

    def __init__(self) -> None:
        super().__init__()
        self.tools = tool_registry.get_schemas(["execute_python"])

    def get_system_prompt(self) -> str:
        return (
            "You are a code specialist agent. You write, review, debug, and test code.\n\n"
            "Guidelines:\n"
            "- Write clean, well-structured Python code\n"
            "- Use the execute_python tool to run and test your code\n"
            "- Include error handling in your code\n"
            "- If writing a function, also write tests and run them\n"
            "- Explain your implementation approach briefly\n"
            "- Fix any errors that occur during execution"
        )
