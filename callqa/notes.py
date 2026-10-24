"""Per-call notes, written once when a call is ingested.

A question across calls ("which customers mentioned X", "what do prospects care about", "how are
renewals handled") needs the supporting turns from every call, and retrieval by similarity to the
question reaches only about half of them. Reading every call at question time (the map step) fixes
that but costs a full read of the dataset per question. Here each call is read once, at ingestion,
into notes under fixed fields, each tied to a verified turn; a question then selects notes by field
and similarity, which costs the same at 20 calls as at 20,000.

The fields are what sales questions are about; a question outside them still gets retrieved excerpts.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from .index import turn_line
from .llm import INGEST_TIMEOUT, LLM, Usage
from .parse import Call
from .verify import check_citation

PROMPT_VERSION = "notes-v2"  # v2: customer questions about capabilities are needs

NoteField = Literal[
    "needs and requirements",
    "pains and current process",
    "objections, risks and concerns",
    "competitors and current tools",
    "integrations and systems",
    "pricing, budget and commercial terms",
    "decision process and timeline",
    "buying signals and next steps",
    "outcome and account health",
    "how the OrbitFlow team ran the call",
]

NOTES_SYSTEM = """You read one sales-call transcript. The vendor is OrbitFlow (workflow automation).
Write notes that will later answer questions across many calls, so be exhaustive and concrete. Use
the fields:
- needs and requirements: capabilities, must-haves, use cases the customer asks for or describes
- pains and current process: how they work today, what breaks, workarounds, who owns what
- objections, risks and concerns: doubts, blockers, gates (security, legal, budget, people)
- competitors and current tools: tools in use or under evaluation, and what is said about them
- integrations and systems: systems that must connect, connector gaps, APIs
- pricing, budget and commercial terms: prices, budgets, discounts, uplifts, usage, contract terms
- decision process and timeline: who decides, approvals, dates, deadlines, notice periods
- buying signals and next steps: interest, pilots, follow-ups agreed, and their absence
- outcome and account health: churn reasons, renewal risk, usage trends, satisfaction
- how the OrbitFlow team ran the call: how reps opened, who led, what they offered or conceded,
  promises made, how they handled pushback
One note per distinct point; corrections, caveats and figures are their own notes. Skip small talk.
A customer's question about a capability ("Can we export audit logs to our own SIEM?", "Is there
version history?", "Can we switch AI off?", "Can the queue be owned by a team?") tells you what they
need: note it under needs and requirements, whatever the answer was.

For each note:
- field: the closest field
- point: the point in one short sentence, faithful to the speaker's wording and certainty
- timestamp and speaker exactly as shown in the transcript line
- quote: a VERBATIM contiguous span from that single turn (max ~25 words) that carries the point"""


class CallNote(BaseModel):
    field: NoteField
    point: str
    timestamp: str
    speaker: str
    quote: str


class CallNotes(BaseModel):
    notes: list[CallNote]


class StoredNote(BaseModel):
    call_id: str
    turn_idx: int
    field: str
    point: str
    speaker: str
    quote: str


def extract(call: Call, calls: dict[str, Call], llm: LLM, usage: Usage | None = None) -> list[StoredNote]:
    """Notes for one call; a note whose quote does not verify against the transcript is dropped."""
    text = "\n".join(turn_line(call, t) for t in call.turns)
    out = llm.structured(NOTES_SYSTEM, f"{call.call_id} · {call.company} · {call.stage}\n\n{text}", CallNotes,
                         reasoning_effort="medium", usage=usage, timeout=INGEST_TIMEOUT)
    in_call = {(call.call_id, t.idx) for t in call.turns}
    kept = []
    for n in out.notes:
        chk = check_citation(calls, call.call_id, n.timestamp, n.speaker, n.quote, in_call)
        if chk.ok and chk.turn is not None:
            kept.append(StoredNote(call_id=call.call_id, turn_idx=chk.turn.idx, field=n.field,
                                   point=n.point, speaker=chk.turn.speaker, quote=n.quote))
    return kept
