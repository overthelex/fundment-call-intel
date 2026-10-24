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
from typing import Literal

from pydantic import BaseModel

from .index import call_parts, turn_line
from .llm import CHECK_HEDGE_AFTER, LLM, QUESTION_HEDGE_AFTER, Usage
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
    point: str = ""


class CallNotes(BaseModel):
    points: list[MapPoint]


def read_call(question: str, call: Call, calls: dict[str, Call], llm: LLM,
              usage: Usage | None = None) -> list[tuple[Turn, str]]:
    """The turns of one call (or part of a call) that bear on the question, each with what it
    contributes, as verified by the citation checker."""
    text = "\n".join(turn_line(call, t) for t in call.turns)
    # transcript first, question last: the provider caches the shared prefix, so a call read for
    # several questions is billed once at full price
    user = f"{call.call_id} · {call.company} · {call.stage}\n\n{text}\n\nQUESTION\n{question}"
    notes = llm.structured(MAP_SYSTEM, user, CallNotes, reasoning_effort="low", usage=usage,
                           hedge_after=QUESTION_HEDGE_AFTER)
    in_call = {(call.call_id, t.idx) for t in call.turns}
    found: dict[int, tuple[Turn, str]] = {}
    for p in notes.points:
        chk = check_citation(calls, call.call_id, p.timestamp, p.speaker, p.quote, in_call)
        if chk.ok and chk.turn is not None and chk.turn.idx not in found:
            found[chk.turn.idx] = (chk.turn, p.point)
    return [found[i] for i in sorted(found)]


def map_calls(question: str, call_ids: list[str], calls: dict[str, Call], llm: LLM,
              usage: Usage | None = None) -> dict[str, list[tuple[Turn, str]]]:
    """call id -> relevant turns with their points (empty = read in full, nothing on the question).
    Each call is read in parts (`index.call_parts`), all parts of all calls at once: the slowest
    whole-call read took ~35 s, a part ~10 s."""
    jobs = [(cid, part) for cid in call_ids for part in call_parts(calls[cid])]
    with ThreadPoolExecutor(len(jobs) or 1) as pool:
        res = list(pool.map(lambda j: read_call(question, j[1], calls, llm, usage), jobs))
    out: dict[str, dict[int, tuple[Turn, str]]] = {cid: {} for cid in call_ids}
    for (cid, _), found in zip(jobs, res):
        for t, point in found:
            out[cid].setdefault(t.idx, (t, point))
    return {cid: [v[i] for i in sorted(v)] for cid, v in out.items()}


# -- counting across calls ----------------------------------------------------
#
# "What matters most to prospects?" is a count over calls. The answer step, given every relevant turn
# of ten calls at once, described the themes in general terms and left out a request raised in five
# of them ("Can the queue be owned by a team?"). Here one small call groups the points found in each
# call into items and lists the calls behind each; the count is then done in code.

TALLY_SYSTEM = """You get short points found in several sales calls, one per line as
"CALL-ID [MM:SS] point", all bearing on one question. Group them into items: one item per distinct,
specific ask, capability or reason, the way a product manager would log it ("exception queue owned by a
team, not a named person"; "export audit logs to our own SIEM"; "change-management scenario in the
evaluation"), never a category ("security and governance", "exception handling"). If a group would
hold two different asks, split it; an item usually has 2-6 points. Each point goes under one item.
Keep items raised only once, too. For each item: a short label, and the refs (call id and timestamp,
exactly as given) of its points."""


class TallyRef(BaseModel):
    call_id: str
    timestamp: str


class TallyItem(BaseModel):
    item: str
    refs: list[TallyRef]


class Tally(BaseModel):
    items: list[TallyItem]


def tally(question: str, found: dict[str, list[tuple[Turn, str]]], llm: LLM,
          usage: Usage | None = None) -> list[tuple[str, list[TallyRef]]]:
    """Items with the calls that raise them, most calls first; refs not among the points are dropped."""
    known = {(cid, t.ts) for cid, ps in found.items() for t, _ in ps}
    lines = [f"{cid} [{t.ts}] {point or t.text[:120]}" for cid, ps in found.items() for t, point in ps]
    if not lines:
        return []
    out = llm.structured(TALLY_SYSTEM, f"QUESTION\n{question}\n\nPOINTS\n" + "\n".join(lines), Tally,
                         reasoning_effort="low", usage=usage, hedge_after=QUESTION_HEDGE_AFTER)
    items = []
    for it in out.items:
        refs = [r for r in it.refs if (r.call_id, r.timestamp) in known]
        if refs:
            items.append((it.item, refs))
    return sorted(items, key=lambda x: -len({r.call_id for r in x[1]}))


