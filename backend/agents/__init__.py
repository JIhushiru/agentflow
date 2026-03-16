from backend.agents.base import BaseAgent
from backend.agents.code import CodeAgent
from backend.agents.critic import CriticAgent
from backend.agents.data import DataAgent
from backend.agents.report import ReportAgent
from backend.agents.research import ResearchAgent
from backend.models import AgentType

AGENT_REGISTRY: dict[AgentType, type[BaseAgent]] = {
    AgentType.RESEARCH: ResearchAgent,
    AgentType.CODE: CodeAgent,
    AgentType.DATA: DataAgent,
    AgentType.REPORT: ReportAgent,
    AgentType.CRITIC: CriticAgent,
}


def create_agent(agent_type: AgentType) -> BaseAgent:
    cls = AGENT_REGISTRY[agent_type]
    return cls()
