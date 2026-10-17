"""Question -> plan -> context -> grounded answer -> citation check."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .index import Chunk, Index, turn_line
from .llm import LLM, Usage
from .parse import Call, Turn, load_calls
from .prompts import ANSWER_SYSTEM, PLANNER_SYSTEM
from .verify import CitationCheck, check_citation

# If the candidate calls fit in this many words, send them whole instead of
# retrieving excerpts. The whole dataset is ~51K words, a single call at most ~5K.
FULL_TEXT_WORD_BUDGET = 12_000

Category = Literal["prospect", "renewal", "churn", "cold_call"]
Confidence = Literal["high", "medium", "low", "insufficient"]


class Plan(BaseModel):
    call_ids: list[str] = Field(description="Calls named by the question; empty = not restricted")
    categories: list[Category] = Field(description="Kinds of call the question is limited to; empty = all")
    scope: Literal["specific", "across"]
    search_queries: list[str]
    entity_notes: list[str] = Field(description="Name mismatches or unknown entities in the question")


class Citation(BaseModel):
    call_id: str
    timestamp: str
    speaker: str
    quote: str


class Claim(BaseModel):
    statement: str
    citations: list[Citation]


class Conflict(BaseModel):
    description: str
    citations: list[Citation]


class Answer(BaseModel):
    summary: str
    claims: list[Claim]
    conflicts: list[Conflict]
    not_found: list[str] = Field(description="Parts of the question the transcripts do not answer")
    confidence: Confidence
    confidence_reason: str


@dataclass
class Context:
    mode: Literal["full", "excerpts"]
    call_ids: list[str]
    turns: list[Turn]
    text: str
    chunks: list[Chunk] = field(default_factory=list)

    @property
    def words(self) -> int:
        return len(self.text.split())


@dataclass
class Result:
    question: str
    plan: Plan | None
    context: Context
    answer: Answer
    claim_checks: list[list[CitationCheck]]
    conflict_checks: list[list[CitationCheck]]
    confidence: Confidence  # after verification
    warnings: list[str]
    usage: dict
    seconds: float

    @property
    def cited_calls(self) -> list[str]:
        seen: dict[str, None] = {}
        for checks in self.claim_checks + self.conflict_checks:
            for c in checks:
                if c.ok and c.turn:
                    seen[c.turn.call_id] = None
        return list(seen)


def call_header(call: Call) -> str:
    # the header exactly as in the file, so a quoted header line can be checked like a turn
    raw = "\n".join(t.text for t in call.header if t.text != "TRANSCRIPT")
    return f"=== {call.call_id} (call kind: {call.category})\n{raw}\nTRANSCRIPT"


def catalogue(calls: list[Call]) -> str:
    return "\n".join(
        f"{c.call_id} | {c.company} | {c.industry} | {c.category} | {c.stage} | "
        + ", ".join(f"{p.name} ({p.company})" for p in c.participants)
        for c in calls
    )


class Pipeline:
    def __init__(self, data_dir: Path = Path("data"), llm: LLM | None = None) -> None:
        self.llm = llm or LLM()
        self.calls_list = load_calls(data_dir)
        self.calls = {c.call_id: c for c in self.calls_list}
        self.index = Index(self.calls_list, self.llm)

    # -- steps -------------------------------------------------------------

    def plan(self, question: str, usage: Usage | None = None) -> Plan:
        user = f"CALL CATALOGUE\n{catalogue(self.calls_list)}\n\nQUESTION\n{question}"
        plan = self.llm.structured(PLANNER_SYSTEM, user, Plan, reasoning_effort="low", usage=usage)
        plan.call_ids = [c for c in (x.strip().upper() for x in plan.call_ids) if c in self.calls]
        return plan

    def candidates(self, plan: Plan) -> list[str]:
        if plan.call_ids:
            return plan.call_ids
        if plan.categories:
            return [c.call_id for c in self.calls_list if c.category in plan.categories]
        return list(self.calls)

    def full_context(self, call_ids: list[str]) -> Context:
        parts, turns = [], []
        for cid in call_ids:
            call = self.calls[cid]
            parts.append(call_header(call) + "\n" + "\n".join(turn_line(call, t) for t in call.turns))
            turns.extend(call.turns)
        return Context("full", call_ids, turns, "\n\n".join(parts))

    def excerpt_context(
        self, question: str, plan: Plan, call_ids: list[str], usage: Usage | None = None
    ) -> Context:
        queries = [question, *plan.search_queries][:5]
        # A quota per call unless the question named its calls: facts about the product or the
        # vendor can sit in any call, often in a single turn that global top-k misses.
        per_call = 0 if plan.call_ids else (2 if plan.scope == "across" else 1)
        hits = self.index.search(queries, call_ids=call_ids, per_call=per_call, usage=usage)
        by_call: dict[str, dict[int, Turn]] = {}
        for chunk, _ in hits:
            by_call.setdefault(chunk.call_id, {}).update({t.idx: t for t in chunk.turns})
        parts, turns = [], []
        for cid in sorted(by_call):
            call, picked = self.calls[cid], by_call[cid]
            lines, prev = [], None
            for i in sorted(picked):
                if prev is not None and i != prev + 1:
                    lines.append("[...]")
                lines.append(turn_line(call, picked[i]))
                prev = i
            parts.append(call_header(call) + "\n" + "\n".join(lines))
            turns.extend(picked[i] for i in sorted(picked))
        return Context("excerpts", sorted(by_call), turns, "\n\n".join(parts), [c for c, _ in hits])

    def answer(self, question: str, context: Context, plan: Plan | None, usage: Usage | None = None) -> Answer:
        notes = ""
        if plan and plan.entity_notes:
            notes = "NOTES FROM QUERY PLANNING\n" + "\n".join(f"- {n}" for n in plan.entity_notes) + "\n\n"
        scope = (
            f"CONTEXT MODE: {context.mode} ({len(context.call_ids)} of {len(self.calls)} calls shown"
            + (", whole transcripts" if context.mode == "full" else ", retrieved excerpts only")
            + ")"
        )
        user = f"{scope}\n\n{notes}TRANSCRIPTS\n{context.text}\n\nQUESTION\n{question}"
        return self.llm.structured(ANSWER_SYSTEM, user, Answer, reasoning_effort="medium", usage=usage)

    def check(self, citations: list[Citation], context: Context) -> list[CitationCheck]:
        in_ctx = {(t.call_id, t.idx) for t in context.turns} | {(cid, -1) for cid in context.call_ids}
        return [check_citation(self.calls, c.call_id, c.timestamp, c.speaker, c.quote, in_ctx) for c in citations]

    # -- entry point -------------------------------------------------------

    def ask(self, question: str, mode: Literal["auto", "full"] = "auto") -> Result:
        """mode="auto": plan, then whole calls or retrieved excerpts depending on size.
        mode="full": skip planning and put the entire dataset in context (baseline)."""
        t0 = time.time()
        usage = Usage()
        plan: Plan | None = None
        if mode == "full":
            context = self.full_context(list(self.calls))
        else:
            plan = self.plan(question, usage)
            ids = self.candidates(plan)
            size = sum(len(t.text.split()) for cid in ids for t in self.calls[cid].turns)
            if size <= FULL_TEXT_WORD_BUDGET:
                context = self.full_context(ids)
            else:
                context = self.excerpt_context(question, plan, ids, usage)

        answer = self.answer(question, context, plan, usage)
        claim_checks = [self.check(c.citations, context) for c in answer.claims]
        conflict_checks = [self.check(c.citations, context) for c in answer.conflicts]

        warnings, confidence = [], answer.confidence
        unsupported = [i for i, checks in enumerate(claim_checks) if not any(c.ok for c in checks)]
        if unsupported:
            warnings.append(f"{len(unsupported)} of {len(claim_checks)} claims have no verifiable quote")
        if claim_checks and len(unsupported) == len(claim_checks) and confidence in ("high", "medium"):
            confidence = "low"
            warnings.append("confidence lowered: no claim could be verified against the transcripts")
        bad = sum(1 for checks in claim_checks + conflict_checks for c in checks if not c.ok)
        if bad:
            warnings.append(f"{bad} citation(s) failed verification (quote not found or wrong speaker)")

        return Result(
            question, plan, context, answer, claim_checks, conflict_checks,
            confidence, warnings, usage.snapshot(), time.time() - t0,
        )