def render_tally(items: list[tuple[str, list[TallyRef]]], n_calls: int) -> str:
    if not items:
        return ""
    lines = [f"ITEMS COUNTED ACROSS CALLS (each of the {n_calls} calls read in full for this question; "
             "the count is of calls, done in code)"]
    for i, (item, refs) in enumerate(items, 1):
        ids = sorted({r.call_id for r in refs})
        where = ", ".join(f"{r.call_id} [{r.timestamp}]" for r in refs)
        lines.append(f"{i}. {item}: {len(ids)} of {n_calls} calls ({where})")
    return "\n".join(lines)


# -- per-call verdicts --------------------------------------------------------
#
# A question across a few whole calls ("which cold calls produced a follow-up?") needs a verdict for
# every call. With low reasoning the answer step, seeing five transcripts at once, said "all five"
# in 3 of 5 replays, although on one call the prospect said "I won't read it". Here each call is
# read on its own for the question, in parallel, and gives its verdict with the turns behind it;
# the answer step then builds on those verdicts instead of one pass over all calls.

VERDICT_SYSTEM = """You read ONE sales-call transcript. The vendor is OrbitFlow (workflow automation).
A question is being asked across several calls; answer it for THIS call only.
- verdict: what this call contributes, in one or two sentences, faithful to what was actually said and
  how firmly. If the question asks whether something happened (a follow-up, a concern, a metric), say
  plainly yes, no, or only partly, and why. A polite "send it over" followed by "I won't read it" is
  not a real next step; a condition ("only if X") is part of the verdict.
- counts: does this call count toward the answer? "yes", "partly" (conditionally, or only in part) or
  "no" (it did not do or say what the question asks about). For a question that ranks or classifies
  every call, "yes".
- evidence: the turns that support the verdict, including anything that weakens it; for each,
  timestamp and speaker exactly as shown and a VERBATIM contiguous span (max ~25 words) as quote.
If nothing in this call bears on the question, say so in the verdict and leave evidence empty."""


class CallVerdict(BaseModel):
    verdict: str
    counts: Literal["yes", "partly", "no"]
    evidence: list[MapPoint]


class Finding(BaseModel):
    call_id: str
    company: str
    verdict: str
    counts: str = "yes"
    evidence: list[MapPoint]  # verified only


def judge_call(question: str, call: Call, calls: dict[str, Call], llm: LLM,
               usage: Usage | None = None) -> Finding:
    text = "\n".join(turn_line(call, t) for t in call.turns)
    # transcript first, question last: the provider caches the shared prefix, so a call read for
    # several questions is billed once at full price
    user = f"{call.call_id} · {call.company} · {call.stage}\n\n{text}\n\nQUESTION\n{question}"
    out = llm.structured(VERDICT_SYSTEM, user, CallVerdict, reasoning_effort="low", usage=usage,
                         hedge_after=CHECK_HEDGE_AFTER)
    in_call = {(call.call_id, t.idx) for t in call.turns}
    kept = []
    for p in out.evidence:
        chk = check_citation(calls, call.call_id, p.timestamp, p.speaker, p.quote, in_call)
        if chk.ok and chk.turn is not None:
            kept.append(MapPoint(timestamp=chk.turn.ts, speaker=chk.turn.speaker, quote=p.quote, point=p.point))
    return Finding(call_id=call.call_id, company=call.company, verdict=out.verdict, counts=out.counts,
                   evidence=kept)


def call_findings(question: str, call_ids: list[str], calls: dict[str, Call], llm: LLM,
                  usage: Usage | None = None, workers: int = 8) -> list[Finding]:
    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(lambda cid: judge_call(question, calls[cid], calls, llm, usage), call_ids))


def uncovered(findings: list[Finding], texts: list[str], cited: set[str]) -> list[Finding]:
    """Calls whose own verdict counts them toward the answer but that the answer neither cites nor names.
    With every verdict in its context, the answer once wrote "three of the four cold calls" and dropped
    the fifth (Kestrel, a follow-up on condition); a drop like that is caught here, not left to the
    reader."""
    blob = "\n".join(texts).lower()
    return [f for f in findings if f.counts != "no" and f.call_id not in cited
            and f.call_id.lower() not in blob and f.company.lower() not in blob]


def render_findings(findings: list[Finding]) -> str:
    lines = ["PER-CALL FINDINGS (each call was read on its own for this question; quotes verified)"]
    for f in findings:
        lines.append(f"{f.call_id} ({f.company}): {f.verdict}")
        for p in f.evidence:
            lines.append(f'   [{p.timestamp}] {p.speaker}: "{p.quote}"')
    return "\n".join(lines)
