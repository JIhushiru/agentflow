from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from backend.config import settings
from backend.llm import llm_client, LLMResponse
from backend.models import AgentOutput, AgentType, Artifact, Task


class BaseAgent(ABC):
    name: str
    agent_type: AgentType
    system_prompt: str
    model: str = settings.default_model

    def __init__(self) -> None:
        self.tools: list[dict[str, Any]] = []

    @abstractmethod
    def get_system_prompt(self) -> str: ...

    def get_tools_schema(self) -> list[dict[str, Any]]:
        """Return Claude tool_use compatible tool definitions."""
        return self.tools

    async def execute(self, task: Task, context: dict[str, Any]) -> AgentOutput:
        """Execute a task and return structured output."""
        start = time.perf_counter()
        reasoning_trace: list[str] = []
        artifacts: list[Artifact] = []
        total_tokens = 0

        messages = self._build_messages(task, context)
        tools_schema = self.get_tools_schema()

        for attempt in range(settings.max_retries + 1):
            try:
                response = await llm_client.chat(
                    model=self.model,
                    system=self.get_system_prompt(),
                    messages=messages,
                    tools=tools_schema or None,
                )
                total_tokens += response.input_tokens + response.output_tokens

                if response.tool_calls:
                    reasoning_trace.append(
                        f"Tool calls: {[tc.name for tc in response.tool_calls]}"
                    )
                    tool_results = await self._execute_tools(response.tool_calls)
                    # Append assistant response + tool results for next turn
                    messages.append({"role": "assistant", "content": response.text})
                    messages.append({"role": "user", "content": tool_results})
                    continue

                reasoning_trace.append(f"Final response (attempt {attempt + 1})")
                duration_ms = int((time.perf_counter() - start) * 1000)

                return AgentOutput(
                    agent_name=self.name,
                    task_id=task.id,
                    result=response.text,
                    artifacts=artifacts,
                    reasoning_trace=reasoning_trace,
                    tokens_used=total_tokens,
                    duration_ms=duration_ms,
                )

            except Exception as e:
                reasoning_trace.append(f"Error (attempt {attempt + 1}): {e}")
                logger.warning(f"Agent {self.name} error on attempt {attempt + 1}: {e}")
                if attempt == settings.max_retries:
                    raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        return AgentOutput(
            agent_name=self.name,
            task_id=task.id,
            result="Agent completed without producing a final response.",
            artifacts=artifacts,
            reasoning_trace=reasoning_trace,
            tokens_used=total_tokens,
            duration_ms=duration_ms,
        )

    def _build_messages(self, task: Task, context: dict[str, Any]) -> list[dict[str, Any]]:
        user_content = f"## Task\n{task.description}"
        if task.input_data:
            user_content += f"\n\n## Input Data\n```json\n{task.input_data}\n```"
        if context:
            deps_output = context.get("dependencies_output", {})
            if deps_output:
                user_content += "\n\n## Context from Previous Tasks\n"
                for dep_id, output in deps_output.items():
                    user_content += f"\n### Output from task {dep_id}:\n{output}\n"
        return [{"role": "user", "content": user_content}]

    async def _execute_tools(
        self, tool_calls: list,
    ) -> list[dict[str, Any]]:
        """Execute tool calls and return results."""
        from backend.tools.registry import tool_registry

        results = []
        for tc in tool_calls:
            tool = tool_registry.get(tc.name)
            if tool is None:
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": f"Error: unknown tool '{tc.name}'",
                    "is_error": True,
                })
                continue
            try:
                output = await tool.execute(**tc.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": str(output),
                })
            except Exception as e:
                logger.error(f"Tool {tc.name} failed: {e}")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": f"Error executing tool: {e}",
                    "is_error": True,
                })
        return results
