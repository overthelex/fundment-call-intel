"""Gold evidence resolves to transcript turns, and a failed answer is labelled with the step that failed."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))

run_eval = pytest.importorskip("run_eval")
from callqa.parse import load_calls  # noqa: E402

CALLS = {c.call_id: c for c in load_calls(ROOT / "data")}


def test_gold_evidence_resolves_timestamps_ranges_and_inherited_calls():
    item = {"evidence": ["CALL-001 [01:51] Rachel / [02:12] QBR; CALL-006 [14:36]-[14:50] Ben, Alastair"]}
    turns = run_eval.gold_turns(item, CALLS)
    stamps = sorted((c, CALLS[c].turns[i].ts) for c, i in turns)
    assert ("CALL-001", "01:51") in stamps and ("CALL-001", "02:12") in stamps
    assert ("CALL-006", "14:36") in stamps and ("CALL-006", "14:50") in stamps
    assert all(c in ("CALL-001", "CALL-006") for c, _ in stamps)


def row(**kw):
    base = {"should_abstain": False, "abstention_correct": True, "citation_status": {"exact": 3},
            "correct": "partly", "contradicted": 0, "evidence_recall": 1.0, "evidence_cited": 0.8,
            "missed_evidence": []}
    return base | kw


def test_failure_points_at_the_first_failed_step():
    assert run_eval.failure(row(correct="yes")) == ""
    assert run_eval.failure(row(evidence_recall=0.5, missed_evidence=["CALL-001 [01:51]"])).startswith("retrieval")
    assert run_eval.failure(row()) == "answer (evidence was in context)"
    assert run_eval.failure(row(contradicted=1)) == "answer: wrong statement"
    assert run_eval.failure(row(should_abstain=True, abstention_correct=False)) == "abstention: answered"
    assert "attribution" in run_eval.failure(row(correct="yes", citation_status={"exact": 2, "wrong_call": 1}))
