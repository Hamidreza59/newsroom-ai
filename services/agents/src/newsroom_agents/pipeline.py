"""LangGraph orchestration of the newsroom agents.

    START → market ─┬→ scout ───┐
                    └→ analyst ─┴→ writer ─┬→ hook ──────┐
                                           ├→ explainer ─┼→ editor ⇄ revise
                                           └→ quiz ──────┘     ↓
                                                         finalize → package → review_gate → publish → END
"""

from __future__ import annotations

import json
import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from mcp import Client
from mcp.client.stdio import StdioServerParameters
from newsroom_core.config import Settings
from newsroom_core.models import (
    CoveredStory,
    Explainer,
    Line,
    MarketBrief,
    MarketSnapshot,
    NewsItem,
    Quiz,
    ShowPackage,
    ShowScript,
)

from newsroom_agents.agents.base import ToolClient, TracedTools
from newsroom_agents.agents.editor import Editor
from newsroom_agents.agents.market_analyst import MarketAnalyst, fact_sheet
from newsroom_agents.agents.news_scout import NewsScout
from newsroom_agents.agents.scriptwriter import Scriptwriter
from newsroom_agents.agents.segments import ExplainerAgent, HookWriter, QuizMaster
from newsroom_agents.estimate import estimate_seconds, script_markdown
from newsroom_agents.guardrails import GuardrailLog, ScopedTools
from newsroom_agents.llm import LlmRouter
from newsroom_agents.observability import Tracer

log = logging.getLogger("newsroom_agents.pipeline")
MAX_REVISIONS = 2
EXPLAINER_PHRASES = "Time for A.I. AI in 30 seconds. Now you know."


class ShowState(TypedDict, total=False):
    snapshot: MarketSnapshot
    items: list[NewsItem]
    brief: MarketBrief
    script: ShowScript
    cold_open: list[Line]
    explainer: Explainer | None
    explainer_material: str
    quiz: Quiz | None
    review: dict[str, Any]
    revisions: int
    package: ShowPackage
    approved: bool


@dataclass
class Newsroom:
    """Everything the graph nodes share for one show: agents, tools, guardrails and tracing."""

    settings: Settings
    show_date: date
    out_dir: Path
    guard: GuardrailLog
    tracer: Tracer
    router: LlmRouter
    orchestrator_tools: TracedTools
    analyst: MarketAnalyst
    scout: NewsScout
    writer: Scriptwriter
    hook: HookWriter
    explainer: ExplainerAgent
    quiz: QuizMaster
    editor: Editor
    record: bool = True

    @property
    def iso_date(self) -> str:
        return self.show_date.isoformat()


class TooLong(Exception):
    pass


def server_params(settings: Settings) -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable,
        args=["-m", "newsroom_mcp.server"],
        env={**os.environ, **settings.server_env()},
    )


def mcp_client(settings: Settings) -> Client:
    """Streamable-HTTP client when MCP_URL is set, otherwise a stdio subprocess."""
    target = settings.mcp_url or server_params(settings)
    return Client(target, read_timeout_seconds=120)


def write_package(nr: Newsroom, pkg: ShowPackage) -> None:
    nr.out_dir.mkdir(parents=True, exist_ok=True)
    (nr.out_dir / "package.json").write_text(pkg.model_dump_json(indent=2))
    (nr.out_dir / "script.md").write_text(script_markdown(
        pkg.script, nr.settings.anchor_names, nr.settings.show_name, nr.iso_date))


def materials_for(items: list[NewsItem]) -> dict[str, str]:
    return {i.id: f"{i.title}. {i.summary}" for i in items}


