from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field
from ulid import ULID


def new_id() -> str:
    return str(ULID())


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class AgentType(str, Enum):
    RESEARCH = "research"
    CODE = "code"
    DATA = "data"
    REPORT = "report"
    CRITIC = "critic"


class Task(BaseModel):
    id: str = Field(default_factory=new_id)
    description: str
    agent_type: AgentType
    dependencies: list[str] = Field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    input_data: dict[str, Any] = Field(default_factory=dict)
    output_data: dict[str, Any] | None = None


class ExecutionPlan(BaseModel):
    goal: str
    tasks: list[Task] = Field(default_factory=list)


class Artifact(BaseModel):
    kind: Literal["file", "chart", "code", "markdown", "table"]
    title: str
    content: str


class AgentOutput(BaseModel):
    agent_name: str
    task_id: str
    result: str
    artifacts: list[Artifact] = Field(default_factory=list)
    reasoning_trace: list[str] = Field(default_factory=list)
    tokens_used: int = 0
    duration_ms: int = 0


class SessionEvent(BaseModel):
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    id: str = Field(default_factory=new_id)
    goal: str
    status: TaskStatus = TaskStatus.PENDING
    plan: ExecutionPlan | None = None
    events: list[SessionEvent] = Field(default_factory=list)
    result: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
