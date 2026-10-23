"""The ingestion store: what is read from each call once, when the call arrives.

One SQLite file (`.cache/callqa.db`). `ingest` is the handler a new or changed call would trigger:
it is idempotent by call id and a digest of the call's content, the model and the prompt versions,
so an unchanged call costs nothing and a changed one is re-read in a single transaction. Reads at
question time are filters and a vector ranking over these rows, never a re-read of the transcripts.
The same tables map onto Postgres + pgvector unchanged when one file is no longer enough.
"""

from __future__ import annotations

import hashlib
import sqlite3
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


def digest(call: Call, llm: LLM) -> str:
    raw = "\x00".join(t.text for t in call.turns) + llm.chat_model + llm.embed_model
    raw += claims_mod.PROMPT_VERSION + notes_mod.PROMPT_VERSION
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class Store:
    def __init__(self, calls: list[Call], llm: LLM, path: Path = Path(".cache/callqa.db")) -> None:
        self.calls = {c.call_id: c for c in calls}
        self.llm = llm
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self._ready = False

    # -- ingestion ---------------------------------------------------------

    def stale(self) -> list[Call]:
        have = dict(self.db.execute("SELECT call_id, digest FROM calls"))
        return [c for c in self.calls.values() if have.get(c.call_id) != digest(c, self.llm)]

    def read(self, call: Call, usage: Usage | None = None) -> tuple[list[StoredClaim], list[StoredNote], np.ndarray]:
        """The LLM work for one call; no database access, so calls can be read in parallel."""
        cl = claims_mod.extract(call, self.calls, self.llm, usage)
        ns = notes_mod.extract(call, self.calls, self.llm, usage)
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

    def ingest(self, usage: Usage | None = None, workers: int = 8) -> int:
        """Read every new or changed call; returns how many were (re)read."""
        todo = self.stale()
        with ThreadPoolExecutor(workers) as pool:
            for call, (cl, ns, vecs) in zip(todo, pool.map(lambda c: self.read(c, usage), todo)):
                self.write(call, cl, ns, vecs)
        self._ready = True
        return len(todo)

    def ensure(self, usage: Usage | None = None) -> None:
        if not self._ready:
            self.ingest(usage)

    # -- reads -------------------------------------------------------------

    def claims(self) -> list[StoredClaim]:
        rows = self.db.execute("SELECT call_id, turn_idx, topic, statement, speaker, quote FROM claims "
                               "ORDER BY call_id, turn_idx")
        return [StoredClaim(call_id=r[0], turn_idx=r[1], topic=r[2], statement=r[3], speaker=r[4], quote=r[5])
                for r in rows]

    def notes(self, call_ids: list[str], fields: list[str] | None = None) -> tuple[list[StoredNote], np.ndarray]:
        q = f"SELECT call_id, turn_idx, field, point, speaker, quote, vector FROM notes " \
            f"WHERE call_id IN ({','.join('?' * len(call_ids))})"
        args: list = list(call_ids)
        if fields:
            q += f" AND field IN ({','.join('?' * len(fields))})"
            args += fields
        rows = self.db.execute(q + " ORDER BY call_id, turn_idx", args).fetchall()
        ns = [StoredNote(call_id=r[0], turn_idx=r[1], field=r[2], point=r[3], speaker=r[4], quote=r[5]) for r in rows]
        vecs = np.stack([np.frombuffer(r[6], dtype=np.float32) for r in rows]) if rows else np.zeros((0, 0))
        return ns, vecs

    def counts(self) -> dict[str, int]:
        return {t: self.db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("calls", "claims", "notes")}
