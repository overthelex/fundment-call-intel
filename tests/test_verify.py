from pathlib import Path

import pytest

from callqa.parse import load_calls
from callqa.verify import check_citation

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def calls():
    return {c.call_id: c for c in load_calls(DATA)}


@pytest.fixture(scope="module")
def turn(calls):
    return calls["CALL-001"].turns[10]


def check(calls, turn, quote, ts=None, speaker=None, call_id="CALL-001"):
    ctx = {(turn.call_id, turn.idx)}
    return check_citation(calls, call_id, ts or turn.ts, speaker or turn.speaker, quote, ctx)


def test_exact_quote(calls, turn):
    words = turn.text.split()
    r = check(calls, turn, " ".join(words[1:8]))
    assert r.status == "exact" and r.in_context and r.turn == turn


def test_punctuation_and_case_do_not_matter(calls, turn):
    r = check(calls, turn, turn.text.upper().replace(",", "").replace(".", "!"))
    assert r.status == "exact"


def test_wrong_timestamp_is_recovered(calls, turn):
    neighbour = calls["CALL-001"].turns[turn.idx + 1]
    r = check(calls, turn, " ".join(turn.text.split()[:8]), ts=neighbour.ts)
    assert r.status == "shifted" and r.turn == turn


def test_invented_quote_is_rejected(calls, turn):
    r = check(calls, turn, "we have decided to sign the contract for five hundred seats today")
    assert r.status == "not_found" and not r.ok


def test_unknown_call(calls, turn):
    assert check(calls, turn, "anything", call_id="CALL-999").status == "unknown_call"


def test_out_of_context_turn_is_flagged(calls):
    other = calls["CALL-002"].turns[5]
    r = check_citation(calls, "CALL-002", other.ts, other.speaker, other.text, context_turns=set())
    assert r.ok and not r.in_context
