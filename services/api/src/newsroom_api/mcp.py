"""MCP client helpers: streamable HTTP when MCP_URL is set, otherwise a stdio subprocess."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from newsroom_core.config import Settings


def mcp_client(settings: Settings) -> Client:
    target = settings.mcp_url or StdioServerParameters(
        command=sys.executable,
        args=["-m", "newsroom_mcp.server"],
        env={**os.environ, **settings.server_env()},
    )
    return Client(target, read_timeout_seconds=120)


def unwrap(result: Any, name: str) -> Any:
    if result.is_error:
        text = result.content[0].text if result.content else "unknown error"
        raise RuntimeError(f"tool {name} failed: {text}")
    data = result.structured_content
    if data is None and result.content:
        data = json.loads(result.content[0].text)
    if isinstance(data, dict) and set(data) == {"result"}:
        return data["result"]
    return data


async def call_tools(settings: Settings, calls: list[tuple[str, dict]]) -> list[Any]:
    """Run several tool calls over one short-lived client session."""
    async with mcp_client(settings) as client:
        return [unwrap(await client.call_tool(name, args), name) for name, args in calls]
