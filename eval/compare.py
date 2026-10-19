"""Paired, per-question comparison of graded runs.

  uv run python eval/compare.py --auto A1.json A2.json A3.json --full F.json \
      [--agree "judge repeat" A1.json A1-again.json] [--agree "opus vs gpt-5.4" A1.json A1-gpt.json]

Shows, per question, the verdict of every auto run and of the full-context baseline, flags questions
where the auto runs disagree with each other (unstable) and where the baseline differs from the auto
majority, and checks whether those differences fall on the unstable questions. Each --agree compares two
gradings of the same answers (the same judge twice, or two judges) and reports how often they agree.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

SCORE = {"yes": 2, "partly": 1, "no": 0}


def load(p: Path) -> dict[str, dict]:
    return {r["id"]: r for r in json.loads(p.read_text()) if "error" not in r}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", type=Path, nargs="+", required=True)
    ap.add_argument("--full", type=Path, required=True)
    ap.add_argument("--agree", nargs=3, action="append", default=[], metavar=("LABEL", "FIRST", "SECOND"))
    args = ap.parse_args()

    autos = [load(p) for p in args.auto]
    full = load(args.full)
    ids = [q for q in full if all(q in a for a in autos)]

    out = [
        "| id | " + " | ".join(f"A{i + 1}" for i in range(len(autos))) + " | F | auto unstable | F vs auto majority |",
        "|---|" + "---|" * (len(autos) + 3),
    ]
    unstable, differs = set(), set()
    for q in ids:
        av = [a[q]["correct"] for a in autos]
        maj, n = Counter(av).most_common(1)[0]
        if len(set(av)) > 1:
            unstable.add(q)
        f = full[q]["correct"]
        rel = ""
        if n > len(av) / 2 and f != maj:
            differs.add(q)
            rel = "better" if SCORE[f] > SCORE[maj] else "worse"
        elif n <= len(av) / 2:
            rel = "no majority"
        bonus = " (bonus)" if full[q].get("bonus_question") else ""
        out.append(f"| {q}{bonus} | " + " | ".join(av) + f" | {f} | {'yes' if q in unstable else ''} | {rel} |")

    head = [q for q in ids if not full[q].get("bonus_question")]
    mean_auto = sum(SCORE[a[q]["correct"]] for a in autos for q in head) / len(autos)
    mean_full = sum(SCORE[full[q]["correct"]] for q in head)
    out += [
        "",
        f"- questions: {len(ids)}; auto runs disagree with each other on {len(unstable)}: {', '.join(sorted(unstable)) or '-'}",
        f"- baseline differs from a clear auto majority on {len(differs)}: {', '.join(sorted(differs)) or '-'}"
        f" (of which unstable across auto runs: {len(differs & unstable)})",
        f"- correctness points (yes=2, partly=1, no=0) over the {len(head)} headline questions:"
        f" auto mean {mean_auto:.1f}, full {mean_full}",
    ]
    for label, first, second in args.agree:
        a, b = load(Path(first)), load(Path(second))
        same = [q for q in a if q in b and a[q]["correct"] == b[q]["correct"]]
        changed = [f"{q} {a[q]['correct']}→{b[q]['correct']}" for q in a if q in b and a[q]["correct"] != b[q]["correct"]]
        out.append(f"- {label}, identical answers: same verdict on {len(same)}/{len(a)}; changed: {', '.join(changed) or '-'}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
