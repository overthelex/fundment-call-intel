"""Vendor-claim extraction keeps only verified quotes said by vendor staff (offline, stand-in LLM)."""

from pathlib import Path

from callqa.claims import CallClaims, ClaimStore, VendorClaim, extract
from callqa.parse import load_calls

CALLS = {c.call_id: c for c in load_calls(Path(__file__).resolve().parent.parent / "data")}


class FakeLLM:
    chat_model = "fake"

    def __init__(self, claims):
        self.claims = claims

    def structured(self, system, user, schema, **kw):
        return CallClaims(claims=self.claims)


def claim(ts, speaker, quote, topic="SSO, SCIM and identity"):
    return VendorClaim(topic=topic, statement="s", timestamp=ts, speaker=speaker, quote=quote)


def test_extract_drops_invented_and_customer_quotes():
    llm = FakeLLM([
        claim("07:23", "Alastair McCrae", "SSO's included on all our plans, that's standard."),  # real, vendor
        claim("07:23", "Alastair McCrae", "SSO is free forever on every plan."),                # invented
        claim("11:34", "Imogen Price", "Is it?", topic="other product facts"),                   # customer
    ])
    kept = extract(CALLS["CALL-006"], CALLS, llm)
    assert [(c.speaker, c.quote) for c in kept] == [("Alastair McCrae", "SSO's included on all our plans, that's standard.")]


def test_context_groups_by_topic_and_returns_cited_turns(tmp_path):
    store = ClaimStore(list(CALLS.values()), None)
    store._claims = extract(CALLS["CALL-006"], CALLS, FakeLLM([
        claim("07:23", "Alastair McCrae", "SSO's included on all our plans"),
        claim("11:30", "Alastair McCrae", "it's completely no-code", topic="no-code vs code, technical skills needed"),
    ]))
    text, turns = store.context()
    assert text.index("## TOPIC: SSO, SCIM and identity") < text.index("## TOPIC: no-code vs code")
    assert [t.ts for t in turns] == ["07:23", "11:30"]


def test_context_can_be_limited_to_topics(tmp_path):
    store = ClaimStore(list(CALLS.values()), None)
    store._claims = extract(CALLS["CALL-006"], CALLS, FakeLLM([
        claim("07:23", "Alastair McCrae", "SSO's included on all our plans"),
        claim("11:30", "Alastair McCrae", "it's completely no-code", topic="no-code vs code, technical skills needed"),
    ]))
    text, turns = store.context(topics=["SSO, SCIM and identity"])
    assert "no-code" not in text
    assert [t.ts for t in turns] == ["07:23"]


def test_map_step_keeps_only_verified_turns():
    from callqa.mapper import CallNotes, MapPoint, read_call

    class MapLLM:
        def structured(self, system, user, schema, **kw):
            return CallNotes(points=[
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="SSO's included on all our plans", point="p"),
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="SSO is free forever", point="p"),
            ])

    turns = read_call("Is SSO on all plans?", CALLS["CALL-006"], CALLS, MapLLM())
    assert [t.ts for t in turns] == ["07:23"]


def test_topic_conflict_check_drops_a_side_with_no_verified_quote():
    from callqa.conflicts import Statement, TopicConflict, TopicConflicts, check_topic

    topic = "no-code vs code, technical skills needed"
    turns = [CALLS["CALL-006"].turns[110], CALLS["CALL-001"].turns[80]]

    class ConflictLLM:
        def structured(self, system, user, schema, **kw):
            real_a = Statement(call_id="CALL-006", timestamp="11:30", speaker="Alastair McCrae", quote="it's completely no-code")
            real_b = Statement(call_id="call-001", timestamp="12:12", speaker="Jon Bell", quote="We don't claim every workflow is no-code")
            fake_b = Statement(call_id="CALL-001", timestamp="12:12", speaker="Jon Bell", quote="Everything needs JavaScript")
            return TopicConflicts(conflicts=[
                TopicConflict(what="real", side_a=[real_a], side_b=[real_b, fake_b]),
                TopicConflict(what="invented", side_a=[real_a], side_b=[fake_b]),
            ])

    found = check_topic(topic, "text", turns, CALLS, ConflictLLM())
    assert [c.what for c in found] == ["real"]
    assert [(s.call_id, s.timestamp) for s in found[0].side_b] == [("CALL-001", "12:12")]  # normalised, invented one dropped


def test_per_call_verdict_keeps_only_verified_evidence():
    from callqa.mapper import CallVerdict, MapPoint, judge_call

    class VerdictLLM:
        def structured(self, system, user, schema, **kw):
            return CallVerdict(verdict="no real next step", evidence=[
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="SSO's included on all our plans"),
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="We'll book the pilot today"),
            ])

    f = judge_call("q", CALLS["CALL-006"], CALLS, VerdictLLM())
    assert f.verdict == "no real next step"
    assert [p.quote for p in f.evidence] == ["SSO's included on all our plans"]
