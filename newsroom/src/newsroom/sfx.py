"""Original sound effects synthesized in code (no third-party audio, no licensing issues)."""

from __future__ import annotations

import numpy as np

ALERT_SECONDS = 1.6


def _env(n: int, attack: int, decay: float, rate: int) -> np.ndarray:
    t = np.arange(n) / rate
    env = np.exp(-t * decay)
    env[:attack] *= np.linspace(0, 1, attack)
    return env


def news_alert(rate: int, seed: int = 7) -> np.ndarray:
    """Whoosh into a bright three-note chime over a low hit, about 1.6 seconds."""
    n = int(ALERT_SECONDS * rate)
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(seed)

    whoosh_n = int(0.42 * rate)
    noise = rng.standard_normal(whoosh_n)
    kernel = np.ones(24) / 24
    noise = noise - np.convolve(noise, kernel, mode="same")
    out[:whoosh_n] += noise * np.linspace(0, 1, whoosh_n) ** 2 * 0.18

    hit_at = int(0.4 * rate)
    hit_n = int(0.9 * rate)
    t = np.arange(hit_n) / rate
    sweep = 2 * np.pi * (95 * t - 30 * t**2)
    out[hit_at:hit_at + hit_n] += np.sin(sweep) * _env(hit_n, 60, 6.0, rate) * 0.55

    for i, freq in enumerate((659.25, 880.0, 1318.5)):
        start = hit_at + int(i * 0.11 * rate)
        m = min(int(0.8 * rate), n - start)
        t = np.arange(m) / rate
        tone = np.sin(2 * np.pi * freq * t) + 0.35 * np.sin(4 * np.pi * freq * t) \
            + 0.12 * np.sin(6 * np.pi * freq * t)
        out[start:start + m] += tone * _env(m, 40, 5.5, rate) * 0.22

    out *= np.linspace(1, 0, n) ** 0.3
    peak = np.max(np.abs(out)) or 1.0
    return (out / peak * 0.55).astype(np.float32)
