from __future__ import annotations

import json
import logging
import re
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError

from newsroom.config import Settings
from newsroom.net import async_http_client

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class LlmUnavailable(Exception):
    """The provider cannot produce an answer; agents fall back to deterministic copy."""


class LlmProvider(Protocol):
    name: str

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T: ...


def _extract_json(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return match.group(0) if match else text


def _schema_hint(schema: type[BaseModel]) -> str:
    return (
        "Respond with a single JSON object only, no prose, matching this JSON schema:\n"
        + json.dumps(schema.model_json_schema())
    )


class _RetryingProvider:
    name = "base"
    max_attempts = 3

    async def _chat(self, messages: list[dict], schema: type[BaseModel]) -> str:
        raise NotImplementedError

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T:
        messages = [
            {"role": "system", "content": f"{system}\n\n{_schema_hint(schema)}"},
            {"role": "user", "content": user},
        ]
        last_error: Exception | None = None
        for _ in range(self.max_attempts):
            try:
                raw = await self._chat(messages, schema)
            except Exception as exc:
                raise LlmUnavailable(f"{self.name}: {exc}") from exc
            try:
                return schema.model_validate_json(_extract_json(raw))
            except ValidationError as exc:
                last_error = exc
                messages += [
                    {"role": "assistant", "content": raw},
                    {"role": "user", "content": f"That JSON was invalid: {exc.errors()[:3]}. "
                                                "Return corrected JSON only."},
                ]
        raise LlmUnavailable(f"{self.name}: invalid JSON after retries: {last_error}")


class OllamaProvider(_RetryingProvider):
    def __init__(self, url: str, model: str, temperature: float = 0.5):
        self.url, self.model, self.temperature = url.rstrip("/"), model, temperature
        self.name = f"ollama:{model}"

    async def _chat(self, messages: list[dict], schema: type[BaseModel]) -> str:
        async with async_http_client(timeout=300) as client:
            resp = await client.post(
                f"{self.url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "format": schema.model_json_schema(),
                    "options": {"temperature": self.temperature, "num_ctx": 8192},
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]


class OpenAICompatibleProvider(_RetryingProvider):
    """Any OpenAI-compatible chat API: Groq, OpenRouter, LM Studio, OpenAI, ..."""

    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.5):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model
        self.temperature = temperature
        self.name = f"openai-compatible:{model}"

    async def _chat(self, messages: list[dict], schema: type[BaseModel]) -> str:
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        async with async_http_client(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": self.temperature,
                    "response_format": {"type": "json_object"},
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]


class MockProvider:
    """No model at all: every agent uses its deterministic fallback copy."""

    name = "mock"

    async def generate_json(self, system: str, user: str, schema: type[T]) -> T:
        raise LlmUnavailable("mock provider")


def make_llm(settings: Settings) -> LlmProvider:
    match settings.llm_provider:
        case "ollama":
            return OllamaProvider(settings.ollama_url, settings.ollama_model)
        case "openai":
            return OpenAICompatibleProvider(
                settings.openai_base_url, settings.openai_api_key, settings.openai_model
            )
        case "mock":
            return MockProvider()
    raise ValueError(f"unknown LLM_PROVIDER {settings.llm_provider!r}")
