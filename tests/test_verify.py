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


def test_header_metadata_can_be_cited(calls):
    r = check_citation(calls, "CALL-007", "header", "header", "2,300 employees", context_turns={("CALL-007", -1)})
    assert r.status == "exact" and r.in_context and r.turn.line == 6


def test_speaker_with_role_suffix_still_matches(calls):
    t = calls["CALL-003"].turns[30]
    r = check_citation(calls, "CALL-003", "99:99", f"{t.speaker} (Some Role, Cedar & Finch)", t.text, set())
    assert r.status == "shifted" and r.turn == t


def test_words_said_by_someone_else_are_a_misattribution(calls):
    # CALL-014 [13:36] is Maya Chen; crediting her words to Sarah must fail
    r = check_citation(calls, "CALL-014", "13:36", "Sarah Lindqvist", "The right response was three days of an SE.", set())
    assert r.status == "wrong_speaker" and not r.ok


def test_exact_neighbour_beats_fuzzy_anchor(calls):
    # the quote is Sarah's [13:40]; Maya's [13:36] is only a near match and must not win
    r = check_citation(
        calls, "CALL-014", "13:36", "Sarah Lindqvist", "The right response was three days of an SE, yes.", set()
    )
    assert r.status == "shifted" and r.turn.ts == "13:40" and r.turn.speaker == "Sarah Lindqvist"


def test_speaker_written_with_role_after_comma(calls):
    t = calls["CALL-014"].turns[20]
    r = check_citation(calls, "CALL-014", t.ts, f"{t.speaker}, Some Role, Verity Payments", t.text, set())
    assert r.status == "exact"


def test_quote_from_another_call_is_rejected_but_located(calls):
    # Leo Grant's SSO line is in CALL-012, not CALL-015
    r = check_citation(calls, "CALL-015", "08:09", "Leo Grant", "SAML SSO is Enterprise.", set())
    assert r.status == "wrong_call" and not r.ok and r.turn.call_id == "CALL-012"


def test_wrong_call_shows_the_cited_call_and_where_the_words_are(calls):
    from types import SimpleNamespace

    from callqa.cli import _cite_line

    r = check_citation(calls, "CALL-003", "03:23", "Imogen Price", "And we've got Zapier already.", set())
    line = _cite_line(SimpleNamespace(calls=calls), r)
    assert line.splitlines()[0].startswith("    ✗ CALL-003 [03:23] Imogen Price")
    assert "→ said in CALL-006 [03:23] by Imogen Price (COO, Fable Media)" in line
    assert "call-006_fable_media.txt:46" in line
