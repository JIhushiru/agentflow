from __future__ import annotations

import json
from typing import Any

from loguru import logger

from backend.config import settings
from backend.llm import llm_client
from backend.models import AgentType, ExecutionPlan, Task, new_id

PLANNER_SYSTEM_PROMPT = """\
You are a task planning agent. Given a user's high-level goal, you decompose it into \
a directed acyclic graph (DAG) of subtasks that specialist agents can execute.

Available agent types:
- research: Web research and information gathering
- code: Writing, reviewing, debugging, and testing code
- data: Data analysis, statistics, and chart generation
- report: Synthesizing findings into well-structured reports
- critic: Reviewing other agents' outputs for quality

Rules:
1. Each task must have a unique ID (use short names like "t1", "t2", etc.)
2. Tasks can depend on other tasks via the "dependencies" field (list of task IDs)
3. Dependencies form a DAG — no cycles allowed
4. Independent tasks will be executed in parallel
5. Keep the plan focused — typically 2-6 tasks
6. The final task should synthesize or report results

Respond with ONLY a JSON object in this exact format:
{
  "tasks": [
    {
      "id": "t1",
      "description": "What this task should accomplish",
      "agent_type": "research",
      "dependencies": [],
      "input_data": {}
    },
    {
      "id": "t2",
      "description": "Analyze the research findings",
      "agent_type": "data",
      "dependencies": ["t1"],
      "input_data": {}
    }
  ]
}
"""


class Planner:
    async def create_plan(self, goal: str) -> ExecutionPlan:
        logger.info(f"Planning for goal: {goal}")

        response = await llm_client.chat(
            model=settings.planner_model,
            system=PLANNER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Goal: {goal}"}],
            max_tokens=2048,
        )

        plan_data = self._parse_plan(response.text)

        tasks = []
        for t in plan_data["tasks"]:
            tasks.append(
                Task(
                    id=t.get("id", new_id()),
                    description=t["description"],
                    agent_type=AgentType(t["agent_type"]),
                    dependencies=t.get("dependencies", []),
                    input_data=t.get("input_data", {}),
                )
            )

        self._validate_dag(tasks)
        plan = ExecutionPlan(goal=goal, tasks=tasks)
        logger.info(f"Plan created with {len(tasks)} tasks")
        return plan

    def _parse_plan(self, text: str) -> dict[str, Any]:
        """Extract JSON from the LLM response, handling markdown code fences."""
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        return json.loads(text)

    def _validate_dag(self, tasks: list[Task]) -> None:
        """Verify there are no cycles and all dependencies exist."""
        task_ids = {t.id for t in tasks}
        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    raise ValueError(f"Task {task.id} depends on unknown task {dep}")

        visited: set[str] = set()
        in_progress: set[str] = set()
        task_map = {t.id: t for t in tasks}

        def visit(tid: str) -> None:
            if tid in visited:
                return
            if tid in in_progress:
                raise ValueError(f"Cycle detected involving task {tid}")
            in_progress.add(tid)
            for dep in task_map[tid].dependencies:
                visit(dep)
            in_progress.remove(tid)
            visited.add(tid)

        for t in tasks:
            visit(t.id)
