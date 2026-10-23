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
    assert store.ingest() == 0 and llm.reads == 1  # unchanged call: not read again
    assert store.counts() == {"calls": 1, "claims": 1, "notes": 1}  # the invented quote was dropped
    notes, vecs = store.notes(["CALL-006"], ["pricing, budget and commercial terms"])
    assert [n.turn_idx for n in notes] and vecs.shape == (1, 3)
    assert store.notes(["CALL-006"], ["needs and requirements"])[0] == []
