"""How stable is the judge? Compare regrades of the same saved answers.

Each results file must come from `run_eval.py --regrade <same file>` (same answers, judged again).
Reports, for the `correct` verdict:
  single vote    share of pairs of individual votes on one answer that disagree (from `judge_votes`,
                 within and across files): what one verdict per answer is exposed to
  combined       answers whose combined verdict differs between the files
  headline       yes / partly / no per file

Usage:
  uv run python eval/judge_stability.py eval/results/<regrade-1>.json eval/results/<regrade-2>.json
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path


def main(paths: list[str]) -> None:
    runs = [{r["id"]: r for r in json.loads(Path(p).read_text()) if "error" not in r} for p in paths]
    ids = sorted(set.intersection(*(set(r) for r in runs)))
    ids = [i for i in ids if not runs[0][i].get("bonus_question")]

    pairs = flips = 0
    for i in ids:
        votes = [v for run in runs for v in run[i].get("judge_votes") or [run[i]["correct"]]]
        for a, b in itertools.combinations(votes, 2):
            pairs += 1
            flips += a != b

    print(f"{len(ids)} questions (bonus excluded), {len(runs)} regrades\n")
    for p, run in zip(paths, runs):
        c = [run[i]["correct"] for i in ids]
        print(f"{Path(p).stem}: yes/partly/no {c.count('yes')}/{c.count('partly')}/{c.count('no')}")
    print(f"\nsingle vote: {flips}/{pairs} pairs of votes on the same answer disagree ({flips / max(1, pairs):.0%})")
    for (pa, a), (pb, b) in itertools.combinations(zip(paths, runs), 2):
        moved = [f"{i} {a[i]['correct']}->{b[i]['correct']}" for i in ids if a[i]["correct"] != b[i]["correct"]]
        print(f"combined: {len(moved)}/{len(ids)} verdicts differ between {Path(pa).stem} and {Path(pb).stem}"
              + (": " + ", ".join(moved) if moved else ""))
    split = [f"{i} ({'/'.join(runs[0][i]['judge_votes'])})" for i in ids
             if len(set(runs[0][i].get("judge_votes") or [])) > 1]
    print(f"\nsplit votes in {Path(paths[0]).stem}: {', '.join(split) or 'none'}")


if __name__ == "__main__":
    main(sys.argv[1:])
