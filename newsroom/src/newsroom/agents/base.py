from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any, TypeVar

from mcp import Client
from pydantic import BaseModel

from newsroom.llm import LlmProvider, LlmUnavailable

T = TypeVar("T", bound=BaseModel)


class ToolClient:
    """Thin wrapper over an MCP client session that returns plain JSON-like values."""

    def __init__(self, client: Client):
        self.client = client

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


class Agent:
    role = "agent"

    def __init__(self, llm: LlmProvider, tools: ToolClient, show_name: str,
                 anchors: dict[str, str] | None = None):
        self.llm = llm
        self.tools = tools
        self.show_name = show_name
        self.anchors = anchors or {"a": "Maya", "b": "Leo"}
        self.log = logging.getLogger(f"newsroom.{self.role}")

    async def ask(self, system: str, user: str, schema: type[T], fallback: Callable[[], T]) -> T:
        try:
            return await self.llm.generate_json(system, user, schema)
        except LlmUnavailable as exc:
            if not str(exc).startswith("mock"):
                self.log.warning("LLM unavailable, using fallback copy: %s", exc)
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
