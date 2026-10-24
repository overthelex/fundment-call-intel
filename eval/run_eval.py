"""Evaluate the pipeline against eval/questions.yaml.

What is measured, per question:
  context_recall  share of the gold calls that reached the model's context    (routing, deterministic)
  evidence_recall share of the gold evidence turns that reached the context    (retrieval, deterministic)
  cited_recall    share of the gold calls the answer actually cites            (use of evidence, deterministic)
  evidence_cited  share of the gold evidence turns the answer cites            (use of evidence, deterministic)
  citation_valid  share of citations whose quote is found in the transcript    (grounding, deterministic)
  correct         does the answer get the main point right                     (correctness, LLM judge)
  core_recall     required core claims stated                                  (completeness, LLM judge)
  atomic_recall   cores plus details, k of n for enumerations                  (completeness, LLM judge)
  penalties       statements the gold set says a correct answer must not make  (LLM judge)
  abstention      did it decline exactly when the data has no answer           (uncertainty, LLM judge)
plus tokens and latency, and per question the first step that failed (`failure`). Questions marked
bonus_question are left out of the headline numbers.

Usage:
  uv run python eval/run_eval.py                    # auto mode
  uv run python eval/run_eval.py --mode full        # whole dataset in context (baseline)
  uv run python eval/run_eval.py --only q03,q07     # subset
  uv run python eval/run_eval.py --regrade eval/results/<file>.json   # re-check and re-judge saved answers
  uv run python eval/run_eval.py --replay eval/results/<file>.json    # new answers on the saved contexts
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import threading
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml
from typing import Literal

from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from callqa.cli import to_dict  # noqa: E402
from callqa.llm import Usage  # noqa: E402
from callqa.parse import Call  # noqa: E402
from callqa.pipeline import Answer, Context, Pipeline, Plan, Result, assess  # noqa: E402

JUDGE_SYSTEM = """You grade an answer produced by a question-answering system over sales-call transcripts.
You get the question, the system's answer, and the rubric written by a human annotator:

REQUIRED FACTS. Each has a core claim and sometimes lettered details.
  core: supported     the answer states the core claim or something equivalent (paraphrase is fine)
        missing       the answer does not state it, or only hints at it vaguely
        contradicted  the answer asserts something incompatible with it (declining to draw a
                      conclusion is missing, not contradicted)
  details_covered: the numbers of the details the answer states (empty list if none).
  If a fact describes an absence ("the transcripts do not mention X"), it is supported when the
  answer says the information was not found.
BONUS FACTS. hit = true if the answer states it. They are never required.
PENALTIES. Statements the answer must not make. hit = true if the answer makes that statement.

Then `correct`, the overall verdict:
  yes     the main point is right: for a question with one answer every required core is supported;
          for a broad question with several themes or items, the large majority of cores are
          supported and none is contradicted. Details and bonus facts never decide this.
  partly  the main point is right but a required core is missing, or the answer hedges where the
          required facts say the evidence clearly points one way, or a penalty is hit outside the
          main point
  no      wrong, contradicts the required facts, a penalty is hit on the main point, or the answer
          wrongly declines
Do not grade the order of ranked items unless a required fact asks for it.

