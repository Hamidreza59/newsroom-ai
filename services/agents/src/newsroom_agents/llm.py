from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal, Protocol, TypeVar

import newsroom_core.net  # noqa: F401
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from newsroom_core.config import Settings
from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from newsroom_agents.guardrails import GuardrailLog

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LlmUnavailable(Exception):
    """The provider cannot produce an answer; agents fall back to deterministic copy."""


class LlmProvider(Protocol):
    name: str

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T: ...


class LangChainProvider:
    """Structured output from any LangChain chat model, validated against a Pydantic schema."""

    def __init__(self, name: str, chat: BaseChatModel, method: str, attempts: int = 3):
        self.name = name
        self.chat = chat
        self.method = method
        self.attempts = attempts

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T:
        runnable = self.chat.with_structured_output(schema, method=self.method).with_retry(
            stop_after_attempt=self.attempts, retry_if_exception_type=(ValidationError, ValueError),
        )
        try:
            result = await runnable.ainvoke([SystemMessage(system), HumanMessage(user)])
        except Exception as exc:
            raise LlmUnavailable(f"{self.name}: {type(exc).__name__}: {exc}") from exc
        if not isinstance(result, schema):
            raise LlmUnavailable(f"{self.name}: no structured result")
        return result


def ollama_provider(url: str, model: str, temperature: float = 0.5) -> LangChainProvider:
    chat = ChatOllama(model=model, base_url=url, temperature=temperature, num_ctx=8192,
                      client_kwargs={"timeout": 300})
    return LangChainProvider(f"ollama:{model}", chat, method="json_schema")


def openai_compatible_provider(base_url: str, api_key: str, model: str,
                               temperature: float = 0.5) -> LangChainProvider:
    """Any OpenAI-compatible chat API: Groq, OpenRouter, LM Studio, OpenAI, ..."""
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    chat = ChatOpenAI(model=model, base_url=base_url, api_key=api_key, temperature=temperature,
                      timeout=120, max_retries=1)
    return LangChainProvider(f"openai-compatible:{model}", chat, method="function_calling")


class MockProvider:
    """No model at all: every agent uses its deterministic fallback copy."""

    name = "mock"

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T:
        raise LlmUnavailable("mock provider")


Tier = Literal["fast", "smart"]


def make_llm(settings: Settings, tier: Tier = "smart") -> LlmProvider:
    match settings.llm_provider:
        case "ollama":
            model = settings.ollama_model if tier == "smart" else settings.ollama_fast_model
            return ollama_provider(settings.ollama_url, model)
        case "openai":
            model = settings.openai_model if tier == "smart" else settings.openai_fast_model
            return openai_compatible_provider(settings.openai_base_url, settings.openai_api_key, model)
        case "mock":
            return MockProvider()
    raise ValueError(f"unknown LLM_PROVIDER {settings.llm_provider!r}")


@dataclass
class AgentUsage:
    agent: str
    tier: str
    model: str
    calls: int = 0
    failures: int = 0
    seconds: float = 0.0


class LlmRouter:
    """Routes each agent to its model tier and enforces a shared call budget + circuit breaker."""

    def __init__(self, settings: Settings, guard: GuardrailLog | None = None,
                 breaker_threshold: int = 3):
        self.settings = settings
        self.guard = guard
        self.providers = {t: make_llm(settings, t) for t in ("fast", "smart")}
        self.budget = settings.llm_call_budget
        self.calls = 0
        self.consecutive_failures = 0
        self.breaker_threshold = breaker_threshold
        self.open = False
        self.usage: dict[str, AgentUsage] = {}

    def for_agent(self, agent: str, tier: Tier) -> LlmProvider:
        return _Metered(self, agent, tier)

    def report(self) -> list[dict]:
        return [vars(u) | {"seconds": round(u.seconds, 1)} for u in self.usage.values()]


class _Metered:
    def __init__(self, router: LlmRouter, agent: str, tier: Tier):
        self.router, self.agent, self.tier = router, agent, tier
        self.inner = router.providers[tier]
        self.name = f"{self.inner.name} [{tier}]"
        router.usage.setdefault(agent, AgentUsage(agent, tier, self.inner.name))

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T:
        r = self.router
        usage = r.usage[self.agent]
        if isinstance(self.inner, MockProvider):
            raise LlmUnavailable("mock provider")
        if r.open:
            raise LlmUnavailable("circuit breaker open")
        if r.calls >= r.budget:
            if r.guard:
                r.guard.add("budget", "llm_calls", "warn", self.agent, f"budget of {r.budget} reached")
            raise LlmUnavailable("LLM call budget exhausted")
        r.calls += 1
        usage.calls += 1
        started = time.monotonic()
        try:
            result = await self.inner.generate_json(system, user, schema)
        except LlmUnavailable:
            usage.failures += 1
            r.consecutive_failures += 1
            if r.consecutive_failures >= r.breaker_threshold and not r.open:
                r.open = True
                if r.guard:
                    r.guard.add("budget", "circuit_breaker", "warn", self.agent,
                                f"{r.consecutive_failures} consecutive LLM failures; using fallbacks")
            raise
        finally:
            usage.seconds += time.monotonic() - started
        r.consecutive_failures = 0
        return result
