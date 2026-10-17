from pathlib import Path

import pytest

from callqa.index import chunk_call
from callqa.parse import _parse_participant, load_calls

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def calls():
    return load_calls(DATA)


def test_all_calls_parsed(calls):
    assert len(calls) == 20
    assert all(c.turns for c in calls)
    assert {c.category for c in calls} == {"prospect", "renewal", "churn", "cold_call"}


def test_company_header_variants(calls):
    by_id = {c.call_id: c for c in calls}
    assert by_id["CALL-001"].company == "Acme Logistics"  # PROSPECT:
    assert by_id["CALL-014"].company == "Verity Payments"  # CUSTOMER:


def test_every_speaker_is_a_listed_participant(calls):
    for c in calls:
        assert {t.side for t in c.turns} <= {"vendor", "customer"}, c.call_id


def test_turn_line_numbers_point_at_the_turn(calls):
    for c in calls:
        lines = c.path.read_text().splitlines()
        for t in c.turns:
            assert lines[t.line - 1].endswith(t.text)


def test_participant_with_note():
    p = _parse_participant("- Martine Duval, Director of Customer Operations, Silverline Travel (joined at 03:41)")
    assert (p.name, p.role, p.company, p.note) == (
        "Martine Duval", "Director of Customer Operations", "Silverline Travel", "joined at 03:41")
    assert p.side == "customer"


def test_chunks_cover_every_turn_and_stay_in_one_call(calls):
    for c in calls:
        chunks = chunk_call(c)
        covered = {t.idx for ch in chunks for t in ch.turns}
        assert covered == set(range(len(c.turns)))
        assert all(t.call_id == c.call_id for ch in chunks for t in ch.turns)
