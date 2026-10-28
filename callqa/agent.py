"""Agentic mode: a LangGraph tool-calling agent gathers the evidence, then the same answer step,
citation check and confidence rules as auto mode write and verify the answer.

Auto mode decides once (plan -> one kind of context). The agent decides step by step: it searches,
reads what it found, and searches again, so a two-step question ("the customer who mentioned X: what
did they say about Y?") can follow its first finding. Only the routing changes; the answer is written
from the turns the agent read, rendered from the transcripts (not from the agent's own messages), so
the two modes are compared on how they gather evidence and nothing else.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Callable

import numpy as np
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError
from langgraph.prebuilt import create_react_agent

from .claims import Topic
from .index import turn_line
from .llm import Usage
from .notes import NoteField

if TYPE_CHECKING:
    from .pipeline import Pipeline

# Each tool round is two graph steps (model, tools); 25 steps is 12 rounds, then the agent is cut off
# and the answer is written from what it gathered so far.
RECURSION_LIMIT = 25
AGENT_EFFORT = os.environ.get("AGENT_EFFORT", "low")
# The answer step reads every gathered turn; past this many words the agent is told to stop reading.
GATHER_WORD_BUDGET = 30_000
NOTES_PER_CALL = 40  # find_notes: the best notes, at most this many

AGENT_SYSTEM = """You gather evidence from B2B sales-call transcripts to answer a question. The vendor on
every call is OrbitFlow (workflow automation). You do NOT write the final answer: another step writes it
from exactly the transcript turns your tools returned. Your job is that every turn the answer needs has
been returned by a tool, and little else.

Tools:
- search_transcripts: hybrid keyword + semantic search over turns; phrase queries the way people talk
  on calls (synonyms, product and competitor names). Optionally limit to some calls.
- find_notes: notes written when each call was read in full at ingestion, by field. Best for questions
  across many calls (themes, "which customers...", comparisons): they cover every call, search does not.
- read_call: a whole call, or a time range of it ("05:00" to "09:30"). Use it to read around a hit,
  for a question about one named call, or to check what a call says on the question.
- vendor_statements: every statement OrbitFlow staff made on one product topic, across all calls. Use it
  for questions about what is true of the product, plans, prices or terms, and whether reps contradict
  each other (call it for each topic the question touches).

How to work:
1. Work out which calls could hold the answer from the catalogue below (names may be misspelt or partial;
   match loosely and look at every candidate).
2. Gather, then look at what came back and decide what is still missing: a reply without its question,
   a figure that may be corrected later in the call, the second step of a two-step question, a call
   in the candidate set you have not looked at.
3. Stop when the evidence covers the question, or when more searching returns nothing new. Usually
   2-6 tool calls; do not read every call when notes or search already cover the question.
4. Finish with one short message: which calls and turns you found, and what you looked for and did not
   find. Do not answer the question.

CALL CATALOGUE (call id | company | industry | kind | stage | participants)
{catalogue}"""


class Gathered:
    """The turns the agent's tools returned, per call, plus counts for the step report."""

    def __init__(self, pipe: "Pipeline") -> None:
        self.pipe = pipe
        self.by_call: dict[str, set[int]] = {}
        self.topics: list[str] = []
        self.tool_calls: list[str] = []

    def add(self, call_id: str, idx: set[int] | list[int]) -> None:
        self.by_call.setdefault(call_id, set()).update(idx)

    @property
    def words(self) -> int:
        return sum(len(self.pipe.calls[c].turns[i].text.split()) for c, ix in self.by_call.items() for i in ix)

    def budget_note(self) -> str:
        w = self.words
        if w > GATHER_WORD_BUDGET:
            return f"\n\n[{w:,} words gathered, over the budget of {GATHER_WORD_BUDGET:,}: stop reading and finish.]"
        return ""