Finally, `declines`: true only if the answer's main message is that the transcripts do not contain
the requested information (it may still cite related material). An answer that reports evidence on
both sides and says it cannot conclude is NOT a decline: declines = false, and grade `correct` by the
rule above (typically partly when the required facts say the evidence points one way). Judge only what the answer text says."""


class FactVerdict(BaseModel):
    n: int
    core: Literal["supported", "missing", "contradicted"]
    details_covered: list[int]
    reason: str


class ExtraVerdict(BaseModel):
    n: int
    hit: bool
    reason: str


class Judgement(BaseModel):
    facts: list[FactVerdict]
    bonus: list[ExtraVerdict]
    penalties: list[ExtraVerdict]
    correct: Literal["yes", "partly", "no"]
    correct_reason: str
    declines: bool


# The judge is Claude Opus, a different vendor from the answering model, run through a local,
# logged-in Claude Code (`claude -p`) with tools, MCP servers and settings disabled.
CLAUDE_JUDGE_MODEL = os.environ.get("CLAUDE_JUDGE_MODEL", "opus")


def check_judge() -> None:
    """Fail before generating any answers, not after."""
    if not shutil.which("claude"):
        raise SystemExit("The evaluation judge runs through Claude Code: install it and log in (`claude`), see README.\n"
                         "Or run with --no-judge for the deterministic metrics only.")


def judge_name() -> str:
    return f"claude-cli:{CLAUDE_JUDGE_MODEL}"


def judge(pipe: Pipeline, user: str) -> Judgement:
    """A different vendor from the answering model, so the judge does not share its blind spots."""
    cmd = [
        "claude", "-p", "--model", CLAUDE_JUDGE_MODEL, "--system-prompt", JUDGE_SYSTEM,
        "--tools", "", "--strict-mcp-config", "--setting-sources", "", "--no-session-persistence",
        "--output-format", "json", "--json-schema", json.dumps(Judgement.model_json_schema()),
    ]
    for attempt in range(3):
        out = subprocess.run(cmd, input=user, capture_output=True, text=True, timeout=600)
        try:
            data = json.loads(out.stdout)
            if not data.get("is_error") and data.get("structured_output"):
                return Judgement.model_validate(data["structured_output"])
        except (json.JSONDecodeError, ValueError):
            pass
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"claude judge failed: {out.stderr[:300] or out.stdout[:300]}")


def norm_fact(f: str | dict) -> dict:
    if isinstance(f, str):
        return {"core": f, "details": [], "min_details": 0}
    details = f.get("details") or []
    return {"core": f["core"], "details": details, "min_details": f.get("min_details") or len(details)}


def rubric(item: dict) -> str:
    out = ["REQUIRED FACTS"]
    for i, f in enumerate(map(norm_fact, item.get("expected_facts") or []), 1):
        out.append(f"{i}. {f['core']}")
        if f["details"]:
            k = f"any {f['min_details']} of {len(f['details'])} is full coverage" if f["min_details"] < len(f["details"]) else "all"
            out.append(f"   details ({k}): " + "; ".join(f"({j}) {d}" for j, d in enumerate(f["details"], 1)))
    for title, key in (("BONUS FACTS", "bonus_facts"), ("PENALTIES", "penalties")):
        xs = item.get(key) or []
        out.append(f"\n{title}" + ("" if xs else "\n(none)"))
        out += [f"{i}. {x}" for i, x in enumerate(xs, 1)]
    return "\n".join(out)


def fact_scores(item: dict, j: Judgement) -> dict:
    """Three views of completeness from the same verdicts:
    core      share of required core claims stated (the headline: did it get the points)
    atomic    cores plus details as separate atoms, enumerations capped at min_details (k of n)
    compound  the old scoring: 1 if core and every detail, 0.5 if core only, else 0"""
    facts = [norm_fact(f) for f in item.get("expected_facts") or []]
    by_n = {v.n: v for v in j.facts}
    core = atoms = hits = compound = 0.0
    for i, f in enumerate(facts, 1):
        v = by_n.get(i)
        ok = bool(v and v.core == "supported")
        covered = len({d for d in (v.details_covered if v else []) if 1 <= d <= len(f["details"])})
        core += ok
        atoms += 1 + f["min_details"]
        hits += ok + min(covered, f["min_details"])
        compound += (1.0 if covered == len(f["details"]) else 0.5) if ok else 0.0
    n = len(facts)
    return {
        "core_recall": core / n if n else None,
        "atomic_recall": hits / atoms if atoms else None,
        "compound_recall": compound / n if n else None,
    }


def answer_text(answer: Answer, confidence: str, notes: list[str] | None = None) -> str:
    """What the user sees, including the notes on names printed under the answer."""
    a = answer
    lines = [f"SUMMARY: {a.summary}", f"CONFIDENCE: {confidence} ({a.confidence_reason})"]
    lines += [f"NOTE ON NAMES: {n}" for n in notes or []]
    lines += [f"- {c.statement}" + "".join(f' [{x.call_id} {x.timestamp} "{x.quote}"]' for x in c.citations) for c in a.claims]
    lines += [f"CONFLICT: {c.description}"
              + (f" | BETTER SUPPORTED: {c.better_supported}" + (f" ({c.why})" if c.why else "") if c.better_supported else "")
              for c in a.conflicts]
    lines += [f"NOT FOUND: {x}" for x in a.not_found]
    return "\n".join(lines)


# Gold evidence is written as "CALL-001 [01:51] Rachel Morgan ... / [02:12] ..." with ranges like
# "[07:09]-[07:17]"; a timestamp belongs to the last call named before it on the line.
EVIDENCE_RE = re.compile(r"(CALL-\d{3})|\[(\d{1,3}:\d{2})\](?:-\[(\d{1,3}:\d{2})\])?")


def _seconds(ts: str) -> int:
    m, s = ts.split(":")
    return int(m) * 60 + int(s)


def gold_turns(item: dict, calls: dict[str, Call]) -> set[tuple[str, int]]:
    """The turns the gold evidence points to, as (call_id, turn index). A timestamp with no exact turn
    falls back to the turn running at that moment (at most 30 s earlier)."""
    out: set[tuple[str, int]] = set()
    for line in item.get("evidence") or []:
        cur = None
        for m in EVIDENCE_RE.finditer(line):
            if m.group(1):
                cur = m.group(1) if m.group(1) in calls else None
                continue
            if cur is None:
                continue
            a = _seconds(m.group(2))
            b = _seconds(m.group(3)) if m.group(3) else a
            hit = [t for t in calls[cur].turns if a <= t.seconds <= b]
            if not hit:
                hit = [t for t in calls[cur].turns if a - 30 <= t.seconds <= a][-1:]
            out |= {(cur, t.idx) for t in hit}
    return out


def failure(row: dict) -> str:
    """The first step that failed, in pipeline order, so a bad answer points at what to fix."""
    if row["should_abstain"]:
        return "abstention: answered" if row["abstention_correct"] is False else ""
    if row["abstention_correct"] is False:
        return "abstention: declined"
    bad = sum(n for s, n in row["citation_status"].items() if s not in ("exact", "shifted", "fuzzy"))
    attribution = f"attribution ({bad} failed citation{'s' * (bad > 1)})" if bad else ""
    if row["correct"] in (None, "yes"):
        return attribution
    # Gold evidence lists every supporting turn and a good answer cites a few, so evidence_cited is a
    # reading aid, not a test: the split here is only whether the model had the evidence at all.
    ev = row["evidence_recall"]
    if row["contradicted"]:
        step = "answer: wrong statement"
    elif ev is not None and ev < 1:
        n = len(row["missed_evidence"])
        step = f"retrieval ({n} evidence turn{'s' * (n > 1)} not in context)"
    else:
        step = "answer (evidence was in context)"
    return "; ".join(x for x in (step, attribution) if x)


def saved_context(pipe: Pipeline, ctx: dict) -> Context:
    turns = [pipe.calls[c].turns[i] for c, i in ctx.get("turns", [])]
    return Context(ctx["mode"], ctx["call_ids"], turns, ctx.get("text", ""), [], ctx.get("claim_topics", []))


def grade(pipe: Pipeline, item: dict, r: Result, use_judge: bool = True) -> dict:
    """Everything except generation, so saved answers can be re-graded against a revised gold set.
    Without the judge only the deterministic metrics are filled; the judged ones are None."""
    gold = set(item.get("expected_calls") or [])
    ctx = set(r.context.call_ids)
    cited = set(r.cited_calls)
    checks = [c for cs in r.claim_checks + r.conflict_checks for c in cs]
    should_abstain = bool(item.get("should_abstain"))
    evidence = gold_turns(item, pipe.calls)
    in_context = {(t.call_id, t.idx) for t in r.context.turns}  # empty for runs saved before turns were
    cited_turns = {(c.turn.call_id, c.turn.idx) for c in checks if c.ok and c.turn}

    user = f"QUESTION\n{item['question']}\n\nANSWER\n{answer_text(r.answer, r.confidence, r.plan.entity_notes if r.plan else None)}\n\n{rubric(item)}"
    j = judge(pipe, user) if use_judge else None
    # a verdict missing for a fact would count as "not stated"; ask again rather than score the gap
    for _ in range(2):
        if j is None or len({v.n for v in j.facts}) >= len(item.get("expected_facts") or []):
            break
        j = judge(pipe, user)
    row = {
        "id": item["id"],
        "kind": item["kind"],
        "bonus_question": bool(item.get("bonus_question")),
        "question": item["question"],
        "context_recall": len(gold & ctx) / len(gold) if gold else None,
        "cited_recall": len(gold & cited) / len(gold) if gold else None,
        "missed_calls": sorted(gold - cited),
        "evidence_recall": len(evidence & in_context) / len(evidence) if evidence and in_context else None,
        "evidence_cited": len(evidence & cited_turns) / len(evidence) if evidence else None,
        "missed_evidence": sorted(f"{c} [{pipe.calls[c].turns[i].ts}]" for c, i in evidence - in_context)
        if in_context else [],
        "citation_valid": sum(c.ok for c in checks) / len(checks) if checks else None,
        "citations": len(checks),
        "citation_status": dict(Counter(c.status for c in checks)),
        "should_abstain": should_abstain,
        "confidence": r.confidence,
    }
    if j is None:
        row |= {"core_recall": None, "atomic_recall": None, "compound_recall": None,
                "contradicted": 0, "penalties_hit": [], "bonus_hit": 0,
                "bonus_total": len(item.get("bonus_facts") or []), "correct": None,
                "correct_reason": None, "verdicts": [], "abstained": None, "abstention_correct": None}
        return row | {"failure": failure(row)}
    row |= {
        **fact_scores(item, j),
        "contradicted": sum(v.core == "contradicted" for v in j.facts),
        "penalties_hit": [p.model_dump() for p in j.penalties if p.hit],
        "bonus_hit": sum(b.hit for b in j.bonus),
        "bonus_total": len(item.get("bonus_facts") or []),
        "correct": j.correct,
        "correct_reason": j.correct_reason,
        "verdicts": [v.model_dump() for v in j.facts],
        "abstained": j.declines,
        "abstention_correct": j.declines == should_abstain,
    }
    return row | {"failure": failure(row)}


def evaluate(pipe: Pipeline, item: dict, mode: str, use_judge: bool = True, judges: ThreadPoolExecutor | None = None):
    """Answer one question, then grade it; with `judges`, the grading (a slow `claude -p`) is handed to
    that pool and a future is returned, so the answering threads move on to the next question and the
    latency they measure stays that of `workers` questions in parallel."""
    t0 = time.time()
    try:
        r = pipe.ask(item["question"], mode=mode)
    except Exception as e:  # keep the run going; report the failure
        return {"id": item["id"], "kind": item["kind"], "error": repr(e), "seconds": time.time() - t0}
    if judges is not None:
        return judges.submit(finish, pipe, item, r, use_judge)
    return finish(pipe, item, r, use_judge)


def finish(pipe: Pipeline, item: dict, r: Result, use_judge: bool) -> dict:
    return {
        **grade(pipe, item, r, use_judge),
        "prompt_tokens": r.usage["prompt_tokens"],
        "completion_tokens": r.usage["completion_tokens"],
        "seconds": round(r.seconds, 1),
        "result": to_dict(r),
    }


def regrade(pipe: Pipeline, item: dict, saved: dict, use_judge: bool = True) -> dict:
    """Re-check the saved answer's citations with the current verifier and re-judge it; no generation."""
    if "error" in saved:
        return saved
    res = saved["result"]
    res["answer"]["relevant_turns"] = [{"call_id": t["call_id"], "timestamp": t["timestamp"]}
                                       for t in res["answer"].get("relevant_turns", [])]  # older runs: none, or with a point
    for c in res["answer"]["conflicts"]:  # runs saved before conflicts were weighed
        c.setdefault("better_supported", "")
        c.setdefault("why", "")
    answer = Answer.model_validate(res["answer"])
    context = saved_context(pipe, res["context"])
    claim_checks = [pipe.check(c.citations, context) for c in answer.claims]
    conflict_checks = [pipe.check(c.citations, context) for c in answer.conflicts]
    confidence, warnings = assess(answer, claim_checks, conflict_checks)
    plan = saved_plan(res)
    r = Result(res["question"], plan, context, answer, claim_checks, conflict_checks,
               confidence, warnings, res["usage"], res["seconds"])
    result = {**to_dict(r), "context": res["context"]}
    return {
        **grade(pipe, item, r, use_judge),
        "prompt_tokens": saved["prompt_tokens"],
        "completion_tokens": saved["completion_tokens"],
        "seconds": saved["seconds"],
        "result": result,
    }


