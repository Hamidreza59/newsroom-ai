from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import date, datetime
from zoneinfo import ZoneInfo

from newsroom_core.config import Settings


def _today() -> date:
    return datetime.now(ZoneInfo("America/New_York")).date()


def _setup_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(name)-22s %(message)s",
        datefmt="%H:%M:%S",
    )
    for noisy in ("httpx", "httpcore", "mcp"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    logging.getLogger("phonemizer").setLevel(logging.ERROR)


def cmd_run(args: argparse.Namespace) -> None:
    from newsroom_agents.pipeline import produce_episode

    settings = Settings()
    if args.offline:
        settings.offline = True
    if args.llm:
        settings.llm_provider = args.llm
    if args.review:
        settings.human_review = True
    show_date = date.fromisoformat(args.date) if args.date else _today()
    asyncio.run(produce_episode(settings, show_date, record=not args.no_record, approve=ask_approval))


def ask_approval(payload: dict) -> bool:
    """Human-in-the-loop gate: shown only when guardrails had to rewrite on-air copy."""
    print(f"\nReview needed: {payload['reason']}\n  events: {payload['events']}\n"
          f"  script: {payload['script']}")
    if not sys.stdin.isatty():
        print("  no terminal attached; leaving the episode unapproved")
        return False
    return input("Approve this episode for publishing? [y/N] ").strip().lower() == "y"


def cmd_graph(_: argparse.Namespace) -> None:
    from newsroom_agents.pipeline import mermaid

    print(mermaid())


def cmd_tools(_: argparse.Namespace) -> None:
    from newsroom_agents.pipeline import mcp_client

    async def show() -> None:
        async with mcp_client(Settings()) as client:
            for tool in (await client.list_tools()).tools:
                print(f"{tool.name:22} {tool.description.splitlines()[0]}")

    asyncio.run(show())


def main() -> None:
    parser = argparse.ArgumentParser(prog="newsroom-agents", description="Multi-agent AI newsroom")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="write today's show package (script, fact-checked)")
    run.add_argument("--date", help="show date YYYY-MM-DD (default: today, US/Eastern)")
    run.add_argument("--offline", action="store_true", help="use sample market data and news")
    run.add_argument("--llm", choices=["ollama", "openai", "mock"])
    run.add_argument("--no-record", action="store_true", help="don't save stories to the archive")
    run.add_argument("--review", action="store_true",
                     help="pause for human approval when guardrails rewrite on-air copy")
    run.set_defaults(func=cmd_run)

    sub.add_parser("tools", help="list the MCP server's tools").set_defaults(func=cmd_tools)
    sub.add_parser("graph", help="print the LangGraph orchestration as Mermaid").set_defaults(
        func=cmd_graph)

    args = parser.parse_args()
    _setup_logging(args.verbose)
    args.func(args)


if __name__ == "__main__":
    main()
