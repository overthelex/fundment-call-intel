"""Agreement between a blind human grading and the LLM judges, on the calibration sample.

  uv run python eval/calibrate.py eval/review/calibration_2026-10-23.json \
      --judge "Claude Opus" eval/results/20261017-155023-auto-regraded.json \
      --judge "Claude Opus, repeat" eval/results/20261017-155023-auto-judge-repeat-opus.json \
      --judge "gpt-5.4" eval/results/20261017-155023-auto-judge-gpt54.json

The human file maps sample ids (a01..a10) to {"verdict": "yes|partly|no", "note": "..."};
eval/review/calibration_sample.json maps the sample ids to question ids.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORE = {"yes": 2, "partly": 1, "no": 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("human", type=Path)
    ap.add_argument("--judge", nargs=2, action="append", required=True, metavar=("LABEL", "RESULTS_JSON"))
    args = ap.parse_args()

    sample = json.loads((ROOT / "eval/review/calibration_sample.json").read_text())["sample"]
    human = {sample[k]: v for k, v in json.loads(args.human.read_text()).items() if v.get("verdict")}
    judges = [(label, {r["id"]: r for r in json.loads(Path(p).read_text())}) for label, p in args.judge]
    qs = [q for q in sample.values() if q in human]

    out = ["| question | human | " + " | ".join(l for l, _ in judges) + " |", "|---|---|" + "---|" * len(judges)]
    for q in qs:
        out.append(f"| {q} | {human[q]['verdict']} | " + " | ".join(j[q]["correct"] for _, j in judges) + " |")
    out.append("")
    for label, j in judges:
        same = sum(j[q]["correct"] == human[q]["verdict"] for q in qs)
        bias = sum(SCORE[j[q]["correct"]] - SCORE[human[q]["verdict"]] for q in qs)
        lean = "more lenient" if bias > 0 else "stricter" if bias < 0 else "no net lean"
        out.append(f"- {label}: agrees with the human on {same}/{len(qs)}; net {bias:+d} points ({lean})")
    out.append("")
    for q in qs:
        if any(j[q]["correct"] != human[q]["verdict"] for _, j in judges) and human[q].get("note"):
            out.append(f"- {q}, human note: {human[q]['note']}")
    print("\n".join(out))


if __name__ == "__main__":
    main()
