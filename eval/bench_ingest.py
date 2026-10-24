"""Ingestion benchmark: one call read whole or in parts, at medium or low reasoning per extraction.

    uv run python eval/bench_ingest.py                    # longest call, 3 variants, 2 repeats
    uv run python eval/bench_ingest.py --call CALL-001 --repeats 3

For each variant: wall time for the call (every request in parallel, as at ingestion), the slowest
request, output tokens, and how many vendor claims and notes survive the citation check. Ingestion
waits for its slowest call, so the slowest request is the number that sets ingestion time.
"""

from __future__ import annotations

import argparse
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from callqa import claims as claims_mod  # noqa: E402
from callqa import llm as llm_mod  # noqa: E402
from callqa import notes as notes_mod  # noqa: E402
from callqa.index import call_parts  # noqa: E402
from callqa.llm import LLM, Usage  # noqa: E402
from callqa.parse import load_calls  # noqa: E402
from callqa.store import merge_claims, merge_notes  # noqa: E402

VARIANTS = [("whole", "medium", "medium"), ("parts", "low", "low"), ("parts", "low", "medium")]  # read, claims, notes


def read(call, calls, llm, split: bool, claims_effort: str, notes_effort: str) -> dict:
    claims_mod.EFFORT, notes_mod.EFFORT = claims_effort, notes_effort
    parts = call_parts(call) if split else [call]
    usage = Usage()
    jobs = [(claims_mod.extract, p) for p in parts * 2] + [(notes_mod.extract, p) for p in parts]

    def timed(job):
        fn, part = job
        t = time.time()
        return fn(part, calls, llm, usage), time.time() - t

    t = time.time()
    with ThreadPoolExecutor(len(jobs)) as pool:
        res = list(pool.map(timed, jobs))
    wall = time.time() - t
    cl = merge_claims(*[r for (r, _), (fn, _) in zip(res, jobs) if fn is claims_mod.extract])
    ns = merge_notes(*[r for (r, _), (fn, _) in zip(res, jobs) if fn is notes_mod.extract])
    return {"wall": wall, "slowest": max(s for _, s in res), "out": usage.completion_tokens,
            "claims": len(cl), "notes": len(ns), "requests": len(jobs)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--call", help="call id (default: the longest call)")
    ap.add_argument("--repeats", type=int, default=2)
    args = ap.parse_args()

    calls = {c.call_id: c for c in load_calls(ROOT / "data")}
    words = lambda c: sum(len(t.text.split()) for t in c.turns)  # noqa: E731
    call = calls[args.call] if args.call else max(calls.values(), key=words)
    llm = LLM()
    print(f"{call.call_id} ({call.company}): {words(call)} words, {len(call_parts(call))} parts; "
          f"{llm.chat_model}; timeout {llm_mod.INGEST_TIMEOUT} s; {args.repeats} repeats", flush=True)

    rows = {v: [] for v in VARIANTS}
    for rep in range(args.repeats):
        for split, ce, ne in VARIANTS:  # interleaved, so a slow minute at the provider hits every variant
            r = read(call, calls, llm, split == "parts", ce, ne)
            rows[(split, ce, ne)].append(r)
            print(f"  rep {rep + 1} {split:5s} claims {ce:6s} notes {ne:6s} wall {r['wall']:5.1f} s  slowest {r['slowest']:5.1f} s  "
                  f"out {r['out']:6,}  claims {r['claims']:3d}  notes {r['notes']:3d}", flush=True)

    print("\n| read | effort: claims / notes | requests | wall per call, s | slowest request, s | output tokens | claims | notes |")
    print("|---|---|---|---|---|---|---|---|")
    for (split, ce, ne), rs in rows.items():
        span = lambda k: "–".join(str(x) for x in sorted({min(round(r[k]) for r in rs), max(round(r[k]) for r in rs)}))  # noqa: E731
        mean = lambda k: statistics.mean(r[k] for r in rs)  # noqa: E731
        print(f"| {split} | {ce} / {ne} | {rs[0]['requests']} | {span('wall')} | {span('slowest')} | "
              f"{mean('out'):,.0f} | {span('claims')} | {span('notes')} |")


if __name__ == "__main__":
    main()
