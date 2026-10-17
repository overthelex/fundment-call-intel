"""Deterministic citation checking.

The model is asked to quote verbatim. Here we check every quote against the
parsed transcript instead of trusting it. A claim with no verifiable citation
is flagged, and if no claim survives the answer's confidence is downgraded.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher

from .parse import Call, Turn

FUZZY_MIN = 0.85  # share of the quote that must match one contiguous region
NEIGHBOUR_TURNS = 2  # how far a wrong timestamp may be off


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = re.sub(r"[—–-]", " ", text)
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


@dataclass
class CitationCheck:
    call_id: str
    timestamp: str
    speaker: str
    quote: str
    status: str  # exact | shifted | fuzzy | not_found | unknown_call
    turn: Turn | None = None
    in_context: bool = False

    @property
    def ok(self) -> bool:
        return self.status in ("exact", "shifted", "fuzzy")


def _match(quote: str, turn: Turn) -> str | None:
    q, t = normalize(quote), normalize(turn.text)
    if not q:
        return None
    if q in t:
        return "exact"
    m = SequenceMatcher(None, q, t, autojunk=False).find_longest_match(0, len(q), 0, len(t))
    if m.size / len(q) >= FUZZY_MIN:
        return "fuzzy"
    return None


def check_citation(
    calls: dict[str, Call],
    call_id: str,
    timestamp: str,
    speaker: str,
    quote: str,
    context_turns: set[tuple[str, int]],
) -> CitationCheck:
    out = CitationCheck(call_id, timestamp, speaker, quote, "unknown_call")
    call = calls.get(call_id.strip().upper())
    if call is None:
        return out
    ts = timestamp.strip().lstrip("[").rstrip("]")
    if ts.lower() == "header":
        for t in call.header:
            status = _match(quote, t)
            if status:
                return _found(out, status, t, context_turns)
        out.status = "not_found"
        return out
    speaker = re.sub(r"\s*\(.*\)\s*$", "", speaker).strip()  # "Name (Role, Company)" -> "Name"
    anchors = [t for t in call.turns if t.ts == ts]

    # 1) the turn the model pointed at
    for t in anchors:
        status = _match(quote, t)
        if status:
            return _found(out, status, t, context_turns)
    # 2) neighbouring turns: right quote, slightly wrong timestamp
    for a in anchors:
        lo, hi = max(0, a.idx - NEIGHBOUR_TURNS), min(len(call.turns), a.idx + NEIGHBOUR_TURNS + 1)
        for t in call.turns[lo:hi]:
            if _match(quote, t) == "exact":
                return _found(out, "shifted", t, context_turns)
    # 3) anywhere in the same call, same speaker (timestamp wrong or missing)
    for t in call.turns:
        if t.speaker == speaker and _match(quote, t) == "exact":
            return _found(out, "shifted", t, context_turns)
    out.status = "not_found"
    return out


def _found(out: CitationCheck, status: str, turn: Turn, context_turns: set[tuple[str, int]]) -> CitationCheck:
    out.status = status
    out.turn = turn
    out.in_context = (turn.call_id, turn.idx) in context_turns
    return out
