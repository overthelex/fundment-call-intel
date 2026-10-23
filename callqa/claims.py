"""Vendor claims: what OrbitFlow staff assert about the product, extracted once per call.

Questions like "has the vendor given inconsistent answers?" are about relationships between calls.
Retrieval by similarity to the question cannot find them: each side of a contradiction is one turn in
a different call, and neither sounds like "an inconsistent answer". So at index time every call gets
one extraction pass that lists the vendor's factual statements under a fixed set of topics. A
consistency question then sees all statements on each topic side by side, and a contradiction is two
statements under the same topic that cannot both be true.

Every extracted quote is checked against the transcript like any citation; ones that fail are dropped.
Results are cached per call content, model and prompt version.
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from .index import turn_line
from .llm import LLM, Usage
from .parse import Call, Turn
from .verify import check_citation

PROMPT_VERSION = "claims-v2"

Topic = Literal[
    "plans and what each tier includes",
    "pricing and discounts",
    "SSO, SCIM and identity",
    "security, compliance and certifications",
    "data residency and hosting",
    "integrations and connectors",
    "no-code vs code, technical skills needed",
    "billing, usage limits and run volumes",
    "AI features",
    "support, services and onboarding",
    "roadmap and future features",
    "other product facts",
]

CLAIMS_SYSTEM = """You read one sales-call transcript. The vendor is OrbitFlow (workflow automation).
List the factual statements OrbitFlow staff make about OrbitFlow's product and commercial terms:
what features exist, which plan includes what, prices, limits, security and compliance, integrations,
how much code is needed, support and services, roadmap. Be exhaustive: the list is later used to
check whether reps contradict each other across calls, so a missed statement is a missed contradiction.
- Short replies count: "That's fine, it's completely no-code", "Yeah, it's on all plans", "No, that's
  Enterprise" are claims (read the customer's question before them to state what they assert).
- Include hedged statements ("I'm fairly sure it's all plans") and later corrections as separate items.
- The topic is the subject of the statement (a hedge about SSO is an SSO claim, not roadmap).

Skip questions, small talk, opinions about the customer's business, and anything said by the customer.

For each statement:
- topic: the closest topic from the list
- statement: what the rep asserted, one short sentence, faithful to their wording and certainty
- timestamp and speaker exactly as shown in the transcript line
- quote: a VERBATIM contiguous span from that single turn (max ~25 words) that carries the statement"""


class VendorClaim(BaseModel):
    topic: Topic
    statement: str
    timestamp: str
    speaker: str
    quote: str


class CallClaims(BaseModel):
    claims: list[VendorClaim]


class StoredClaim(BaseModel):
    call_id: str
    turn_idx: int
    topic: str
    statement: str
    speaker: str
    quote: str


def _digest(call: Call, llm: LLM) -> str:
    raw = "\x00".join(t.text for t in call.turns) + llm.chat_model + PROMPT_VERSION
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def extract(call: Call, calls: dict[str, Call], llm: LLM, usage: Usage | None = None) -> list[StoredClaim]:
    text = "\n".join(turn_line(call, t) for t in call.turns)
    out = llm.structured(CLAIMS_SYSTEM, f"{call.call_id} · {call.company}\n\n{text}", CallClaims,
                         reasoning_effort="medium", usage=usage)
    in_call = {(call.call_id, t.idx) for t in call.turns}
    kept = []
    for c in out.claims:
        chk = check_citation(calls, call.call_id, c.timestamp, c.speaker, c.quote, in_call)
        # keep only quotes that verify and were said by vendor staff
        if chk.ok and chk.turn is not None and chk.turn.side == "vendor":
            kept.append(StoredClaim(call_id=call.call_id, turn_idx=chk.turn.idx, topic=c.topic,
                                    statement=c.statement, speaker=chk.turn.speaker, quote=c.quote))
    return kept


class ClaimStore:
    def __init__(self, calls: list[Call], llm: LLM, cache_dir: Path = Path(".cache")) -> None:
        self.calls = {c.call_id: c for c in calls}
        self.llm, self.cache_dir = llm, cache_dir
        self._claims: list[StoredClaim] | None = None

    def load(self, usage: Usage | None = None, workers: int = 8) -> list[StoredClaim]:
        """All vendor claims, extracting (in parallel) only calls missing from the cache."""
        if self._claims is not None:
            return self._claims
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        def one(call: Call) -> list[StoredClaim]:
            path = self.cache_dir / f"claims-{call.call_id}-{_digest(call, self.llm)}.json"
            if path.exists():
                return [StoredClaim.model_validate(x) for x in json.loads(path.read_text())]
            claims = extract(call, self.calls, self.llm, usage)
            path.write_text(json.dumps([c.model_dump() for c in claims], indent=1))
            return claims

        with ThreadPoolExecutor(workers) as pool:
            self._claims = [c for cs in pool.map(one, self.calls.values()) for c in cs]
        return self._claims

    def context(self, usage: Usage | None = None, topics: list[str] | None = None) -> tuple[str, list[Turn]]:
        """Every vendor claim grouped by topic (or only the given topics), each shown as the full turn it came from."""
        by_topic: dict[str, list[StoredClaim]] = {}
        for c in self.load(usage):
            by_topic.setdefault(c.topic, []).append(c)
        parts, turns, seen = [], [], set()
        for topic in Topic.__args__:
            if topics is not None and topic not in topics:
                continue
            items = sorted(by_topic.get(topic, []), key=lambda c: (c.call_id, c.turn_idx))
            if not items:
                continue
            lines, shown = [f"## TOPIC: {topic}"], set()
            for c in items:
                if (c.call_id, c.turn_idx) in shown:
                    continue
                shown.add((c.call_id, c.turn_idx))
                call = self.calls[c.call_id]
                t = call.turns[c.turn_idx]
                lines.append(f"{c.call_id} ({call.company}, {call.category}) {turn_line(call, t)}")
                if (c.call_id, t.idx) not in seen:
                    seen.add((c.call_id, t.idx))
                    turns.append(t)
            parts.append("\n".join(lines))
        return "\n\n".join(parts), turns
