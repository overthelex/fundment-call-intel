"""Question -> plan -> context -> grounded answer -> citation check."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Literal

import numpy as np
from pydantic import BaseModel, Field

from .claims import ClaimStore, Topic
from .conflicts import find_conflicts, render as render_conflicts
from .index import Chunk, Index, turn_line
from .llm import LLM, QUESTION_HEDGE_AFTER, Usage
from .mapper import call_findings, map_calls, render_findings, render_tally, tally, uncovered
from .notes import NoteField
from .store import Store
from .names import ambiguous_names
from .parse import Call, Turn, load_calls
from .prompts import ANSWER_SYSTEM, PLANNER_SYSTEM
from .verify import CitationCheck, check_citation

# A product-fact question is "specific" and touches one or two topics. A planner that marks more topics,
# or an "across" question ("which customers asked about SSO?", "what do prospects ask for?"), is
# describing customers, where every vendor statement would only crowd the excerpts.
MAX_PRODUCT_TOPICS = 3

# How questions across calls get their context: "notes" selects the notes written at ingestion (cost
# independent of the number of calls); "map" reads every candidate call at question time (kept for
# comparison, capped at MAX_MAP_CALLS); "retrieval" uses excerpts only.
Across = Literal["notes", "map", "retrieval"]
MAX_MAP_CALLS = 25
# Reasoning effort of the answer step; it is most of the answer's output tokens, hence of its latency.
ANSWER_EFFORT = os.environ.get("ANSWER_EFFORT", "low")
# At most this many noted turns go to the answer step, best first by similarity of their notes to the question.
NOTE_BUDGET = 250

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
    vendor_consistency: bool = Field(
        description="True only when the question asks whether OrbitFlow's own statements agree with each other"
    )
    product_topics: list[Topic] = Field(
        description="Topics of a question about what is true of OrbitFlow's product or terms; empty otherwise"
    )
    note_fields: list[NoteField] = Field(
        description="For a question across calls, the note fields that hold the answer; empty = all"
    )
    assess_each_call: bool = Field(
        description="True when the answer needs a verdict on each candidate call: ranking or classifying "
                    "calls, saying which calls did something, or comparing groups of calls"
    )
    pooled_across_calls: bool = Field(
        default=False,
        description="True when the answer is what many calls share: the most common or most important "
                    "needs, themes, objections or reasons across the calls",
    )


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
    better_supported: str = Field(
        description='Which side the evidence favours, one short phrase, or "cannot tell"'
    )
    why: str = Field(description="The reasons, from the weighing criteria; empty if cannot tell")


class RelevantTurn(BaseModel):
    # only a pointer: every token here is generated before the answer and adds to latency
    call_id: str
    timestamp: str


class Answer(BaseModel):
    # Generated first, before the answer: an inventory of every turn that bears on the question, so
    # the answer is written from a full list instead of from the first few points the model recalls.
    relevant_turns: list[RelevantTurn] = Field(
        description="Every turn in the context that bears on the question, in transcript order"
    )
    summary: str
    claims: list[Claim]
    conflicts: list[Conflict]
    not_found: list[str] = Field(description="Parts of the question the transcripts do not answer")
    confidence: Confidence
    confidence_reason: str


@dataclass
class Context:
    mode: Literal["full", "excerpts", "claims", "mapped", "notes"]
    call_ids: list[str]
    turns: list[Turn]
    text: str
    chunks: list[Chunk] = field(default_factory=list)
    claim_topics: list[str] = field(default_factory=list)  # vendor statements appended for these topics

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
    # per step: seconds and tokens, so a slow answer shows which step was slow (latency follows the
    # tokens the model generates, not the size of the context)
    steps: dict = field(default_factory=dict)

    @property
    def cited_calls(self) -> list[str]:
        seen: dict[str, None] = {}
        for checks in self.claim_checks + self.conflict_checks:
            for c in checks:
                if c.ok and c.turn:
                    seen[c.turn.call_id] = None
        return list(seen)


def assess(
    answer: Answer, claim_checks: list[list[CitationCheck]], conflict_checks: list[list[CitationCheck]]
) -> tuple[Confidence, list[str]]:
    """Confidence after verification: the model cannot keep high confidence on claims nothing supports."""
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
    return confidence, warnings


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


def answer_texts(answer: "Answer") -> list[str]:
    return ([answer.summary] + [c.statement for c in answer.claims] + [c.description for c in answer.conflicts])


def cited_call_ids(answer: "Answer") -> set[str]:
    return {x.call_id for c in list(answer.claims) + list(answer.conflicts) for x in c.citations}


class Pipeline:
    def __init__(self, data_dir: Path = Path("data"), llm: LLM | None = None, across: Across = "notes") -> None:
        self.llm = llm or LLM()
        self.calls_list = load_calls(data_dir)
        self.calls = {c.call_id: c for c in self.calls_list}
        self.index = Index(self.calls_list, self.llm)
        self.store = Store(self.calls_list, self.llm)
        self.claims = ClaimStore(self.calls_list, self.store)
        self.across = across

    # -- steps -------------------------------------------------------------

    def plan(self, question: str, usage: Usage | None = None) -> Plan:
        user = f"CALL CATALOGUE\n{catalogue(self.calls_list)}\n\nQUESTION\n{question}"
        plan = self.llm.structured(PLANNER_SYSTEM, user, Plan, reasoning_effort="low", usage=usage,
                                   hedge_after=QUESTION_HEDGE_AFTER)
        plan.call_ids = [c for c in (x.strip().upper() for x in plan.call_ids) if c in self.calls]
        plan.entity_notes += ambiguous_names(question, self.calls_list)
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
        by_call: dict[str, set[int]] = {}
        for chunk, _ in hits:
            by_call.setdefault(chunk.call_id, set()).update(t.idx for t in chunk.turns)
        text, turns = self.excerpt_text(by_call)
        return Context("excerpts", sorted(by_call), turns, text, [c for c, _ in hits])

    def excerpt_text(self, by_call: dict[str, set[int]]) -> tuple[str, list[Turn]]:
        parts, turns = [], []
        for cid in sorted(by_call):
            call, picked = self.calls[cid], sorted(by_call[cid])
            lines, prev = [], None
            for i in picked:
                if prev is not None and i != prev + 1:
                    lines.append("[...]")
                lines.append(turn_line(call, call.turns[i]))
                prev = i
            parts.append(call_header(call) + "\n" + "\n".join(lines))
            turns.extend(call.turns[i] for i in picked)
        return "\n\n".join(parts), turns

    def mapped_context(
        self, question: str, plan: Plan, call_ids: list[str], usage: Usage | None = None
    ) -> Context:
        """Retrieved excerpts plus, from every candidate call read in full by the map step, each
        relevant turn with its neighbours (so a reply keeps its question)."""
        retrieved = self.excerpt_context(question, plan, call_ids, usage)
        found = map_calls(question, call_ids, self.calls, self.llm, usage)
        by_call: dict[str, set[int]] = {}
        for t in retrieved.turns:
            by_call.setdefault(t.call_id, set()).add(t.idx)
        for cid, pts in found.items():
            n = len(self.calls[cid].turns)
            for t, _ in pts:
                by_call.setdefault(cid, set()).update(i for i in (t.idx - 1, t.idx, t.idx + 1) if 0 <= i < n)
        text, turns = self.excerpt_text(by_call)
        text = (f"CALLS READ IN FULL FOR THIS QUESTION ({len(found)}): " + ", ".join(found) + "\n\n" + text)
        if plan.pooled_across_calls:
            text = render_tally(tally(question, found, self.llm, usage), len(found)) + "\n\n" + text
        empty = [f"{cid} ({self.calls[cid].company})" for cid, ts in found.items() if not ts]
        if empty:
            text += "\n\nCALLS READ IN FULL WITH NOTHING ON THIS QUESTION: " + ", ".join(empty)
        return Context("mapped", sorted(by_call), turns, text, retrieved.chunks)

    def notes_context(
        self, question: str, plan: Plan, call_ids: list[str], usage: Usage | None = None
    ) -> Context:
        """Retrieved excerpts plus the turns behind the ingestion notes in the question's fields, best
        first by similarity, up to NOTE_BUDGET turns; a short reply also brings the turn before it."""
        self.store.ensure(usage)
        retrieved = self.excerpt_context(question, plan, call_ids, usage)
        notes, vecs = self.store.notes(call_ids, plan.note_fields or None)
        noted = {n.call_id for n in notes}  # before the budget cut: a call cut for space did have notes
        if len({(n.call_id, n.turn_idx) for n in notes}) > NOTE_BUDGET:
            # the budget counts turns, not notes: a turn with notes in three fields is shown once
            qv = np.asarray(self.llm.embed([question], usage=usage)[0], dtype=np.float32)
            keep, seen = [], set()
            for i in np.argsort(-(vecs @ (qv / np.linalg.norm(qv)))):
                key = (notes[i].call_id, notes[i].turn_idx)
                if key not in seen and len(seen) == NOTE_BUDGET:
                    break
                seen.add(key)
                keep.append(i)
            notes = [notes[i] for i in sorted(keep)]
        by_call: dict[str, set[int]] = {}
        for t in retrieved.turns:
            by_call.setdefault(t.call_id, set()).add(t.idx)
        for n in notes:
            turn = self.calls[n.call_id].turns[n.turn_idx]
            by_call.setdefault(n.call_id, set()).add(n.turn_idx)
            if n.turn_idx > 0 and len(turn.text.split()) < 20:
                by_call[n.call_id].add(n.turn_idx - 1)
        whole = self.whole_groups(plan, call_ids)
        for cid in whole:
            by_call[cid] = set(range(len(self.calls[cid].turns)))
        text, turns = self.excerpt_text(by_call)
        empty = [f"{cid} ({self.calls[cid].company})" for cid in call_ids if cid not in noted and cid not in whole]
        if empty:
            fields = "; ".join(plan.note_fields) if plan.note_fields else "any field"
            text += f"\n\nCALLS WITH NO NOTES ON {fields.upper()}: " + ", ".join(empty)
        if whole:
            text = ("WHOLE TRANSCRIPTS (shown in full, not as notes): " + ", ".join(whole) + "\n\n" + text)
        return Context("notes", sorted(by_call), turns, text, retrieved.chunks)

    def whole_groups(self, plan: Plan, call_ids: list[str]) -> list[str]:
        """For a question comparing kinds of call ("renewals versus new business"), the kinds small
        enough to send whole, smallest first, within the word budget; the rest stay as notes. A small
        group read in full keeps what notes miss: who opens and runs the call, the standard terms."""
        if len(plan.categories) < 2:
            return []
        groups: dict[str, list[str]] = {}
        for cid in call_ids:
            groups.setdefault(self.calls[cid].category, []).append(cid)
        words = {g: sum(len(t.text.split()) for cid in ids for t in self.calls[cid].turns) for g, ids in groups.items()}
        whole, used = [], 0
        for g in sorted(groups, key=words.get)[:-1]:  # the largest kind always stays as notes
            if used + words[g] > FULL_TEXT_WORD_BUDGET:
                break
            whole += groups[g]
            used += words[g]
        return sorted(whole)

    def claims_context(self, usage: Usage | None = None) -> Context:
        """Every vendor claim grouped by topic, plus the contradictions found by checking each topic on
        its own (in parallel), so the answer does not depend on one pass comparing ~600 statements."""
        text, turns = self.claims.context(usage)
        found = find_conflicts(self.claims.topics(usage), self.calls, self.llm, usage)
        return Context("claims", sorted({t.call_id for t in turns}), turns,
                       render_conflicts(found) + "\n\n" + text)

    def with_vendor_statements(self, context: Context, topics: list[str], usage: Usage | None = None) -> Context:
        """Add every vendor statement on the question's product topics, from all calls. Retrieval returns
        the passages most similar to the question, so a product fact stated in six calls and contradicted
        in one may reach the model as one statement against one; the claims table has all of them."""
        text, turns = self.claims.context(usage, topics)
        if not turns:
            return context
        have = {(t.call_id, t.idx) for t in context.turns}
        new = [t for t in turns if (t.call_id, t.idx) not in have]
        block = ("VENDOR STATEMENTS ON THIS TOPIC (every product statement by OrbitFlow staff on these topics, "
                 "across all calls)\n" + text)
        return Context(context.mode, sorted(set(context.call_ids) | {t.call_id for t in turns}),
                       context.turns + new, context.text + "\n\n" + block, context.chunks, topics)

    def answer(self, question: str, context: Context, plan: Plan | None, usage: Usage | None = None,
               extra: str = "") -> Answer:
        notes = ""
        if plan and plan.entity_notes:
            notes = "NOTES FROM QUERY PLANNING\n" + "\n".join(f"- {n}" for n in plan.entity_notes) + "\n\n"
        shown = {"full": "whole transcripts", "excerpts": "retrieved excerpts only",
                 "claims": "every product statement by OrbitFlow staff, grouped by topic",
                 "mapped": "every candidate call was read in full for this question; shown are the relevant "
                           "turns with neighbours, plus retrieved excerpts",
                 "notes": "every call was read in full when it was ingested and its points noted by field; shown "
                          "are the turns behind the notes in the fields this question needs, plus retrieved "
                          "excerpts"}[context.mode]
        scope = f"CONTEXT MODE: {context.mode} ({len(context.call_ids)} of {len(self.calls)} calls shown, {shown})"
        if context.claim_topics:
            scope += "\nPlus every OrbitFlow statement on: " + "; ".join(context.claim_topics)
        user = f"{scope}\n\nTRANSCRIPTS\n{context.text}\n\n{notes}{extra}QUESTION\n{question}"
        # at medium reasoning an answer takes 60 s or more, so a duplicate would be sent for every one
        hedge = QUESTION_HEDGE_AFTER if ANSWER_EFFORT == "low" else None
        return self.llm.structured(ANSWER_SYSTEM, user, Answer, reasoning_effort=ANSWER_EFFORT, usage=usage,
                                   hedge_after=hedge)

    def check(self, citations: list[Citation], context: Context) -> list[CitationCheck]:
        in_ctx = {(t.call_id, t.idx) for t in context.turns} | {(cid, -1) for cid in context.call_ids}
        return [check_citation(self.calls, c.call_id, c.timestamp, c.speaker, c.quote, in_ctx) for c in citations]

    # -- entry point -------------------------------------------------------

    def ask(self, question: str, mode: Literal["auto", "full"] = "auto",
            on_step: Callable[[str], None] | None = None) -> Result:
        """mode="auto": plan, then whole calls or retrieved excerpts depending on size, or the vendor-claims
        table for questions about whether the vendor contradicts itself.
        mode="full": skip planning and put the entire dataset in context (baseline)."""
        t0 = time.time()
        usage = Usage()
        steps: dict[str, dict] = {}
        mark = {"t": t0, "u": usage.snapshot()}

        def done(step: str) -> None:
            now, u = time.time(), usage.snapshot()
            steps[step] = {"seconds": round(now - mark["t"], 2),
                           "prompt_tokens": u["prompt_tokens"] - mark["u"]["prompt_tokens"],
                           "completion_tokens": u["completion_tokens"] - mark["u"]["completion_tokens"],
                           "cached_tokens": u["cached_tokens"] - mark["u"]["cached_tokens"]}
            mark.update(t=now, u=u)

        say = on_step or (lambda _: None)
        plan: Plan | None = None
        findings: list = []
        if mode == "full":
            context = self.full_context(list(self.calls))
        else:
            say("planning")
            plan = self.plan(question, usage)
            done("plan")
            scope = "named calls" if plan.call_ids else (", ".join(plan.categories) or "all calls")
            say(f"plan: {plan.scope} question over {scope}"
                + (f"; note fields: {', '.join(plan.note_fields)}" if plan.scope == "across" and plan.note_fields else ""))
            ids = self.candidates(plan)
            size = sum(len(t.text.split()) for cid in ids for t in self.calls[cid].turns)
            if plan.vendor_consistency and not plan.call_ids:
                context = self.claims_context(usage)
            elif size <= FULL_TEXT_WORD_BUDGET:
                context = self.full_context(ids)
            elif plan.scope == "across" and self.across == "notes":
                context = self.notes_context(question, plan, ids, usage)
            elif plan.scope == "across" and self.across == "map" and len(ids) <= MAX_MAP_CALLS:
                # Each call read for the question; for "what matters most" (pooled_across_calls) the
                # points are also counted across calls. Not the default: on q05 it reached every
                # evidence turn (1.0 vs 0.33-0.50) and core recall 0.50-0.83 (vs 0.33-0.67), at ~45 s
                # and ~150K tokens against 15-18 s and ~25K.
                say(f"reading each of {len(ids)} calls for the question")
                context = self.mapped_context(question, plan, ids, usage)
            else:
                context = self.excerpt_context(question, plan, ids, usage)
            # A verdict per call, read on its own, when the answer has to be built call by call: one pass
            # over several calls drops a call or its caveat (q10 "all five cold calls", q07 left out Acme).
            # Always for a few whole calls; beyond the word budget only when the planner says the question
            # assesses each call, and for at most MAX_MAP_CALLS candidates.
            if (plan.scope == "across" and len(ids) > 1 and context.mode in ("full", "notes", "excerpts")
                    and (context.mode == "full" or (plan.assess_each_call and len(ids) <= MAX_MAP_CALLS))):
                say(f"reading each of {len(ids)} calls on its own")
                findings = call_findings(question, ids, self.calls, self.llm, usage)
                context.text = render_findings(findings) + "\n\n" + context.text
            if (plan.product_topics and len(plan.product_topics) <= MAX_PRODUCT_TOPICS
                    and plan.scope == "specific" and context.mode != "claims" and not plan.call_ids):
                context = self.with_vendor_statements(context, plan.product_topics, usage)
        done("context")
        say(f"context: {context.mode}, {len(context.call_ids)} calls, {context.words:,} words; writing the answer")

        answer = self.answer(question, context, plan, usage)
        missing = uncovered(findings, answer_texts(answer), cited_call_ids(answer))
        if missing:  # one more pass, told which calls it left out
            say("answer left out " + ", ".join(f.call_id for f in missing) + "; answering again")
            note = ("COVERAGE CHECK: a previous answer left out these calls, which their per-call findings "
                    "count toward the answer; cover each of them:\n"
                    + "\n".join(f"- {f.call_id} ({f.company}): {f.verdict}" for f in missing) + "\n\n")
            answer = self.answer(question, context, plan, usage, extra=note)
            missing = uncovered(findings, answer_texts(answer), cited_call_ids(answer))
        done("answer")
        claim_checks = [self.check(c.citations, context) for c in answer.claims]
        conflict_checks = [self.check(c.citations, context) for c in answer.conflicts]
        confidence, warnings = assess(answer, claim_checks, conflict_checks)
        if missing:
            warnings.append("the answer does not cover " + ", ".join(f"{f.call_id} ({f.company})" for f in missing)
                            + ", which the per-call findings count toward it")
        done("check")

        return Result(
            question, plan, context, answer, claim_checks, conflict_checks,
            confidence, warnings, usage.snapshot(), time.time() - t0, steps,
        )
