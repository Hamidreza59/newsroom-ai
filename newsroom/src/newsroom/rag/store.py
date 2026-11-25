from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from newsroom.rag.embedder import Embedder

SCHEMA = """
CREATE TABLE IF NOT EXISTS docs (
    id TEXT NOT NULL,
    collection TEXT NOT NULL,
    embedder TEXT NOT NULL,
    date TEXT NOT NULL,
    text TEXT NOT NULL,
    meta TEXT NOT NULL,
    vec BLOB NOT NULL,
    PRIMARY KEY (id, collection, embedder)
);
CREATE INDEX IF NOT EXISTS docs_coll_date ON docs (collection, embedder, date);
CREATE TABLE IF NOT EXISTS segments (
    kind TEXT NOT NULL,
    key TEXT NOT NULL,
    date TEXT NOT NULL,
    payload TEXT NOT NULL,
    PRIMARY KEY (kind, date)
);
"""


@dataclass
class Hit:
    id: str
    text: str
    date: str
    meta: dict
    similarity: float


class VectorStore:
    """Small SQLite-backed vector store; brute-force cosine search is plenty at this scale."""

    def __init__(self, path: Path | str, embedder: Embedder):
        self.embedder = embedder
        if str(path) != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.RLock()
        self.db.executescript(SCHEMA)

    def add(self, collection: str, docs: list[tuple[str, str, str, dict]]) -> int:
        """docs: (id, date, text, meta)"""
        if not docs:
            return 0
        vecs = self.embedder.embed([d[2] for d in docs])
        rows = [
            (doc_id, collection, self.embedder.name, date, text, json.dumps(meta),
             vec.astype(np.float32).tobytes())
            for (doc_id, date, text, meta), vec in zip(docs, vecs, strict=True)
        ]
        with self.lock:
            self.db.executemany("INSERT OR REPLACE INTO docs VALUES (?,?,?,?,?,?,?)", rows)
            self.db.commit()
        return len(rows)

    def count(self, collection: str) -> int:
        cur = self.db.execute(
            "SELECT COUNT(*) FROM docs WHERE collection=? AND embedder=?",
            (collection, self.embedder.name),
        )
        return cur.fetchone()[0]

    def search(self, collection: str, query: str, k: int = 3, since: str | None = None,
               until: str | None = None) -> list[Hit]:
        """Cosine search; `since` is inclusive, `until` exclusive (ISO dates)."""
        sql = "SELECT id, date, text, meta, vec FROM docs WHERE collection=? AND embedder=?"
        args: list = [collection, self.embedder.name]
        if since:
            sql += " AND date >= ?"
            args.append(since)
        if until:
            sql += " AND date < ?"
            args.append(until)
        with self.lock:
            rows = self.db.execute(sql, args).fetchall()
        if not rows:
            return []
        matrix = np.stack([np.frombuffer(r[4], dtype=np.float32) for r in rows])
        q = self.embedder.embed([query])[0]
        sims = matrix @ q
        order = np.argsort(-sims)[:k]
        return [
            Hit(rows[i][0], rows[i][2], rows[i][1], json.loads(rows[i][3]), float(sims[i]))
            for i in order
        ]


class SegmentLog:
    """Remembers recurring segments (explainer topics, quizzes) across shows."""

    def __init__(self, store: VectorStore):
        self.db, self.lock = store.db, store.lock

    def record(self, kind: str, key: str, date: str, payload: dict) -> None:
        with self.lock:
            self.db.execute("INSERT OR REPLACE INTO segments VALUES (?,?,?,?)",
                            (kind, key, date, json.dumps(payload)))
            self.db.commit()

    def recent(self, kind: str, since: str, before: str) -> list[dict]:
        with self.lock:
            rows = self.db.execute(
                "SELECT key, date, payload FROM segments WHERE kind=? AND date>=? AND date<? "
                "ORDER BY date DESC", (kind, since, before)).fetchall()
        return [{"key": k, "date": d, "payload": json.loads(p)} for k, d, p in rows]


def chunk_markdown(text: str) -> list[tuple[str, str]]:
    """Split markdown into (heading, body) chunks at ## headings."""
    chunks, heading, body = [], "", []
    for line in text.splitlines():
        if line.startswith("## "):
            if body:
                chunks.append((heading, "\n".join(body).strip()))
            heading, body = line[3:].strip(), []
        elif not line.startswith("# "):
            body.append(line)
    if body:
        chunks.append((heading, "\n".join(body).strip()))
    return [(h, b) for h, b in chunks if b]