def make_tools(pipe: "Pipeline", got: Gathered, usage: Usage):
    calls = pipe.calls

    def known(ids: list[str]) -> list[str]:
        return [c for c in (x.strip().upper() for x in ids) if c in calls]

    @tool
    def search_transcripts(query: str, call_ids: list[str] | None = None) -> str:
        """Hybrid search over transcript turns. call_ids optionally limits the search to those calls."""
        got.tool_calls.append(f"search({query!r}{', ' + ','.join(call_ids) if call_ids else ''})")
        ids = known(call_ids or []) or list(calls)
        hits = pipe.index.search([query], call_ids=ids, per_call=0 if call_ids else 1, top_k=8,
                                 max_chunks=12, usage=usage)
        if not hits:
            return "no results"
        out = []
        for chunk, _ in hits:
            got.add(chunk.call_id, [t.idx for t in chunk.turns])
            call = calls[chunk.call_id]
            out.append(f"--- {chunk.call_id} ({call.company}, {call.category}) [{chunk.span}]\n"
                       + "\n".join(turn_line(call, t) for t in chunk.turns))
        return "\n".join(out) + got.budget_note()

    @tool
    def find_notes(query: str, fields: list[NoteField] | None = None, call_ids: list[str] | None = None) -> str:
        """Ingestion notes (one point per note, with the turn it came from), ranked by similarity to
        query. fields and call_ids optionally narrow them; empty means all."""
        got.tool_calls.append(f"notes({query!r}; {', '.join(fields or []) or 'all fields'})")
        pipe.store.ensure(usage)
        ids = known(call_ids or []) or list(calls)
        notes, vecs = pipe.store.notes(ids, list(fields) if fields else None)
        if not notes:
            return "no notes"
        qv = np.asarray(pipe.llm.embed([query], usage=usage)[0], dtype=np.float32)
        order = np.argsort(-(vecs @ (qv / np.linalg.norm(qv))))[:NOTES_PER_CALL]
        picked = sorted((notes[i] for i in order), key=lambda n: (n.call_id, n.turn_idx))
        lines, seen_calls = [], set()
        for n in picked:
            call = calls[n.call_id]
            got.add(n.call_id, [n.turn_idx])
            seen_calls.add(n.call_id)
            lines.append(f"{n.call_id} ({call.company}) [{call.turns[n.turn_idx].ts}] {n.speaker} · {n.field}: {n.point}")
        silent = [c for c in ids if c not in {n.call_id for n in notes}]
        tail = f"\nCalls with no notes in these fields: {', '.join(silent)}" if silent else ""
        return "\n".join(lines) + tail + got.budget_note()

    @tool
    def read_call(call_id: str, start: str = "", end: str = "") -> str:
        """Read a call: whole, or the turns from timestamp start to end (MM:SS, inclusive)."""
        got.tool_calls.append(f"read({call_id}{' ' + start + '-' + end if start or end else ''})")
        cid = call_id.strip().upper()
        if cid not in calls:
            return f"unknown call {call_id}; ids look like CALL-007"
        call = calls[cid]

        def sec(ts: str, default: int) -> int:
            try:
                m, s = ts.strip().strip("[]").split(":")
                return int(m) * 60 + int(s)
            except ValueError:
                return default

        lo, hi = sec(start, 0), sec(end, 10 ** 6)
        turns = [t for t in call.turns if lo <= t.seconds <= hi]
        got.add(cid, [t.idx for t in turns])
        from .pipeline import call_header
        return call_header(call) + "\n" + "\n".join(turn_line(call, t) for t in turns) + got.budget_note()

    @tool
    def vendor_statements(topic: Topic) -> str:
        """Every statement OrbitFlow staff made on this product topic, in all calls."""
        got.tool_calls.append(f"vendor({topic})")
        text, turns = pipe.claims.context(usage, [topic])
        for t in turns:
            got.add(t.call_id, [t.idx])
        if topic not in got.topics:
            got.topics.append(topic)
        return (text or "no statements on this topic") + got.budget_note()

    return [search_transcripts, find_notes, read_call, vendor_statements]


def chat_model() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ.get("CHAT_MODEL", "gpt-5.4-mini"),
        api_key=os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("LLM_BASE_URL") or None,
        reasoning_effort=AGENT_EFFORT,
        timeout=120,
        max_retries=8,
    )


def gather(pipe: "Pipeline", question: str, usage: Usage, say: Callable[[str], None]) -> Gathered:
    """Run the agent until it stops or hits the step limit; return what its tools returned."""
    from .pipeline import catalogue

    got = Gathered(pipe)
    agent = create_react_agent(chat_model(), make_tools(pipe, got, usage),
                               prompt=AGENT_SYSTEM.format(catalogue=catalogue(pipe.calls_list)))
    seen = 0
    try:
        for state in agent.stream({"messages": [HumanMessage(question)]},
                                  {"recursion_limit": RECURSION_LIMIT}, stream_mode="values"):
            msgs = state["messages"]
            for m in msgs[seen:]:
                if isinstance(m, AIMessage):
                    u = m.usage_metadata or {}
                    cached = (u.get("input_token_details") or {}).get("cache_read", 0) or 0
                    usage.add(u.get("input_tokens", 0), u.get("output_tokens", 0), cached=cached)
                    for tc in m.tool_calls:
                        say(f"agent → {tc['name']}({', '.join(f'{k}={v!r}' for k, v in tc['args'].items())})")
            seen = len(msgs)
    except GraphRecursionError:
        say(f"agent stopped at the step limit ({RECURSION_LIMIT}); answering from what it gathered")
    return got