def build_graph(nr: Newsroom):
    async def market(state: ShowState) -> ShowState:
        snap = MarketSnapshot.model_validate(await nr.orchestrator_tools.call("get_market_snapshot"))
        log.info("market snapshot as of %s (sample=%s)", snap.as_of, snap.sample_data)
        return {"snapshot": snap, "revisions": 0}

    async def scout(state: ShowState) -> ShowState:
        return {"items": await nr.scout.run(nr.settings.stories_per_show, nr.iso_date)}

    async def analyst(state: ShowState) -> ShowState:
        return {"brief": await nr.analyst.run(state["snapshot"])}

    async def writer(state: ShowState) -> ShowState:
        return {"script": await nr.writer.run(state["brief"], state["items"], nr.show_date)}

    async def hook(state: ShowState) -> ShowState:
        return {"cold_open": await nr.hook.run(state["script"].stories, state["snapshot"])}

    async def explainer(state: ShowState) -> ShowState:
        result = await nr.explainer.run(state["script"].stories, nr.iso_date)
        if not result:
            return {"explainer": None, "explainer_material": ""}
        ex, material = result
        return {"explainer": ex, "explainer_material": material}

    async def quiz(state: ShowState) -> ShowState:
        q = await nr.quiz.run(state["script"].stories, materials_for(state["items"]),
                              state["snapshot"], nr.iso_date)
        return {"quiz": q}

    def hook_material(state: ShowState) -> str:
        top = state["items"][0]
        return f"{top.title}. {top.summary} {fact_sheet(state['snapshot'])}"

    async def editor(state: ShowState) -> ShowState:
        script = state["script"].model_copy(update={
            "cold_open": state.get("cold_open", []), "explainer": state.get("explainer"),
            "quiz": state.get("quiz")})
        review = nr.editor.review(script, state["snapshot"], materials_for(state["items"]))
        hook_issues = nr.editor.check_segment(script.cold_open, hook_material(state), state["snapshot"])
        ex_material = f"{state.get('explainer_material', '')} {EXPLAINER_PHRASES}"
        ex_issues = (nr.editor.check_segment(script.explainer.lines, ex_material)
                     if script.explainer else [])
        clean = review.clean and not hook_issues and not ex_issues
        if state.get("revisions", 0) == 0:
            nr.tracer.metrics["editor_first_pass_clean"] = clean
        nr.tracer.count("editor_reviews")
        return {"script": script, "review": {
            "clean": clean, "revisable": not review.clean, "market": review.market,
            "stories": review.stories, "hook": hook_issues, "explainer": ex_issues}}

    def after_editor(state: ShowState) -> str:
        """Bounded autonomy: only rewritable copy loops back, at most MAX_REVISIONS times."""
        if state["review"]["revisable"] and state.get("revisions", 0) < MAX_REVISIONS:
            return "revise"
        return "finalize"

    async def revise(state: ShowState) -> ShowState:
        review, script = state["review"], state["script"]
        n = state.get("revisions", 0) + 1
        log.info("revision round %d", n)
        nr.tracer.count("revisions")
        market = script.market
        if review["market"]:
            market = await nr.analyst.run(state["snapshot"], feedback="\n".join(review["market"]))
        stories = []
        for i, (item, seg) in enumerate(zip(state["items"], script.stories, strict=True)):
            issues = review["stories"].get(seg.story_id)
            stories.append(await nr.writer.write_story(item, i, "\n".join(issues)) if issues else seg)
        return {"script": script.model_copy(update={"market": market, "stories": stories}),
                "revisions": n}

    async def finalize(state: ShowState) -> ShowState:
        review, script, snap = state["review"], state["script"], state["snapshot"]
        if review["market"]:
            nr.guard.add("output", "market_fallback", "block", "editor", "; ".join(review["market"]))
            script = script.model_copy(update={"market": nr.analyst.fallback(snap)})
        stories = []
        for i, (item, seg) in enumerate(zip(state["items"], script.stories, strict=True)):
            if any(x.startswith("remove") for x in review["stories"].get(seg.story_id, [])):
                nr.guard.add("output", "story_fallback", "block", "editor", seg.headline)
                seg = nr.writer.segment(item, nr.writer.fallback_story(item, i))
            stories.append(seg)
        update: dict[str, Any] = {"stories": stories}
        if review["hook"]:
            nr.guard.add("output", "hook_fallback", "warn", "editor", "; ".join(review["hook"]))
            update["cold_open"] = nr.hook.fallback(stories[0], snap)
        if review["explainer"]:
            nr.guard.add("output", "explainer_dropped", "warn", "editor", "; ".join(review["explainer"]))
            update["explainer"] = None
        script = nr.editor.redact(script.model_copy(update=update), nr.guard)
        return {"script": nr.editor.enforce(script)}

    async def package(state: ShowState) -> ShowState:
        script, snap = state["script"], state["snapshot"]
        seconds = estimate_seconds(script)
        while seconds > nr.settings.max_seconds:
            try:
                script = await shorten(script, seconds)
            except TooLong:
                log.warning("estimated %.1fs is over budget and nothing is left to cut", seconds)
                break
            seconds = estimate_seconds(script)
        pkg = ShowPackage(date=nr.iso_date, script=script, snapshot=snap, estimated_seconds=seconds,
                          needs_review=nr.guard.needs_review, approved=False)
        write_package(nr, pkg)
        return {"package": pkg, "script": script}

    async def drop_story(script: ShowScript, seconds: float) -> ShowScript:
        dropped = script.stories[-1]
        log.info("%.1fs estimated; dropping story '%s'", seconds, dropped.headline)
        script = script.model_copy(update={"stories": script.stories[:-1]})
        bookends = await nr.writer.write_bookends(script.market, script.stories, nr.show_date)
        return script.model_copy(update={"intro": bookends.intro, "outro": bookends.outro})

    async def shorten(script: ShowScript, seconds: float) -> ShowScript:
        """Time budget, in priority order: 3 stories, then the quiz recap, explainer, 2 stories, quiz."""
        if len(script.stories) > 3:
            return await drop_story(script, seconds)
        if script.quiz and script.quiz.reveal_lines:
            log.info("%.1fs estimated; dropping the quiz recap", seconds)
            return script.model_copy(update={"quiz": script.quiz.model_copy(
                update={"reveal_lines": [], "reveal": ""})})
        if script.explainer:
            log.info("%.1fs estimated; dropping the explainer", seconds)
            return script.model_copy(update={"explainer": None})
        if len(script.stories) > 2:
            return await drop_story(script, seconds)
        if script.quiz:
            log.info("%.1fs estimated; dropping the quiz", seconds)
            return script.model_copy(update={"quiz": None})
        raise TooLong(seconds)

    async def review_gate(state: ShowState) -> ShowState:
        approved = True
        if nr.settings.human_review and nr.guard.needs_review:
            decision = interrupt({"reason": "guardrails had to rewrite on-air copy",
                                  "script": str(nr.out_dir / "script.md"),
                                  "events": nr.guard.counts()})
            approved = bool(decision)
        pkg = state["package"].model_copy(update={"approved": approved})
        write_package(nr, pkg)
        return {"approved": approved, "package": pkg}

    async def publish(state: ShowState) -> ShowState:
        if not state.get("approved") or nr.settings.offline or not nr.record:
            return {}
        script, items = state["script"], {i.id: i for i in state["items"]}
        tools = nr.orchestrator_tools
        await tools.call("record_coverage", show_date=nr.iso_date, stories=[
            CoveredStory(id=s.story_id, title=items[s.story_id].title,
                         summary=items[s.story_id].summary, url=s.url).model_dump()
            for s in script.stories])
        if script.explainer:
            await tools.call("record_segment", kind="explainer", key=script.explainer.key,
                             show_date=nr.iso_date, payload={"title": script.explainer.title})
        if script.quiz:
            q = script.quiz
            await tools.call("record_segment", kind="quiz", key=nr.iso_date, show_date=nr.iso_date,
                             payload={"question": q.question, "options": q.options,
                                      "answer_index": q.answer_index})
        return {}

    g = StateGraph(ShowState)
    for name, fn in [("market", market), ("scout", scout), ("analyst", analyst),
                     ("writer", writer), ("hook", hook), ("explainer", explainer), ("quiz", quiz),
                     ("editor", editor), ("revise", revise), ("finalize", finalize),
                     ("package", package), ("review_gate", review_gate), ("publish", publish)]:
        g.add_node(name, traced(nr, name, fn))
    g.add_edge(START, "market")
    g.add_edge("market", "scout")
    g.add_edge("market", "analyst")
    g.add_edge(["scout", "analyst"], "writer")
    for seg in ("hook", "explainer", "quiz"):
        g.add_edge("writer", seg)
    g.add_edge(["hook", "explainer", "quiz"], "editor")
    g.add_conditional_edges("editor", after_editor, {"revise": "revise", "finalize": "finalize"})
    g.add_edge("revise", "editor")
    g.add_edge("finalize", "package")
    g.add_edge("package", "review_gate")
    g.add_edge("review_gate", "publish")
    g.add_edge("publish", END)
    return g.compile(checkpointer=InMemorySaver())


