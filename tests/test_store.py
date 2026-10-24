"""The ingestion store reads each call once, keeps only verified quotes, and filters notes by field."""

from pathlib import Path

from callqa.claims import CallClaims, VendorClaim
from callqa.notes import CallNote, CallNotes
from callqa.parse import load_calls
from callqa.store import Store

CALLS = [c for c in load_calls(Path(__file__).resolve().parent.parent / "data") if c.call_id == "CALL-006"]


class FakeLLM:
    chat_model, embed_model = "fake", "fake-embed"

    def __init__(self):
        self.reads = 0

    def structured(self, system, user, schema, **kw):
        if schema is CallClaims:
            self.reads += 1
            return CallClaims(claims=[VendorClaim(topic="SSO, SCIM and identity", statement="s", timestamp="07:23",
                                                  speaker="Alastair McCrae", quote="SSO's included on all our plans")])
        return CallNotes(notes=[
            CallNote(field="pricing, budget and commercial terms", point="p", timestamp="07:23",
                     speaker="Alastair McCrae", quote="SSO's included on all our plans"),
            CallNote(field="needs and requirements", point="invented", timestamp="07:23",
                     speaker="Alastair McCrae", quote="we need a moon base"),
        ])

    def embed(self, texts, usage=None):
        return [[1.0, 0.0, 0.0] for _ in texts]


def test_ingest_is_idempotent_and_keeps_verified_notes(tmp_path):
    llm = FakeLLM()
    store = Store(CALLS, llm, path=tmp_path / "db.sqlite")
    assert store.ingest() == 1
    assert store.ingest() == 0 and llm.reads == 2  # two claim passes; unchanged call: not read again
    assert store.counts() == {"calls": 1, "claims": 1, "notes": 1}  # the invented quote was dropped
    notes, vecs = store.notes(["CALL-006"], ["pricing, budget and commercial terms"])
    assert [n.turn_idx for n in notes] and vecs.shape == (1, 3)
    assert store.notes(["CALL-006"], ["needs and requirements"])[0] == []


def test_an_empty_extraction_is_retried(tmp_path):
    class FlakyLLM(FakeLLM):
        def structured(self, system, user, schema, **kw):
            if schema is CallClaims and self.reads == 0:
                self.reads += 1
                return CallClaims(claims=[])
            return super().structured(system, user, schema, **kw)

    llm = FlakyLLM()
    store = Store(CALLS, llm, path=tmp_path / "db.sqlite")
    store.ingest()
    assert llm.reads == 2 and store.counts()["claims"] == 1


def test_first_question_from_several_threads_ingests_once(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    llm = FakeLLM()
    store = Store(CALLS, llm, path=tmp_path / "db.sqlite")
    with ThreadPoolExecutor(4) as pool:
        list(pool.map(lambda _: store.ensure(), range(4)))
    assert llm.reads == 2 and store.counts()["claims"] == 1


def test_two_claim_passes_are_merged():
    from callqa.claims import StoredClaim
    from callqa.store import merge_claims

    def c(idx, topic, quote):
        return StoredClaim(call_id="CALL-006", turn_idx=idx, topic=topic, statement="s", speaker="x", quote=quote)

    a = [c(82, "SSO, SCIM and identity", "SSO's included on all our plans")]
    b = [c(82, "SSO, SCIM and identity", "included on all our plans"), c(110, "no-code vs code, technical skills needed", "it's completely no-code")]
    assert [(m.turn_idx, m.quote) for m in merge_claims(a, b)] == [(82, "SSO's included on all our plans"), (110, "it's completely no-code")]


def test_notes_on_an_overlap_turn_come_from_the_first_part():
    from callqa.notes import StoredNote
    from callqa.store import merge_notes

    def n(idx, field, point):
        return StoredNote(call_id="CALL-004", turn_idx=idx, field=field, point=point, speaker="x", quote="q")

    first = [n(10, "needs and requirements", "a"), n(11, "needs and requirements", "b")]
    second = [n(11, "needs and requirements", "b again"), n(11, "pains and current process", "c"), n(12, "needs and requirements", "d")]
    assert [(m.turn_idx, m.point) for m in merge_notes(first, second)] == [(10, "a"), (11, "b"), (11, "c"), (12, "d")]
