from __future__ import annotations

import hashlib
import itertools
import re
from typing import Protocol

import numpy as np

from newsroom.net import http_client

WORD_RE = re.compile(r"[a-z0-9]+")


class Embedder(Protocol):
    name: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


class HashingEmbedder:
    """Offline feature-hashing embedder over unigrams and bigrams."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.name = f"hashing-{dim}"

    def _vector(self, text: str) -> np.ndarray:
        words = WORD_RE.findall(text.lower())
        feats = words + [f"{a}_{b}" for a, b in itertools.pairwise(words)]
        vec = np.zeros(self.dim, dtype=np.float32)
        for f in feats:
            h = int.from_bytes(hashlib.md5(f.encode()).digest()[:4], "little")
            vec[h % self.dim] += 1.0 if (h >> 31) & 1 else -1.0
        norm = np.linalg.norm(vec)
        return vec / norm if norm else vec

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vector(t) for t in texts]) if texts else np.zeros((0, self.dim))


class OllamaEmbedder:
    def __init__(self, url: str, model: str):
        self.url = url.rstrip("/")
        self.model = model
        self.name = f"ollama-{model}"

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, 1), dtype=np.float32)
        with http_client(timeout=120) as client:
            resp = client.post(f"{self.url}/api/embed", json={"model": self.model, "input": texts})
            resp.raise_for_status()
        vecs = np.asarray(resp.json()["embeddings"], dtype=np.float32)
        return vecs / np.linalg.norm(vecs, axis=1, keepdims=True).clip(min=1e-9)


def make_embedder(kind: str, ollama_url: str = "", ollama_model: str = "") -> Embedder:
    if kind == "ollama":
        return OllamaEmbedder(ollama_url, ollama_model)
    return HashingEmbedder()
