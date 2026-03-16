from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine

from loguru import logger

from backend.agents import create_agent
from backend.models import (
    AgentOutput,
    ExecutionPlan,
    SessionEvent,
    Task,
    TaskStatus,
)


class ExecutionEngine:
    """Executes a task DAG with dependency resolution and parallel execution."""

    def __init__(
        self,
        on_event: Callable[[SessionEvent], Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self._on_event = on_event
        self._outputs: dict[str, AgentOutput] = {}

    async def execute(self, plan: ExecutionPlan) -> dict[str, AgentOutput]:
        """Execute all tasks in the plan respecting dependencies."""
        task_map: dict[str, Task] = {t.id: t for t in plan.tasks}
        pending = set(task_map.keys())
        running: set[str] = set()
        completed: set[str] = set()
        failed: set[str] = set()

        async def run_task(task: Task) -> None:
            task.status = TaskStatus.RUNNING
            await self._emit(SessionEvent(
                event_type="task_started",
                data={"task_id": task.id, "agent_type": task.agent_type.value, "description": task.description},
            ))

            try:
                agent = create_agent(task.agent_type)

                # Gather outputs from dependencies
                context: dict[str, Any] = {}
                deps_output = {}
                for dep_id in task.dependencies:
                    if dep_id in self._outputs:
                        deps_output[dep_id] = self._outputs[dep_id].result
                if deps_output:
                    context["dependencies_output"] = deps_output

                await self._emit(SessionEvent(
                    event_type="agent_thinking",
                    data={"task_id": task.id, "agent": agent.name},
                ))

                output = await agent.execute(task, context)
                self._outputs[task.id] = output
                task.status = TaskStatus.COMPLETE
                task.output_data = {"result": output.result}

                await self._emit(SessionEvent(
                    event_type="task_complete",
                    data={
                        "task_id": task.id,
                        "agent": agent.name,
                        "result_preview": output.result[:200],
                        "tokens_used": output.tokens_used,
                        "duration_ms": output.duration_ms,
                    },
                ))
                logger.info(
                    f"Task {task.id} complete ({output.duration_ms}ms, {output.tokens_used} tokens)"
                )

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.output_data = {"error": str(e)}
                await self._emit(SessionEvent(
                    event_type="task_failed",
                    data={"task_id": task.id, "error": str(e)},
                ))
                logger.error(f"Task {task.id} failed: {e}")
                raise

        # Main execution loop — schedule tasks as their dependencies complete
        while pending or running:
            # Find tasks whose dependencies are all satisfied
            ready = []
            for tid in list(pending):
                task = task_map[tid]
                deps_met = all(d in completed for d in task.dependencies)
                deps_failed = any(d in failed for d in task.dependencies)
                if deps_failed:
                    pending.discard(tid)
                    failed.add(tid)
                    task.status = TaskStatus.FAILED
                    task.output_data = {"error": "Dependency failed"}
                    await self._emit(SessionEvent(
                        event_type="task_failed",
                        data={"task_id": tid, "error": "Dependency failed"},
                    ))
                elif deps_met:
                    ready.append(tid)

            # Launch ready tasks in parallel
            tasks_to_run: list[asyncio.Task[None]] = []
            for tid in ready:
                pending.discard(tid)
                running.add(tid)
                tasks_to_run.append(
                    asyncio.create_task(run_task(task_map[tid]), name=f"task-{tid}")
                )

            if not tasks_to_run and running:
                # Wait for at least one running task to finish
                done, _ = await asyncio.wait(
                    [t for t in asyncio.all_tasks() if t.get_name().startswith("task-") and not t.done()],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for d in done:
                    tid = d.get_name().removeprefix("task-")
                    running.discard(tid)
                    if d.exception():
                        failed.add(tid)
                    else:
                        completed.add(tid)
            elif tasks_to_run:
                # Wait for the batch we just launched
                results = await asyncio.gather(
                    *tasks_to_run, return_exceptions=True
                )
                for task_coro, result in zip(tasks_to_run, results):
                    tid = task_coro.get_name().removeprefix("task-")
                    running.discard(tid)
                    if isinstance(result, Exception):
                        failed.add(tid)
                    else:
                        completed.add(tid)
            else:
                # Nothing to do — everything has been processed
                break

        return self._outputs

    async def _emit(self, event: SessionEvent) -> None:
        if self._on_event:
            await self._on_event(event)