def saved_plan(res: dict) -> Plan | None:
    if not res.get("plan"):
        return None
    return Plan.model_validate({"product_topics": [], "note_fields": [], "vendor_consistency": False, "assess_each_call": False,
                               **res["plan"]})


def replay(pipe: Pipeline, item: dict, saved: dict, use_judge: bool = True) -> dict:
    """A new answer on the exact context of a saved run: isolates the answer step from routing and
    retrieval, e.g. to test a prompt change on the questions that failed."""
    if "error" in saved:
        return saved
    res = saved["result"]
    if not res["context"].get("turns"):
        raise SystemExit(f"{item['id']}: this run predates saved contexts; --replay needs a run made since 23.10")
    context = saved_context(pipe, res["context"])
    plan = saved_plan(res)
    usage, t0 = Usage(), time.time()
    answer = pipe.answer(item["question"], context, plan, usage)
    claim_checks = [pipe.check(c.citations, context) for c in answer.claims]
    conflict_checks = [pipe.check(c.citations, context) for c in answer.conflicts]
    confidence, warnings = assess(answer, claim_checks, conflict_checks)
    r = Result(item["question"], plan, context, answer, claim_checks, conflict_checks,
               confidence, warnings, usage.snapshot(), time.time() - t0)
    return {
        **grade(pipe, item, r, use_judge),
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


def pct(xs: list[float], p: int) -> str:
    return f"{xs[min(len(xs) - 1, round(p / 100 * (len(xs) - 1)))]:.1f}" if xs else "-"


def summarise(rows: list[dict], mode: str, judge_label: str = "", workers: int = 4) -> str:
    ran = [r for r in rows if "error" not in r]
    ok = [r for r in ran if not r.get("bonus_question")]  # headline numbers exclude bonus questions
    answerable = [r for r in ok if not r["should_abstain"]]
    unanswerable = [r for r in ok if r["should_abstain"]]
    status = Counter(s for r in ok for s, n in r["citation_status"].items() for _ in range(n))
    failed = {k: v for k, v in status.items() if k not in ("exact", "shifted", "fuzzy")}
    judged = any(r["correct"] is not None for r in ok)
    lat = sorted(r["seconds"] for r in ok)
    answer_out = [r["result"].get("steps", {}).get("answer", {}).get("completion_tokens") for r in ok]
    for r in ran:  # recomputed, so a saved run is re-labelled when the rules change
        r["failure"] = failure(r) if "evidence_recall" in r else ""
    steps = Counter(r["failure"].split(" (")[0].split(";")[0] for r in ok if r.get("failure"))
    failures = ", ".join(f"{k} {v}" for k, v in steps.most_common())

    def j(value: str) -> str:
        return value if judged else "not judged"

    bonus = f"{sum(r['bonus_hit'] for r in ok)}/{sum(r['bonus_total'] for r in ok)}"
    abst_ok = f"{sum(bool(r['abstained']) for r in unanswerable)}/{len(unanswerable)}"
    abst_false = f"{sum(bool(r['abstained']) for r in answerable)}/{len(answerable)}"

    out = [
        f"## Mode: {mode}  ({len(ran)}/{len(rows)} questions ran; headline over {len(ok)}, bonus questions listed separately)",
        "",
        f"Judge: `{judge_label}`" if judged else "Judge: none (`--no-judge`), deterministic metrics only",
        "",
        "| metric | value |",
        "|---|---|",
        f"| context recall (gold calls reached the model) | {fmt(mean([r['context_recall'] for r in answerable]))} |",
        f"| evidence recall (gold evidence turns reached the model) | {fmt(mean([r.get('evidence_recall') for r in answerable]))} |",
        f"| cited recall (gold calls cited in the answer) | {fmt(mean([r['cited_recall'] for r in answerable]))} |",
        f"| evidence cited (gold evidence turns cited) | {fmt(mean([r.get('evidence_cited') for r in answerable]))} |",
        f"| citation validity (quote found verbatim) | {fmt(mean([r['citation_valid'] for r in ok]))} |",
        f"| failed citations by kind | {', '.join(f'{k} {v}' for k, v in sorted(failed.items())) or 'none'} |",
        f"| answer correct (LLM judge): yes / partly / no | "
        f"{j('/'.join(str(sum(r['correct'] == v for r in ok)) for v in ('yes', 'partly', 'no')))} |",
        f"| core fact recall (LLM judge) | {j(fmt(mean([r['core_recall'] for r in answerable])))} |",
        f"| atomic fact recall: cores + details, k of n for lists | {j(fmt(mean([r['atomic_recall'] for r in answerable])))} |",
        f"| compound fact recall: old scoring, 1 / 0.5 / 0 | {j(fmt(mean([r['compound_recall'] for r in answerable])))} |",
        f"| core facts contradicted | {j(str(sum(r['contradicted'] for r in ok)))} |",
        f"| penalties hit | {j(str(sum(len(r['penalties_hit']) for r in ok)))} |",
        f"| bonus facts stated | {j(bonus)} |",
        f"| correct abstention on unanswerable | {j(abst_ok)} |",
        f"| false abstention on answerable | {j(abst_false)} |",
        f"| mean prompt tokens / question | {mean([r['prompt_tokens'] for r in ok]) or 0:,.0f} |",
        f"| mean latency (s) | {fmt(mean([r['seconds'] for r in ok]))} |",
        f"| latency p50 / p95 (s), {workers} questions in parallel | {pct(lat, 50)} / {pct(lat, 95)} |",
        f"| answer step: mean output tokens (what latency follows) | "
        f"{'-' if mean(answer_out) is None else f'{mean(answer_out):,.0f}'} |",
        f"| first failed step | {failures or 'none'} |",
        "",
        "| id | kind | correct | ctx recall | ev. recall | cited recall | ev. cited | cit. valid | core | atomic | penalties | abstain ok | conf | failure |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        if "error" in r:
            out.append(f"| {r['id']} | {r['kind']} | ERROR: {r['error'][:60]} ||||||||||||")
            continue
        out.append(
            f"| {r['id']}{' (bonus)' if r.get('bonus_question') else ''} | {r['kind']} | {r['correct'] or '-'} | "
            f"{fmt(r['context_recall'])} | {fmt(r.get('evidence_recall'))} | {fmt(r['cited_recall'])} | "
            f"{fmt(r.get('evidence_cited'))} | {fmt(r['citation_valid'])} | "
            f"{fmt(r['core_recall'])} | {fmt(r['atomic_recall'])} | {len(r['penalties_hit']) or ''} | "
            f"{'-' if r['abstention_correct'] is None else '✓' if r['abstention_correct'] else '✗'} | {r['confidence']} | {r.get('failure', '')} |"
        )
    return "\n".join(out)


def run_all(fn, items: list[dict], workers: int) -> list[dict]:
    """Run fn over the questions in parallel, printing one progress line per finished question."""
    done = 0

    def one(it: dict) -> dict:
        nonlocal done
        r = fn(it)
        if hasattr(r, "result"):  # grading handed to the judge pool
            r = r.result()
        done += 1
        status = f"ERROR {r['error'][:60]}" if "error" in r else f"correct={r['correct'] or '-'}"
        print(f"[{done}/{len(items)}] {it['id']} {status}", file=sys.stderr, flush=True)
        return r

    with ThreadPoolExecutor(workers) as pool:
        return list(pool.map(one, items))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["auto", "full"], default="auto")
    ap.add_argument("--only", help="comma-separated question ids")
    ap.add_argument("--workers", type=int, default=4, help="questions answered in parallel (latency is measured under this load)")
    ap.add_argument("--judge-workers", type=int, default=8, help="judge calls (claude -p) in parallel")
    ap.add_argument("--questions", type=Path, default=ROOT / "eval" / "questions.yaml")
    ap.add_argument("--regrade", type=Path, metavar="RESULTS_JSON",
                    help="re-check citations and re-judge the answers saved in a results file, without generating")
    ap.add_argument("--across", choices=["notes", "map", "retrieval"], default="notes",
                    help="context for questions across calls: ingestion notes (default), map step, or retrieval only")
    ap.add_argument("--replay", type=Path, metavar="RESULTS_JSON",
                    help="generate new answers on the contexts saved in a results file (answer step only)")
    ap.add_argument("--suffix", default=None, help="output name suffix for --regrade / --replay")
    ap.add_argument("--no-judge", action="store_true",
                    help="skip the LLM judge: deterministic metrics only (context/cited recall, citations, tokens); no Claude Code needed")
    args = ap.parse_args()

    use_judge = not args.no_judge
    if use_judge:
        check_judge()
    items = yaml.safe_load(args.questions.read_text())
    if args.only:
        wanted = set(args.only.split(","))
        items = [i for i in items if i["id"] in wanted]

    pipe = Pipeline(ROOT / "data", across=args.across)
    if args.regrade or args.replay:
        src = args.regrade or args.replay
        fn, suffix = (regrade, "regraded") if args.regrade else (replay, "replay")
        saved = {r["id"]: r for r in json.loads(src.read_text())}
        mode = "full" if "-full" in src.stem else "auto"
        items = [i for i in items if i["id"] in saved]
        rows = run_all(lambda it: fn(pipe, it, saved[it["id"]], use_judge), items,
                       args.judge_workers if fn is regrade else args.workers)
        label = f"{src.stem}-{args.suffix or suffix}"
    else:
        mode = args.mode
        with ThreadPoolExecutor(args.judge_workers) as judges:
            # the answer pool hands each answer to the judges and takes the next question; waiting on the
            # verdicts happens in run_all's own threads, so more of them than answer workers
            answering = threading.BoundedSemaphore(args.workers)

            def answer_then_judge(it: dict):
                with answering:
                    out = evaluate(pipe, it, mode, use_judge, judges)
                return out

            rows = run_all(answer_then_judge, items, args.workers + args.judge_workers)
        label = f"{time.strftime('%Y%m%d-%H%M%S')}-{mode}" + ("" if args.across == "notes" else f"-{args.across}")
    if not use_judge:
        label += "-nojudge"

    out_dir = ROOT / "eval" / "results"
    out_dir.mkdir(exist_ok=True)
    base, n = label, 2
    while (out_dir / f"{label}.json").exists():  # two runs started in the same second
        label, n = f"{base}-{n}", n + 1
    (out_dir / f"{label}.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False))
    report = summarise(rows, mode, judge_name(), args.workers)
    (out_dir / f"{label}.md").write_text(report + "\n")
    print(report)
    print(f"\nTotal tokens: {pipe.llm.usage.snapshot()}")
    print(f"Saved eval/results/{label}.json")


if __name__ == "__main__":
    main()