def traced(nr: Newsroom, name: str, fn):
    async def node(state: ShowState) -> ShowState:
        with nr.tracer.span("graph", "node", name):
            return await fn(state)
    node.__name__ = name
    return node


def _newsroom(settings: Settings, show_date: date, tools: ToolClient | None,
              guard: GuardrailLog, tracer: Tracer, record: bool = True) -> Newsroom:
    router = LlmRouter(settings, guard)
    anchors = settings.anchor_names

    def scoped(role: str) -> TracedTools:
        return TracedTools(ScopedTools(tools, role, guard), tracer)

    def agent(cls):
        return cls(router.for_agent(cls.role, cls.tier), scoped(cls.role), settings.show_name,
                   anchors, guard, tracer)

    return Newsroom(
        settings=settings, show_date=show_date,
        out_dir=settings.out_dir / show_date.isoformat(), guard=guard, tracer=tracer,
        router=router, orchestrator_tools=scoped("orchestrator"),
        analyst=agent(MarketAnalyst), scout=agent(NewsScout), writer=agent(Scriptwriter),
        hook=agent(HookWriter), explainer=agent(ExplainerAgent), quiz=agent(QuizMaster),
        editor=Editor(list(anchors.values()), settings.show_name), record=record,
    )


def mermaid() -> str:
    """The orchestration graph as Mermaid, built without models, TTS or MCP."""
    settings = Settings()
    settings.llm_provider = "mock"
    nr = _newsroom(settings, date.today(), None, GuardrailLog(), Tracer())
    return build_graph(nr).get_graph().draw_mermaid()


