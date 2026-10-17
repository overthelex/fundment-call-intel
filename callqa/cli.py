"""Command line: `callqa ask "question"`, or `callqa` for an interactive prompt."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .pipeline import Pipeline, Result
from .verify import CitationCheck

MARK = {"exact": "✓", "shifted": "✓~", "fuzzy": "≈", "wrong_speaker": "✗", "wrong_call": "✗", "not_found": "✗", "unknown_call": "✗"}


def _cite_line(pipe: Pipeline, c: CitationCheck) -> str:
    mark = MARK[c.status]
    if c.turn:
        call = pipe.calls[c.turn.call_id]
        p = call.speaker(c.turn.speaker)
        who = f"{c.turn.speaker}" + (f" ({p.role}, {p.company})" if p else "")
        where = f"{call.path}:{c.turn.line}"
        note = "" if c.status == "exact" else f"  [{c.status}: cited {c.timestamp} {c.speaker}]"
        return f'    {mark} {c.turn.call_id} [{c.turn.ts}] {who}: "{c.quote}"\n       {where}{note}'
    return f'    {mark} {c.call_id} [{c.timestamp}] {c.speaker}: "{c.quote}"  (quote not found in transcript)'


def render(pipe: Pipeline, r: Result) -> str:
    a = r.answer
    out = [f"\nAnswer  (confidence: {r.confidence}{'' if r.confidence == a.confidence else f', model said {a.confidence}'})"]
    out.append(a.summary)
    out.append(f"  why this confidence: {a.confidence_reason}")
    if a.claims:
        out.append("\nEvidence")
        for i, (claim, checks) in enumerate(zip(a.claims, r.claim_checks), 1):
            out.append(f"  {i}. {claim.statement}")
            out.extend(_cite_line(pipe, c) for c in checks)
    if a.conflicts:
        out.append("\nConflicting statements")
        for conflict, checks in zip(a.conflicts, r.conflict_checks):
            out.append(f"  - {conflict.description}")
            out.extend(_cite_line(pipe, c) for c in checks)
    if a.not_found:
        out.append("\nNot found in the transcripts")
        out.extend(f"  - {x}" for x in a.not_found)
    if r.plan and r.plan.entity_notes:
        out.append("\nNotes")
        out.extend(f"  - {x}" for x in r.plan.entity_notes)
    if r.warnings:
        out.append("\nWarnings")
        out.extend(f"  ! {w}" for w in r.warnings)
    ctx = r.context
    u = r.usage
    out.append(
        f"\n[{ctx.mode}: {len(ctx.call_ids)} calls, {ctx.words:,} words in context · "
        f"{u['calls']} API calls · {u['prompt_tokens']:,} in / {u['completion_tokens']:,} out tokens · {r.seconds:.1f}s]"
    )
    return "\n".join(out)


def to_dict(r: Result) -> dict:
    def checks(cs: list[CitationCheck]) -> list[dict]:
        return [
            {
                "call_id": c.call_id,
                "timestamp": c.timestamp,
                "speaker": c.speaker,
                "quote": c.quote,
                "status": c.status,
                "in_context": c.in_context,
                "resolved": f"{c.turn.call_id} [{c.turn.ts}] line {c.turn.line}" if c.turn else None,
            }
            for c in cs
        ]

    return {
        "question": r.question,
        "plan": r.plan.model_dump() if r.plan else None,
        "context": {"mode": r.context.mode, "call_ids": r.context.call_ids, "words": r.context.words},
        "answer": r.answer.model_dump(),
        "confidence": r.confidence,
        "claim_checks": [checks(c) for c in r.claim_checks],
        "conflict_checks": [checks(c) for c in r.conflict_checks],
        "cited_calls": r.cited_calls,
        "warnings": r.warnings,
        "usage": r.usage,
        "seconds": round(r.seconds, 2),
    }


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="callqa", description=__doc__)
    ap.add_argument("--data", type=Path, default=Path("data"))
    sub = ap.add_subparsers(dest="cmd")
    ask = sub.add_parser("ask", help="answer one question")
    ask.add_argument("question")
    ask.add_argument("--mode", choices=["auto", "full"], default="auto",
                     help="auto = plan + whole calls or retrieved excerpts; full = entire dataset in context")
    ask.add_argument("--json", action="store_true", help="print the raw result as JSON")
    sub.add_parser("index", help="build the embedding cache")
    args = ap.parse_args(argv)

    pipe = Pipeline(args.data)
    if args.cmd == "index":
        print(f"indexed {len(pipe.index.chunks)} chunks from {len(pipe.calls)} calls")
        return
    if args.cmd == "ask":
        r = pipe.ask(args.question, mode=args.mode)
        print(json.dumps(to_dict(r), indent=2, ensure_ascii=False) if args.json else render(pipe, r))
        return

    print(f"{len(pipe.calls)} calls loaded. Ask a question (empty line to quit).")
    while True:
        try:
            q = input("\n? ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not q:
            break
        print(render(pipe, pipe.ask(q)))


if __name__ == "__main__":
    sys.exit(main())
