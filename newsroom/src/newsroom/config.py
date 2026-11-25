from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DISCLAIMER = (
    "This show is for information and entertainment only and is not financial or medical advice. "
    "Do your own research before investing."
)

INDICES = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "^DJI": "Dow Jones"}

WATCHLIST = {
    "NVDA": "Nvidia",
    "MSFT": "Microsoft",
    "AAPL": "Apple",
    "GOOGL": "Alphabet",
    "AMZN": "Amazon",
    "META": "Meta",
    "TSLA": "Tesla",
    "AMD": "AMD",
    "AVGO": "Broadcom",
    "TSM": "TSMC",
    "ORCL": "Oracle",
    "PLTR": "Palantir",
    "MRNA": "Moderna",
    "VRTX": "Vertex",
    "REGN": "Regeneron",
    "RXRX": "Recursion",
}


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).lower() in {"1", "true", "yes", "on"}


@dataclass
class Settings:
    show_name: str = field(default_factory=lambda: _env("SHOW_NAME", "Bits & Bulls"))
    offline: bool = field(default_factory=lambda: _bool("NEWSROOM_OFFLINE"))

    llm_provider: str = field(default_factory=lambda: _env("LLM_PROVIDER", "ollama"))
    ollama_url: str = field(default_factory=lambda: _env("OLLAMA_URL", "http://localhost:11434"))
    ollama_model: str = field(default_factory=lambda: _env("OLLAMA_MODEL", "qwen2.5:14b"))
    ollama_fast_model: str = field(default_factory=lambda: _env("OLLAMA_FAST_MODEL", "llama3.2"))
    openai_base_url: str = field(
        default_factory=lambda: _env("OPENAI_BASE_URL", "https://api.groq.com/openai/v1")
    )
    openai_api_key: str = field(default_factory=lambda: _env("OPENAI_API_KEY", ""))
    openai_model: str = field(
        default_factory=lambda: _env("OPENAI_MODEL", "llama-3.3-70b-versatile")
    )
    openai_fast_model: str = field(
        default_factory=lambda: _env("OPENAI_FAST_MODEL", "llama-3.1-8b-instant")
    )
    llm_call_budget: int = field(default_factory=lambda: int(_env("LLM_CALL_BUDGET", "40")))
    human_review: bool = field(default_factory=lambda: _bool("HUMAN_REVIEW"))

    tts_provider: str = field(default_factory=lambda: _env("TTS_PROVIDER", "kokoro"))
    anchor_a_name: str = field(default_factory=lambda: _env("ANCHOR_A_NAME", "Maya"))
    anchor_a_voice: str = field(default_factory=lambda: _env("ANCHOR_A_VOICE", "af_heart"))
    anchor_b_name: str = field(default_factory=lambda: _env("ANCHOR_B_NAME", "Leo"))
    anchor_b_voice: str = field(default_factory=lambda: _env("ANCHOR_B_VOICE", "am_michael"))
    kokoro_speed: float = field(default_factory=lambda: float(_env("KOKORO_SPEED", "1.05")))

    embedder: str = field(default_factory=lambda: _env("EMBEDDER", "hashing"))
    ollama_embed_model: str = field(
        default_factory=lambda: _env("OLLAMA_EMBED_MODEL", "nomic-embed-text")
    )

    stories_per_show: int = field(default_factory=lambda: int(_env("STORIES_PER_SHOW", "5")))
    max_seconds: float = field(default_factory=lambda: float(_env("MAX_SECONDS", "235")))
    fps: int = 30

    out_dir: Path = field(default_factory=lambda: Path(_env("OUT_DIR", str(ROOT / "out"))))
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(ROOT / "data"))))

    @property
    def anchor_names(self) -> dict[str, str]:
        return {"a": self.anchor_a_name, "b": self.anchor_b_name}

    @property
    def db_path(self) -> Path:
        return self.data_dir / "newsroom.db"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    def server_env(self) -> dict[str, str]:
        return {
            "NEWSROOM_OFFLINE": "1" if self.offline else "0",
            "EMBEDDER": self.embedder,
            "OLLAMA_URL": self.ollama_url,
            "OLLAMA_EMBED_MODEL": self.ollama_embed_model,
            "DATA_DIR": str(self.data_dir),
        }


load_dotenv(ROOT / ".env")
