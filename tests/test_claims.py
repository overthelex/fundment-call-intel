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

    found = read_call("Is SSO on all plans?", CALLS["CALL-006"], CALLS, MapLLM())
    assert [(t.ts, point) for t, point in found] == [("07:23", "p")]


def test_tally_counts_calls_and_drops_unknown_refs():
    from callqa.mapper import Tally, TallyItem, TallyRef, render_tally, tally

    t6, t1 = CALLS["CALL-006"].turns[5], CALLS["CALL-001"].turns[5]

    class TallyLLM:
        def structured(self, system, user, schema, **kw):
            return Tally(items=[
                TallyItem(item="rare", refs=[TallyRef(call_id="CALL-006", timestamp=t6.ts)]),
                TallyItem(item="common", refs=[TallyRef(call_id="CALL-006", timestamp=t6.ts),
                                               TallyRef(call_id="CALL-001", timestamp=t1.ts),
                                               TallyRef(call_id="CALL-009", timestamp="00:00")]),  # not a point
            ])

    items = tally("q", {"CALL-006": [(t6, "a")], "CALL-001": [(t1, "b")]}, TallyLLM())
    assert [(i, len(r)) for i, r in items] == [("common", 2), ("rare", 1)]
    assert "common: 2 of 2 calls" in render_tally(items, 2)


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
            return CallVerdict(verdict="no real next step", counts="no", evidence=[
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="SSO's included on all our plans"),
                MapPoint(timestamp="07:23", speaker="Alastair McCrae", quote="We'll book the pilot today"),
            ])

    f = judge_call("q", CALLS["CALL-006"], CALLS, VerdictLLM())
    assert f.verdict == "no real next step" and f.counts == "no"
    assert [p.quote for p in f.evidence] == ["SSO's included on all our plans"]


def test_comparison_sends_the_small_kinds_of_call_whole():
    from types import SimpleNamespace

    from callqa.pipeline import Pipeline, Plan

    plan = Plan(call_ids=[], categories=["renewal", "prospect"], scope="across", search_queries=[],
                entity_notes=[], vendor_consistency=False, product_topics=[], note_fields=[], assess_each_call=False)
    ids = [c for c in CALLS if CALLS[c].category in ("renewal", "prospect")]
    whole = Pipeline.whole_groups(SimpleNamespace(calls=CALLS), plan, ids)
    assert whole == sorted(c for c in ids if CALLS[c].category == "renewal")  # prospects, the largest kind, stay as notes
    assert Pipeline.whole_groups(SimpleNamespace(calls=CALLS), plan.model_copy(update={"categories": ["prospect"]}), ids) == []


def test_a_call_the_findings_count_but_the_answer_drops_is_reported():
    from callqa.mapper import Finding, uncovered

    def f(cid, company, counts):
        return Finding(call_id=cid, company=company, verdict="v", counts=counts, evidence=[])

    findings = [f("CALL-016", "Quarry Ridge Foods", "yes"), f("CALL-019", "Trafford Dental Group", "no"),
                f("CALL-020", "Kestrel Robotics", "partly"), f("CALL-018", "Beacon Housing Trust", "yes")]
    texts = ["Three of the four cold calls produced a follow-up; Beacon Housing Trust agreed to a meeting."]
    missing = uncovered(findings, texts, cited={"CALL-016"})
    assert [m.call_id for m in missing] == ["CALL-020"]  # a "no" may go unmentioned; named or cited is covered