async def produce_episode(settings: Settings, show_date: date, record: bool = True,
                          approve: Callable[[dict], bool] | None = None) -> Path:
    guard, tracer = GuardrailLog(), Tracer()
    async with mcp_client(settings) as client:
        nr = _newsroom(settings, show_date, ToolClient(client, tracer), guard, tracer, record)
        log.info("models: smart=%s fast=%s  offline=%s",
                 nr.router.providers["smart"].name, nr.router.providers["fast"].name,
                 settings.offline)
        graph = build_graph(nr)
        config = {"configurable": {"thread_id": f"show-{nr.iso_date}"}}
        result = await graph.ainvoke({}, config)
        while "__interrupt__" in result:
            payload = result["__interrupt__"][0].value
            decision = approve(payload) if approve else False
            result = await graph.ainvoke(Command(resume=decision), config)

    pkg: ShowPackage = result["package"]
    write_reports(nr, result)
    log.info("package ready: %s (~%.1fs, %d stories, needs_review=%s) in %.0fs",
             nr.out_dir, pkg.estimated_seconds, len(pkg.script.stories),
             guard.needs_review, tracer.summary()["wall_seconds"])
    return nr.out_dir


def write_reports(nr: Newsroom, result: ShowState) -> None:
    nr.guard.write(nr.out_dir / "guardrails.json")
    nr.tracer.write(nr.out_dir)
    report = {
        "date": nr.iso_date,
        "models": {tier: p.name for tier, p in nr.router.providers.items()},
        "llm_calls": {"used": nr.router.calls, "budget": nr.router.budget,
                      "circuit_breaker_open": nr.router.open},
        "agents": nr.router.report(),
        "trace": nr.tracer.summary(),
        "guardrails": {"needs_review": nr.guard.needs_review, "counts": nr.guard.counts()},
        "approved": result.get("approved", False),
    }
    (nr.out_dir / "run_report.json").write_text(json.dumps(report, indent=2))
