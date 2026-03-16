"""Unified LLM client supporting Ollama (free/local), Anthropic Claude, and Groq."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import httpx
from loguru import logger

from backend.config import settings


@dataclass
class LLMMessage:
    role: str
    content: str


@dataclass
class ToolCall:
    id: str
    name: str
    input: dict[str, Any]


@dataclass
class LLMResponse:
    text: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    input_tokens: int = 0
    output_tokens: int = 0


class LLMClient:
    """Routes to Ollama, Anthropic, or Groq based on settings.llm_provider."""

    async def chat(
        self,
        *,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        if settings.llm_provider == "anthropic":
            return await self._anthropic_chat(model, system, messages, tools, max_tokens)
        elif settings.llm_provider == "groq":
            return await self._groq_chat(model, system, messages, tools, max_tokens)
        else:
            return await self._ollama_chat(model, system, messages, tools, max_tokens)

    # ── Ollama (free, local) ──────────────────────────────────────────────

    async def _ollama_chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> LLMResponse:
        ollama_messages = self._build_openai_messages(system, messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"num_predict": max_tokens},
        }

        if tools:
            openai_tools = self._convert_tools_to_openai(tools)
            if openai_tools:
                payload["tools"] = openai_tools

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{settings.ollama_base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()

        message = data.get("message", {})
        text = message.get("content", "")
        tool_calls: list[ToolCall] = []

        # Parse Ollama tool calls
        for i, tc in enumerate(message.get("tool_calls", [])):
            func = tc.get("function", {})
            tool_calls.append(ToolCall(
                id=f"ollama_{i}",
                name=func.get("name", ""),
                input=func.get("arguments", {}),
            ))

        # Estimate tokens from response metadata
        input_tokens = data.get("prompt_eval_count", 0)
        output_tokens = data.get("eval_count", 0)

        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    # ── Groq (cloud, OpenAI-compatible) ─────────────────────────────────

    async def _groq_chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> LLMResponse:
        openai_messages = self._build_openai_messages(system, messages)

        payload: dict[str, Any] = {
            "model": model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }
        if tools:
            openai_tools = self._convert_tools_to_openai(tools)
            if openai_tools:
                payload["tools"] = openai_tools

        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{settings.groq_base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            resp.raise_for_status()
            data = resp.json()

        choice = data["choices"][0]["message"]
        text = choice.get("content", "") or ""
        tool_calls: list[ToolCall] = []

        import json as _json

        for tc in choice.get("tool_calls", []) or []:
            func = tc.get("function", {})
            raw_args = func.get("arguments", "{}")
            args = _json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            tool_calls.append(ToolCall(
                id=tc.get("id", f"groq_{id(tc)}"),
                name=func.get("name", ""),
                input=args,
            ))

        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )

    # ── Shared helpers for OpenAI-compatible APIs ─────────────────────────

    def _build_openai_messages(
        self, system: str, messages: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Convert internal message format to OpenAI-compatible messages."""
        openai_messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        for msg in messages:
            if msg["role"] == "user":
                content = msg["content"]
                if isinstance(content, list):
                    parts = []
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "tool_result":
                            prefix = "[Tool Error] " if item.get("is_error") else "[Tool Result] "
                            parts.append(prefix + str(item.get("content", "")))
                        else:
                            parts.append(str(item))
                    content = "\n".join(parts)
                openai_messages.append({"role": "user", "content": content})
            elif msg["role"] == "assistant":
                content = msg["content"]
                if isinstance(content, list):
                    text_parts = []
                    for block in content:
                        if hasattr(block, "text"):
                            text_parts.append(block.text)
                        elif hasattr(block, "name"):
                            text_parts.append(f"[Called tool: {block.name}]")
                    content = "\n".join(text_parts)
                openai_messages.append({"role": "assistant", "content": content})
        return openai_messages

    @staticmethod
    def _convert_tools_to_openai(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Convert Claude tool_use format to OpenAI function-calling format."""
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {}),
                },
            })
        return openai_tools

    # ── Anthropic Claude ──────────────────────────────────────────────────

    async def _anthropic_chat(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None,
        max_tokens: int,
    ) -> LLMResponse:
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        kwargs: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools

        response = await client.messages.create(**kwargs)

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(ToolCall(id=block.id, name=block.name, input=block.input))

        return LLMResponse(
            text="\n".join(text_parts),
            tool_calls=tool_calls,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )


# Global singleton
llm_client = LLMClient()
