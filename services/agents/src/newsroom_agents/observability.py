"""Tracing for the agent pipeline: every agent step, LLM call and tool call becomes a span."""

from __future__ import annotations

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Span:
    agent: str
    kind: str
    name: str
    started: float
    ms: float = 0.0
    ok: bool = True
    detail: str = ""


@dataclass
class Tracer:
    spans: list[Span] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    t0: float = field(default_factory=time.monotonic)

    @contextmanager
    def span(self, agent: str, kind: str, name: str, detail: str = ""):
        s = Span(agent, kind, name, round(time.monotonic() - self.t0, 3), detail=detail[:200])
        start = time.monotonic()
        try:
            yield s
        except Exception as exc:
            s.ok = False
            s.detail = f"{type(exc).__name__}: {exc}"[:200]
            raise
        finally:
            s.ms = round((time.monotonic() - start) * 1000, 1)
            self.spans.append(s)

    def count(self, key: str, n: int = 1) -> None:
        self.metrics[key] = self.metrics.get(key, 0) + n

    def summary(self) -> dict[str, Any]:
        per_agent: dict[str, dict[str, float]] = {}
        for s in self.spans:
            a = per_agent.setdefault(s.agent, {"spans": 0, "tool_calls": 0, "llm_calls": 0, "ms": 0.0})
            a["spans"] += 1
            a["ms"] = round(a["ms"] + s.ms, 1)
            if s.kind == "tool":
                a["tool_calls"] += 1
            if s.kind == "llm":
                a["llm_calls"] += 1
        return {"wall_seconds": round(time.monotonic() - self.t0, 1), "agents": per_agent,
                "metrics": self.metrics}

    def write(self, out_dir: Path) -> None:
        with (out_dir / "trace.jsonl").open("w") as fh:
            for s in self.spans:
                fh.write(json.dumps(asdict(s)) + "\n")
