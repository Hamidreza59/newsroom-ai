from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, ClassVar, TypeVar

from mcp import Client
from pydantic import BaseModel

from newsroom_agents.guardrails import GuardrailLog, ScopedTools
from newsroom_agents.llm import LlmProvider, LlmUnavailable, Tier
from newsroom_agents.observability import Tracer

T = TypeVar("T", bound=BaseModel)


class ToolClient:
    """Thin wrapper over an MCP client session that returns plain JSON-like values."""

    def __init__(self, client: Client, tracer: Tracer | None = None):
        self.client = client
        self.tracer = tracer

    async def call(self, name: str, **arguments: Any) -> Any:
        result = await self.client.call_tool(name, arguments)
        if result.is_error:
            text = result.content[0].text if result.content else "unknown error"
            raise RuntimeError(f"tool {name} failed: {text}")
        data = result.structured_content
        if data is None and result.content:
            data = json.loads(result.content[0].text)
        if isinstance(data, dict) and set(data) == {"result"}:
            return data["result"]
        return data


class TracedTools:
    """Scoped tool access that also records every call as a trace span."""

    def __init__(self, scoped: ScopedTools, tracer: Tracer):
        self.scoped, self.tracer = scoped, tracer

    async def call(self, name: str, **arguments: Any) -> Any:
        with self.tracer.span(self.scoped.agent, "tool", name):
            return await self.scoped.call(name, **arguments)


class Agent:
    """Base agent: one responsibility, a model tier, scoped tools, and a deterministic fallback."""

    role: ClassVar[str] = "agent"
    tier: ClassVar[Tier] = "smart"

    def __init__(self, llm: LlmProvider, tools: Any, show_name: str,
                 anchors: dict[str, str] | None = None, guard: GuardrailLog | None = None,
                 tracer: Tracer | None = None):
        self.llm = llm
        self.tools = tools
        self.show_name = show_name
        self.anchors = anchors or {"a": "Maya", "b": "Leo"}
        self.guard = guard or GuardrailLog()
        self.tracer = tracer or Tracer()
        self.log = logging.getLogger(f"newsroom.{self.role}")

    async def ask(self, system: str, user: str, schema: type[T], fallback: Callable[[], T]) -> T:
        with self.tracer.span(self.role, "llm", schema.__name__) as span:
            try:
                return await self.llm.generate_json(system, user, schema)
            except LlmUnavailable as exc:
                if not str(exc).startswith("mock"):
                    self.log.warning("LLM unavailable, using fallback copy: %s", exc)
                span.detail = f"fallback: {exc}"[:200]
                self.tracer.count(f"fallback.{self.role}")
                return fallback()

    def cast(self) -> str:
        a, b = self.anchors["a"], self.anchors["b"]
        return (
            f"The show has two co-anchors at a news desk: {a} (speaker \"a\") and {b} "
            f"(speaker \"b\"). They are warm, professional and talk to each other naturally, "
            "handing off by name now and then. Each line is one to three short sentences."
        )

    async def style(self, query: str, k: int = 2) -> str:
        sections = await self.tools.call("search_style_guide", query=query, k=k)
        return "\n".join(f"- {s}" for s in sections)
