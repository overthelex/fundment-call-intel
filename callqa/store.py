"""The ingestion store: what is read from each call once, when the call arrives.

One SQLite file (`.cache/callqa.db`). `ingest` is the handler a new or changed call would trigger:
it is idempotent by call id and a digest of the call's content, the model and the prompt versions,
so an unchanged call costs nothing and a changed one is re-read in a single transaction. Reads at
question time are filters and a vector ranking over these rows, never a re-read of the transcripts.
The same tables map onto Postgres + pgvector unchanged when one file is no longer enough.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from . import claims as claims_mod
from . import notes as notes_mod
from .claims import StoredClaim
from .llm import LLM, Usage
from .notes import StoredNote
from .parse import Call

SCHEMA = """
CREATE TABLE IF NOT EXISTS calls (
    call_id TEXT PRIMARY KEY, digest TEXT NOT NULL, company TEXT, category TEXT, stage TEXT, date TEXT
);
CREATE TABLE IF NOT EXISTS claims (
    call_id TEXT NOT NULL, turn_idx INTEGER NOT NULL, topic TEXT NOT NULL,
    statement TEXT, speaker TEXT, quote TEXT
);
CREATE TABLE IF NOT EXISTS notes (
    call_id TEXT NOT NULL, turn_idx INTEGER NOT NULL, field TEXT NOT NULL,
    point TEXT, speaker TEXT, quote TEXT, vector BLOB
);
CREATE INDEX IF NOT EXISTS notes_by_call_field ON notes (call_id, field);
CREATE INDEX IF NOT EXISTS claims_by_topic ON claims (topic);
"""


# Calls read at once; each read is two parallel LLM calls. 20 calls x 2 stay far below the deployment's
# limits (gpt-5.4-mini: 1M tokens and 1,000 requests per minute); 429s are retried by the client.
INGEST_WORKERS = int(os.environ.get("INGEST_WORKERS", "20"))


def digest(call: Call, llm: LLM) -> str:
    raw = "\x00".join(t.text for t in call.turns) + llm.chat_model + llm.embed_model
    raw += claims_mod.PROMPT_VERSION + notes_mod.PROMPT_VERSION
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def merge_claims(*passes: list[StoredClaim]) -> list[StoredClaim]:
    """Union of several extraction passes over one call, one claim per turn and topic."""
    seen, out = set(), []
    for c in (c for p in passes for c in p):
        if (c.turn_idx, c.topic) not in seen:
            seen.add((c.turn_idx, c.topic))
            out.append(c)
    return sorted(out, key=lambda c: c.turn_idx)


class Store:
    def __init__(self, calls: list[Call], llm: LLM, path: Path = Path(".cache/callqa.db")) -> None:
        self.calls = {c.call_id: c for c in calls}
        self.llm = llm
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self._ready = False
        # one connection shared by the eval's worker threads: ingestion and reads take turns, and a
        # first question asked from several threads at once ingests once
        self._lock = threading.RLock()

    # -- ingestion ---------------------------------------------------------

    def stale(self) -> list[Call]:
        have = dict(self.db.execute("SELECT call_id, digest FROM calls"))
        return [c for c in self.calls.values() if have.get(c.call_id) != digest(c, self.llm)]

    def read(self, call: Call, usage: Usage | None = None) -> tuple[list[StoredClaim], list[StoredNote], np.ndarray]:
        """The LLM work for one call; no database access, so calls can be read in parallel.

        Vendor claims are extracted twice, in parallel, and merged: one pass can miss a single short
        reply ("That's fine, it's completely no-code" was missing from one index), and a missed claim
        is a missed contradiction for every question about the vendor's consistency. An empty result
        is retried once: on a fresh index the extraction occasionally came back empty for a whole call."""
        def claims() -> list[StoredClaim]:
            return claims_mod.extract(call, self.calls, self.llm, usage)

        def notes() -> list[StoredNote]:
            return notes_mod.extract(call, self.calls, self.llm, usage) or notes_mod.extract(call, self.calls, self.llm, usage)

        with ThreadPoolExecutor(3) as pool:  # independent reads of the same call
            cl_a, cl_b, ns_f = pool.submit(claims), pool.submit(claims), pool.submit(notes)
            cl = merge_claims(cl_a.result(), cl_b.result()) or claims()
            ns = ns_f.result()
        if not cl or not ns:
            print(f"warning: {call.call_id} has {len(cl)} vendor claims and {len(ns)} notes after a retry",
                  file=sys.stderr, flush=True)
        vecs = np.zeros((0, 0), dtype=np.float32)
        if ns:
            vecs = np.asarray(self.llm.embed([f"{n.field}: {n.point}" for n in ns], usage=usage), dtype=np.float32)
            vecs /= np.linalg.norm(vecs, axis=1, keepdims=True)
        return cl, ns, vecs

    def write(self, call: Call, cl: list[StoredClaim], ns: list[StoredNote], vecs: np.ndarray) -> None:
        with self.db:  # one transaction: a call is either fully replaced or untouched
            self.db.execute("DELETE FROM claims WHERE call_id = ?", (call.call_id,))
            self.db.execute("DELETE FROM notes WHERE call_id = ?", (call.call_id,))
            self.db.executemany(
                "INSERT INTO claims VALUES (?, ?, ?, ?, ?, ?)",
                [(c.call_id, c.turn_idx, c.topic, c.statement, c.speaker, c.quote) for c in cl])
            self.db.executemany(
                "INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(n.call_id, n.turn_idx, n.field, n.point, n.speaker, n.quote, v.tobytes()) for n, v in zip(ns, vecs)])
            self.db.execute(
                "INSERT OR REPLACE INTO calls VALUES (?, ?, ?, ?, ?, ?)",
                (call.call_id, digest(call, self.llm), call.company, call.category, call.stage, call.date))

    def ingest(self, usage: Usage | None = None, workers: int = INGEST_WORKERS) -> int:
        """Read every new or changed call; returns how many were (re)read."""
        with self._lock:
            todo = self.stale()
            if todo:
                print(f"ingesting {len(todo)} new or changed calls (once, {workers} at a time)",
                      file=sys.stderr, flush=True)
            with ThreadPoolExecutor(workers) as pool:
                for call, (cl, ns, vecs) in zip(todo, pool.map(lambda c: self.read(c, usage), todo)):
                    self.write(call, cl, ns, vecs)
            self._ready = True
            return len(todo)

    def ensure(self, usage: Usage | None = None) -> None:
        if not self._ready:
            with self._lock:
                if not self._ready:
                    self.ingest(usage)

    # -- reads -------------------------------------------------------------

    def claims(self) -> list[StoredClaim]:
        with self._lock:
            rows = self.db.execute("SELECT call_id, turn_idx, topic, statement, speaker, quote FROM claims "
                                   "ORDER BY call_id, turn_idx").fetchall()
        return [StoredClaim(call_id=r[0], turn_idx=r[1], topic=r[2], statement=r[3], speaker=r[4], quote=r[5])
                for r in rows]

    def notes(self, call_ids: list[str], fields: list[str] | None = None) -> tuple[list[StoredNote], np.ndarray]:
        q = f"SELECT call_id, turn_idx, field, point, speaker, quote, vector FROM notes " \
            f"WHERE call_id IN ({','.join('?' * len(call_ids))})"
        args: list = list(call_ids)
        if fields:
            q += f" AND field IN ({','.join('?' * len(fields))})"
            args += fields
        with self._lock:
            rows = self.db.execute(q + " ORDER BY call_id, turn_idx", args).fetchall()
        ns = [StoredNote(call_id=r[0], turn_idx=r[1], field=r[2], point=r[3], speaker=r[4], quote=r[5]) for r in rows]
        vecs = np.stack([np.frombuffer(r[6], dtype=np.float32) for r in rows]) if rows else np.zeros((0, 0))
        return ns, vecs

    def counts(self) -> dict[str, int]:
        with self._lock:
            return {t: self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("calls", "claims", "notes")}
