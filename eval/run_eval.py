"""Evaluate the pipeline against eval/questions.yaml.

What is measured, per question:
  context_recall  share of the gold calls that reached the model's context    (retrieval, deterministic)
  cited_recall    share of the gold calls the answer actually cites            (use of evidence, deterministic)
  citation_valid  share of citations whose quote is found in the transcript    (grounding, deterministic)
  correct         does the answer get the main point right                     (correctness, LLM judge)
  fact_recall     gold facts stated: supported 1, partial 0.5                  (completeness, LLM judge)
  abstention      did it decline exactly when the data has no answer           (uncertainty, LLM judge)
plus tokens and latency.

Usage:
  uv run python eval/run_eval.py                    # auto mode
  uv run python eval/run_eval.py --mode full        # whole dataset in context (baseline)
  uv run python eval/run_eval.py --only q03,q07     # subset
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from callqa.cli import to_dict  # noqa: E402
from callqa.pipeline import Pipeline, Result  # noqa: E402

JUDGE_SYSTEM = """You grade an answer produced by a question-answering system over sales-call transcripts.
You get the question, the system's answer, and a list of expected facts written by a human annotator.
For each expected fact give a verdict:
  supported     the answer states it or something equivalent (paraphrase and extra detail are fine)
  partial       the answer states the core of it but misses some of its parts (facts often bundle details)
  missing       the answer does not state it, or only hints at it vaguely
  contradicted  the answer says something incompatible with it
If an expected fact describes an absence ("the transcripts do not mention X"), it is supported when the
answer says the information was not found. Judge only what the answer text says.

Then give one overall verdict, `correct`: does the answer get the question right, judged against the
expected facts? Missing background detail is fine; what matters is whether the main point is right and
nothing important is wrong or invented. yes = right; partly = main point right but an important part
missing or hedged where the facts are clear; no = wrong, contradicts the facts, or wrongly declines.

