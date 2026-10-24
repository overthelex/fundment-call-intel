"""Command line: `callqa ask "question"`, or `callqa` for an interactive prompt."""

from __future__ import annotations

import argparse
import json
import sys
import time
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
    if r.plan and r.plan.entity_notes:
        out.append("\nNotes on names")
        out.extend(f"  - {x}" for x in r.plan.entity_notes)
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
            if conflict.better_supported:
                why = f": {conflict.why}" if conflict.why else ""
                out.append(f"    → better supported: {conflict.better_supported}{why}")
    if a.not_found:
        out.append("\nNot found in the transcripts")
        out.extend(f"  - {x}" for x in a.not_found)
    if r.warnings:
        out.append("\nWarnings")
        out.extend(f"  ! {w}" for w in r.warnings)
    ctx = r.context
    u = r.usage
    out.append(
        f"\n[{ctx.mode}: {len(ctx.call_ids)} calls, {ctx.words:,} words in context · "
        f"{u['calls']} API calls · {u['prompt_tokens']:,} in / {u['completion_tokens']:,} out tokens · {r.seconds:.1f}s]"
    )
    if r.steps:
        out.append("[" + " · ".join(
            f"{k} {v['seconds']:.1f}s" + (f" ({v['completion_tokens']:,} out)" if v["completion_tokens"] else "")
            for k, v in r.steps.items()) + "]")
    return "\n".join(out)


def progress() -> callable:
    """Print each pipeline step to stderr as it starts, with the elapsed time."""
    t0 = time.time()
    return lambda msg: print(f"  [{time.time() - t0:5.1f}s] {msg}", file=sys.stderr, flush=True)


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
        # everything the answer step saw, so an answer can be traced and re-generated (eval --replay)
        "context": {
            "mode": r.context.mode, "call_ids": r.context.call_ids, "words": r.context.words,
            "claim_topics": r.context.claim_topics,
            "turns": [[t.call_id, t.idx] for t in r.context.turns],
            "text": r.context.text,
        },
        "answer": r.answer.model_dump(),
        "confidence": r.confidence,
        "claim_checks": [checks(c) for c in r.claim_checks],
        "conflict_checks": [checks(c) for c in r.conflict_checks],
        "cited_calls": r.cited_calls,
        "warnings": r.warnings,
        "usage": r.usage,
        "seconds": round(r.seconds, 2),
        "steps": r.steps,
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
    ask.add_argument("--across", choices=["notes", "map", "retrieval"], default="notes",
                     help="questions across calls: notes written at ingestion (default), or read each call "
                          "for the question and count points across calls (map; slower, more complete)")
    sub.add_parser("index", help="ingest the calls: embeddings, vendor claims and per-call notes (all cached)")
    args = ap.parse_args(argv)

    pipe = Pipeline(args.data, across=getattr(args, "across", "notes"))
    if args.cmd == "index":
        print(f"indexed {len(pipe.index.chunks)} chunks from {len(pipe.calls)} calls")
        n = pipe.store.ingest()
        c = pipe.store.counts()
        print(f"ingested {n} new or changed calls; store holds {c['calls']} calls, "
              f"{c['claims']} vendor claims, {c['notes']} notes")
        return
    if args.cmd == "ask":
        r = pipe.ask(args.question, mode=args.mode, on_step=None if args.json else progress())
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
        print(render(pipe, pipe.ask(q, on_step=progress())))


if __name__ == "__main__":
    sys.exit(main())
