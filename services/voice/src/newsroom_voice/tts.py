from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path
from typing import ClassVar, Protocol

import numpy as np
import soundfile as sf
from newsroom_core.config import Settings
from newsroom_core.net import http_client

from newsroom_voice.speech import normalize_for_speech

log = logging.getLogger(__name__)

KOKORO_RELEASE = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0"
KOKORO_FILES = ["kokoro-v1.0.onnx", "voices-v1.0.bin"]
SAMPLE_RATE = 24000


class TtsEngine(Protocol):
    name: str
    sample_rate: int

    def synth(self, text: str, speaker: str) -> np.ndarray: ...


def download_kokoro(models_dir: Path) -> None:
    models_dir.mkdir(parents=True, exist_ok=True)
    for name in KOKORO_FILES:
        target = models_dir / name
        if target.exists():
            continue
        log.info("downloading %s ...", name)
        tmp = target.with_suffix(".part")
        with http_client(timeout=600) as client, client.stream("GET", f"{KOKORO_RELEASE}/{name}") as r:
            r.raise_for_status()
            with tmp.open("wb") as fh:
                for chunk in r.iter_bytes(1 << 20):
                    fh.write(chunk)
        tmp.rename(target)


class KokoroTts:
    """Kokoro-82M (Apache-2.0) via ONNX: free, local, commercially usable voices."""

    sample_rate = SAMPLE_RATE

    def __init__(self, models_dir: Path, voices: dict[str, str], speed: float):
        from kokoro_onnx import Kokoro

        download_kokoro(models_dir)
        self.kokoro = Kokoro(str(models_dir / KOKORO_FILES[0]), str(models_dir / KOKORO_FILES[1]))
        self.voices, self.speed = voices, speed
        self.name = "kokoro:" + "+".join(voices.values())

    def synth(self, text: str, speaker: str) -> np.ndarray:
        samples, rate = self.kokoro.create(
            normalize_for_speech(text), voice=self.voices[speaker], speed=self.speed, lang="en-us"
        )
        if rate != self.sample_rate:
            raise RuntimeError(f"unexpected sample rate {rate}")
        return np.asarray(samples, dtype=np.float32)


class SayTts:
    """macOS `say` — handy for quick local previews; not licensed for published content."""

    sample_rate = SAMPLE_RATE
    name = "macos-say"
    voices: ClassVar[dict[str, str]] = {"a": "Samantha", "b": "Daniel"}

    def synth(self, text: str, speaker: str) -> np.ndarray:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "s.wav"
            subprocess.run(
                ["say", "-v", self.voices.get(speaker, "Samantha"), "-o", str(out),
                 f"--data-format=LEI16@{SAMPLE_RATE}", normalize_for_speech(text)],
                check=True,
            )
            data, _ = sf.read(out, dtype="float32")
        return data


class SilentTts:
    """Silence sized like speech (2.6 words/s); for tests and dry runs."""

    sample_rate = SAMPLE_RATE
    name = "silent"

    def synth(self, text: str, speaker: str) -> np.ndarray:
        seconds = max(0.6, len(text.split()) / 2.6)
        return np.zeros(int(seconds * self.sample_rate), dtype=np.float32)


def make_tts(settings: Settings) -> TtsEngine:
    match settings.tts_provider:
        case "kokoro":
            return KokoroTts(
                settings.models_dir,
                {"a": settings.anchor_a_voice, "b": settings.anchor_b_voice},
                settings.kokoro_speed,
            )
        case "say":
            return SayTts()
        case "silent":
            return SilentTts()
    raise ValueError(f"unknown TTS_PROVIDER {settings.tts_provider!r}")