Finally, `declines`: true if the answer's main message is that the transcripts do not contain the
requested information (it may still cite related material), false if it provides the information."""

SCORE = {"supported": 1.0, "partial": 0.5, "missing": 0.0, "contradicted": 0.0}


class FactVerdict(BaseModel):
    fact: str
    verdict: Literal["supported", "partial", "missing", "contradicted"]
    reason: str


class Judgement(BaseModel):
    verdicts: list[FactVerdict]
    correct: Literal["yes", "partly", "no"]
    correct_reason: str
    declines: bool


def answer_text(r: Result) -> str:
    a = r.answer
    lines = [f"SUMMARY: {a.summary}", f"CONFIDENCE: {r.confidence} ({a.confidence_reason})"]
    lines += [f"- {c.statement}" + "".join(f' [{x.call_id} {x.timestamp} "{x.quote}"]' for x in c.citations) for c in a.claims]
    lines += [f"CONFLICT: {c.description}" for c in a.conflicts]
    lines += [f"NOT FOUND: {x}" for x in a.not_found]
    return "\n".join(lines)


def evaluate(pipe: Pipeline, item: dict, mode: str) -> dict:
    t0 = time.time()
    try:
        r = pipe.ask(item["question"], mode=mode)
    except Exception as e:  # keep the run going; report the failure
        return {"id": item["id"], "kind": item["kind"], "error": repr(e), "seconds": time.time() - t0}

    gold = set(item.get("expected_calls") or [])
    ctx = set(r.context.call_ids)
    cited = set(r.cited_calls)
    checks = [c for cs in r.claim_checks + r.conflict_checks for c in cs]
    should_abstain = bool(item.get("should_abstain"))

    facts = item.get("expected_facts") or []
    verdicts: list[dict] = []
    correct: str | None
    declined: bool
    if facts:
        user = (
            f"QUESTION\n{item['question']}\n\nANSWER\n{answer_text(r)}\n\nEXPECTED FACTS\n"
            + "\n".join(f"{i + 1}. {f}" for i, f in enumerate(facts))
        )
        j = pipe.llm.structured(JUDGE_SYSTEM, user, Judgement, model=pipe.llm.judge_model, reasoning_effort="low")
        verdicts = [v.model_dump() for v in j.verdicts]
        correct, correct_reason, declined = j.correct, j.correct_reason, j.declines
    else:
        correct, correct_reason, declined = None, "", r.confidence == "insufficient"

    return {
        "id": item["id"],
        "kind": item["kind"],
        "question": item["question"],
        "context_recall": len(gold & ctx) / len(gold) if gold else None,
        "cited_recall": len(gold & cited) / len(gold) if gold else None,
        "missed_calls": sorted(gold - cited),
        "citation_valid": sum(c.ok for c in checks) / len(checks) if checks else None,
        "citations": len(checks),
        "fact_recall": sum(SCORE[v["verdict"]] for v in verdicts) / len(verdicts) if verdicts else None,
        "contradicted": sum(v["verdict"] == "contradicted" for v in verdicts),
        "correct": correct,
        "correct_reason": correct_reason,
        "verdicts": verdicts,
        "should_abstain": should_abstain,
        "abstained": declined,
        "abstention_correct": declined == should_abstain,
        "confidence": r.confidence,
        "prompt_tokens": r.usage["prompt_tokens"],
        "completion_tokens": r.usage["completion_tokens"],
        "seconds": round(r.seconds, 1),
        "result": to_dict(r),
    }


def mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def fmt(x: float | None) -> str:
    return "-" if x is None else f"{x:.2f}"


def summarise(rows: list[dict], mode: str) -> str:
    ok = [r for r in rows if "error" not in r]
    answerable = [r for r in ok if not r["should_abstain"]]
    unanswerable = [r for r in ok if r["should_abstain"]]
    out = [
        f"## Mode: {mode}  ({len(ok)}/{len(rows)} questions ran)",
        "",
        "| metric | value |",
        "|---|---|",
        f"| context recall (gold calls reached the model) | {fmt(mean([r['context_recall'] for r in answerable]))} |",
        f"| cited recall (gold calls cited in the answer) | {fmt(mean([r['cited_recall'] for r in answerable]))} |",
        f"| citation validity (quote found verbatim) | {fmt(mean([r['citation_valid'] for r in ok]))} |",
        f"| answer correct (LLM judge): yes / partly / no | "
        f"{'/'.join(str(sum(r['correct'] == v for r in ok)) for v in ('yes', 'partly', 'no'))} |",
        f"| fact recall, completeness (LLM judge) | {fmt(mean([r['fact_recall'] for r in answerable]))} |",
        f"| facts contradicted by the answer | {sum(r['contradicted'] for r in ok)} |",
        f"| correct abstention on unanswerable | {sum(r['abstained'] for r in unanswerable)}/{len(unanswerable)} |",
        f"| false abstention on answerable | {sum(r['abstained'] for r in answerable)}/{len(answerable)} |",
        f"| mean prompt tokens / question | {mean([r['prompt_tokens'] for r in ok]) or 0:,.0f} |",
        f"| mean latency (s) | {fmt(mean([r['seconds'] for r in ok]))} |",
        "",
        "| id | kind | correct | ctx recall | cited recall | cit. valid | fact recall | abstain ok | conf | missed calls |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if "error" in r:
            out.append(f"| {r['id']} | {r['kind']} | ERROR: {r['error'][:60]} |||||||")
            continue
        out.append(
            f"| {r['id']} | {r['kind']} | {r['correct'] or '-'} | {fmt(r['context_recall'])} | {fmt(r['cited_recall'])} | "
            f"{fmt(r['citation_valid'])} | {fmt(r['fact_recall'])} | {'✓' if r['abstention_correct'] else '✗'} | "
            f"{r['confidence']} | {', '.join(r['missed_calls'])} |"
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["auto", "full"], default="auto")
    ap.add_argument("--only", help="comma-separated question ids")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--questions", type=Path, default=ROOT / "eval" / "questions.yaml")
    args = ap.parse_args()

    items = yaml.safe_load(args.questions.read_text())
    if args.only:
        wanted = set(args.only.split(","))
        items = [i for i in items if i["id"] in wanted]

    pipe = Pipeline(ROOT / "data")
    with ThreadPoolExecutor(args.workers) as pool:
        rows = list(pool.map(lambda it: evaluate(pipe, it, args.mode), items))

    out_dir = ROOT / "eval" / "results"
    out_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    (out_dir / f"{stamp}-{args.mode}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    report = summarise(rows, args.mode)
    (out_dir / f"{stamp}-{args.mode}.md").write_text(report + "\n")
    print(report)
    print(f"\nTotal tokens: {pipe.llm.usage.snapshot()}")
    print(f"Saved eval/results/{stamp}-{args.mode}.json")


if __name__ == "__main__":
    main()
