"""Map step for questions across many calls: one reader per call, in parallel.

Retrieval returns the passages most similar to the question. For "which customers mentioned X" or
"what do prospects care about", the supporting turns are spread over many calls and often phrased
nothing like the question, so about half of them never reached the answer step (evidence recall 0.54
on retrieved excerpts against 0.96 on whole calls). Here a small, cheap pass reads every candidate
call in full and lists the turns that bear on the question; the answer step then sees those turns,
and a list of the calls that were read and had nothing, so "this list is complete" can be backed.

Every listed quote goes through the citation checker; ones that fail are dropped.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from .index import turn_line
from .llm import LLM, Usage
from .parse import Call, Turn
from .verify import check_citation

MAP_SYSTEM = """You read ONE sales-call transcript. The vendor is OrbitFlow (workflow automation).
A question is being asked across many calls; your job is only to find what THIS call contributes.
List every turn that bears on the question: direct statements, examples, figures, caveats and
corrections, and the other side's reaction when it matters. Be inclusive: a missed turn is a missed
answer, an extra one costs little. If nothing in this call bears on the question, return an empty list.

For each turn:
- timestamp and speaker exactly as shown in the transcript line
- quote: a VERBATIM contiguous span from that single turn (max ~25 words) that carries the point
- point: what it contributes, a few words"""


class MapPoint(BaseModel):
    timestamp: str
    speaker: str
    quote: str
    point: str


class CallNotes(BaseModel):
    points: list[MapPoint]


def read_call(question: str, call: Call, calls: dict[str, Call], llm: LLM,
              usage: Usage | None = None) -> list[Turn]:
    """The turns of one call that bear on the question, as verified by the citation checker."""
    text = "\n".join(turn_line(call, t) for t in call.turns)
    user = f"QUESTION\n{question}\n\n{call.call_id} · {call.company} · {call.stage}\n\n{text}"
    notes = llm.structured(MAP_SYSTEM, user, CallNotes, reasoning_effort="low", usage=usage)
    in_call = {(call.call_id, t.idx) for t in call.turns}
    found: dict[int, Turn] = {}
    for p in notes.points:
        chk = check_citation(calls, call.call_id, p.timestamp, p.speaker, p.quote, in_call)
        if chk.ok and chk.turn is not None:
            found[chk.turn.idx] = chk.turn
    return [found[i] for i in sorted(found)]


def map_calls(question: str, call_ids: list[str], calls: dict[str, Call], llm: LLM,
              usage: Usage | None = None, workers: int = 8) -> dict[str, list[Turn]]:
    """call id -> relevant turns (empty list = read in full, nothing on the question)."""
    with ThreadPoolExecutor(workers) as pool:
        found = pool.map(lambda cid: read_call(question, calls[cid], calls, llm, usage), call_ids)
        return dict(zip(call_ids, found))
