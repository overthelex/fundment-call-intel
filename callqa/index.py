"""Chunking and hybrid (BM25 + dense) retrieval over transcript turns.

Chunks are windows of consecutive turns inside one call. Conversation is
messy (sentences broken across turns, interruptions), so a window keeps a
question together with its answer; the overlap stops a point being cut in two.
Each chunk carries a short call header so the embedding knows whose call it is.
"""

from __future__ import annotations

import hashlib
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rank_bm25 import BM25Okapi

from .llm import LLM
from .parse import Call, Turn

WINDOW_WORDS = 180
OVERLAP_TURNS = 2
RRF_K = 60

_STOP = set(
    "a an the and or but if of to in on at for with is are was were be been it its this that "
    "i you we they he she um uh like so yeah okay just do does did have has had not no".split()
)


@dataclass
class Chunk:
    chunk_id: str
    call_id: str
    turns: list[Turn]
    text: str  # what gets embedded / BM25-indexed

    @property
    def span(self) -> str:
        return f"{self.turns[0].ts}-{self.turns[-1].ts}"


def turn_line(call: Call, t: Turn) -> str:
    p = call.speaker(t.speaker)
    who = f"{t.speaker} ({p.role}, {p.company})" if p else t.speaker
    return f"[{t.ts}] {who}: {t.text}"


def chunk_call(call: Call) -> list[Chunk]:
    header = f"{call.call_id} · {call.company} ({call.industry}) · {call.category} · {call.stage}"
    chunks: list[Chunk] = []
    start = 0
    while start < len(call.turns):
        end, words = start, 0
        while end < len(call.turns) and (words < WINDOW_WORDS or end - start < 3):
            words += len(call.turns[end].text.split())
            end += 1
        window = call.turns[start:end]
        body = "\n".join(turn_line(call, t) for t in window)
        chunks.append(Chunk(f"{call.call_id}#{len(chunks)}", call.call_id, window, f"{header}\n{body}"))
        if end >= len(call.turns):
            break
        start = max(end - OVERLAP_TURNS, start + 1)
    return chunks


def tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in _STOP]


class Index:
    def __init__(self, calls: list[Call], llm: LLM, cache_dir: Path = Path(".cache")) -> None:
        self.calls = {c.call_id: c for c in calls}
        self.chunks = [ch for c in calls for ch in chunk_call(c)]
        self.llm = llm
        self.bm25 = BM25Okapi([tokenize(ch.text) for ch in self.chunks])
        self.vectors = self._load_or_embed(cache_dir)

    def _load_or_embed(self, cache_dir: Path) -> np.ndarray:
        digest = hashlib.sha256(
            ("\x00".join(ch.text for ch in self.chunks) + self.llm.embed_model).encode()
        ).hexdigest()[:16]
        path = cache_dir / f"embeddings-{digest}.npy"
        if path.exists():
            return np.load(path)
        vecs = np.asarray(self.llm.embed([ch.text for ch in self.chunks]), dtype=np.float32)
        vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        np.save(path, vecs)
        return vecs

    def search(
        self,
        queries: list[str],
        call_ids: list[str] | None = None,
        per_call: int = 2,
        top_k: int = 12,
        max_chunks: int = 40,
    ) -> list[tuple[Chunk, float]]:
        """Hybrid search with reciprocal-rank fusion.

        Returns the global top_k chunks plus up to `per_call` best chunks from
        every candidate call. The per-call quota matters for "across the
        dataset" questions: without it, one long call that repeats a keyword
        crowds out the short calls that mention it once.
        """
        allowed = set(call_ids) if call_ids else set(self.calls)
        idx = [i for i, ch in enumerate(self.chunks) if ch.call_id in allowed]
        if not idx:
            return []
        qvecs = np.asarray(self.llm.embed(queries), dtype=np.float32)
        qvecs /= np.linalg.norm(qvecs, axis=1, keepdims=True)

        fused: dict[int, float] = defaultdict(float)
        for q, qv in zip(queries, qvecs):
            dense = self.vectors[idx] @ qv
            sparse = np.asarray(self.bm25.get_scores(tokenize(q)))[idx]
            for scores in (dense, sparse):
                for rank, j in enumerate(np.argsort(-scores)):
                    fused[idx[j]] += 1.0 / (RRF_K + rank)

        ranked = sorted(fused.items(), key=lambda kv: -kv[1])
        picked: dict[int, float] = dict(ranked[:top_k])
        taken: dict[str, int] = defaultdict(int)
        for i, score in ranked:
            cid = self.chunks[i].call_id
            if taken[cid] < per_call:
                taken[cid] += 1
                picked.setdefault(i, score)
        best = sorted(picked.items(), key=lambda kv: -kv[1])[:max_chunks]
        return [(self.chunks[i], s) for i, s in best]
