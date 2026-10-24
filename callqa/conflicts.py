"""Contradiction check one topic at a time, for questions about whether the vendor contradicts itself.

The answer step for such a question sees every vendor statement, ~600 of them under 12 topics, and has
to compare the statements within each topic. With low reasoning it reliably found the most visible
contradiction (SSO on all plans vs Enterprise) and only sometimes the second ("completely no-code" vs
"we don't claim every workflow is no-code"): 3 of 5 replays on the same context, against 5 of 5 with
medium reasoning at 5x the latency. Here each topic is checked by its own small call, in parallel, so
every topic is looked at by construction; the answer step then weighs the pairs found.

Every quote goes through the citation checker, against the turns of that topic; a pair loses a side
whose quotes all fail and is then dropped.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from pydantic import BaseModel

from .llm import CHECK_HEDGE_AFTER, LLM, Usage
from .parse import Call, Turn
from .verify import check_citation

CONFLICT_SYSTEM = """You see every statement OrbitFlow staff made on ONE topic across many sales calls,
each as the full turn with its call. Find where reps tell customers different things about the same
point, so that a customer who heard both would be misled by one of them. Typical cases: a feature on
all plans vs only on one tier; "completely no-code" or "just configuration" vs "we don't claim every
workflow is no-code" or "that needs code"; different prices, limits, terms or policies; something
included for free in one call and paid in another; a promise one rep makes and another rules out.
A blanket claim made to one customer contradicts a general statement made to another, even if the
first was said about that customer's use case. A hedge or later correction by the same rep goes on
its side. Mere differences in detail, emphasis or wording do not count. If there are none, return an
empty list.

Report each contradiction ONCE, with every statement of each position on its side (not one entry per
pair of calls):
- what: the two positions in one short sentence ("SSO on all plans vs SAML SSO on Enterprise only")
- side_a, side_b: the statements on each side; for each, call_id, timestamp and speaker exactly as shown,
  and a VERBATIM contiguous span from that single turn (max ~25 words) as quote"""


class Statement(BaseModel):
    call_id: str
    timestamp: str
    speaker: str
    quote: str


class TopicConflict(BaseModel):
    what: str
    side_a: list[Statement]
    side_b: list[Statement]


class TopicConflicts(BaseModel):
    conflicts: list[TopicConflict]


class FoundConflict(BaseModel):
    topic: str
    what: str
    side_a: list[Statement]
    side_b: list[Statement]


def check_topic(topic: str, text: str, turns: list[Turn], calls: dict[str, Call], llm: LLM,
                usage: Usage | None = None) -> list[FoundConflict]:
    out = llm.structured(CONFLICT_SYSTEM, text, TopicConflicts, reasoning_effort="low", usage=usage,
                         hedge_after=CHECK_HEDGE_AFTER)
    shown = {(t.call_id, t.idx) for t in turns}

    def verified(side: list[Statement]) -> list[Statement]:
        kept = []
        for s in side:
            chk = check_citation(calls, s.call_id, s.timestamp, s.speaker, s.quote, shown)
            if chk.ok and chk.turn is not None and (chk.turn.call_id, chk.turn.idx) in shown:
                kept.append(Statement(call_id=chk.turn.call_id, timestamp=chk.turn.ts, speaker=chk.turn.speaker,
                                      quote=s.quote))
        return kept

    found = []
    for c in out.conflicts:
        a, b = verified(c.side_a), verified(c.side_b)
        if a and b:
            found.append(FoundConflict(topic=topic, what=c.what, side_a=a, side_b=b))
    return found


# Each topic is checked this many times, in parallel, and the contradictions found are merged: one
# pass over the 29 statements on "no-code vs code" found the "completely no-code" contradiction in 7 of
# 10 runs, so q11 missed it in about one run in three; two passes miss it in about one in eleven.
PASSES = 2


def merge(found: list[FoundConflict]) -> list[FoundConflict]:
    """One entry per contradiction: a pair on the same topic that shares a statement with one already
    kept (from another pass, or split by the same pass, e.g. "SSO on all plans" against "SAML SSO on
    Enterprise" and against "SAML SSO and SCIM on Enterprise") adds its statements to that one."""
    key = lambda side: {(s.call_id, s.timestamp) for s in side}  # noqa: E731
    out: list[FoundConflict] = []
    for c in found:
        a, b = key(c.side_a), key(c.side_b)
        for k in out:
            ka, kb = key(k.side_a), key(k.side_b)
            if k.topic == c.topic and (a & ka or b & kb or a & kb or b & ka):
                same = bool(a & ka or b & kb)
                for side, extra in ((k.side_a, c.side_a if same else c.side_b), (k.side_b, c.side_b if same else c.side_a)):
                    side += [s for s in extra if (s.call_id, s.timestamp) not in key(side)]
                break
        else:
            out.append(c)
    return out


def find_conflicts(blocks: list[tuple[str, str, list[Turn]]], calls: dict[str, Call], llm: LLM,
                   usage: Usage | None = None, workers: int = 24, passes: int = PASSES) -> list[FoundConflict]:
    """blocks: (topic, statements text, turns) per topic, as from ClaimStore.topics()."""
    with ThreadPoolExecutor(workers) as pool:
        per_topic = list(pool.map(lambda b: check_topic(b[0], b[1], b[2], calls, llm, usage), blocks * passes))
    return merge([c for found in per_topic for c in found])


def render(found: list[FoundConflict]) -> str:
    if not found:
        return "CONTRADICTIONS FOUND TOPIC BY TOPIC: none (every topic was checked separately)"
    lines = ["CONTRADICTIONS FOUND TOPIC BY TOPIC (every topic was checked separately; quotes verified)"]
    for i, c in enumerate(found, 1):
        lines.append(f"{i}. [{c.topic}] {c.what}")
        for label, side in (("A", c.side_a), ("B", c.side_b)):
            for s in side:
                lines.append(f'   {label}: {s.call_id} [{s.timestamp}] {s.speaker}: "{s.quote}"')
    return "\n".join(lines)
