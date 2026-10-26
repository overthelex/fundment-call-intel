from pathlib import Path

import pytest

from callqa.mapper import Blocker, BuyingSignals, MapPoint, Signal, WaitsOn, rate_call, ranking_text, tier_of
from callqa.parse import load_calls

DATA = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def calls():
    return {c.call_id: c for c in load_calls(DATA)}


def test_tier_from_signals():
    top = {"sponsor": "committed", "timeline": "dated", "next_step": "pilot"}
    assert tier_of(top, False) == ("strongest", 6)
    assert tier_of(top, True)[0] == "conditional"  # the decision waits on something else
    assert tier_of({"sponsor": "engaged", "timeline": "dated", "next_step": "follow_up"}, False) == ("conditional", 4)
    assert tier_of({"sponsor": "engaged", "timeline": "vague", "next_step": "follow_up"}, False)[0] == "unlikely near-term"


class FakeLLM:
    def __init__(self, out):
        self.out = out

    def structured(self, *args, **kwargs):
        return self.out


REAL = MapPoint(timestamp="00:39", speaker="Noah Williams", quote="Connector breadth is genuinely good.", point="x")
MADE_UP = MapPoint(timestamp="00:44", speaker="Hannah Cole", quote="We will sign the contract this week.", point="y")


def test_a_signal_without_a_real_quote_does_not_count(calls):
    out = BuyingSignals(
        sponsor=Signal(level="committed", evidence=MADE_UP),
        timeline=Signal(level="dated", evidence=REAL),
        next_step=Signal(level="pilot", evidence=REAL),
        waits_on=WaitsOn(answer="yes", evidence=MADE_UP),
        blockers=[Blocker(kind="gate", description="invented gate", evidence=MADE_UP)],
    )
    f = rate_call(calls["CALL-005"], calls, FakeLLM(out))
    assert f.signals["sponsor"] == "none"  # the made-up quote fails the citation check
    assert f.caveats == []  # neither the unbacked wait nor the unbacked gate counts or shows
    assert (f.tier, f.score) == ("conditional", 4)


def test_ranking_is_written_from_the_tiers(calls):
    out = BuyingSignals(
        sponsor=Signal(level="committed", evidence=REAL), timeline=Signal(level="dated", evidence=REAL),
        next_step=Signal(level="pilot", evidence=REAL), waits_on=WaitsOn(answer="no"),
        blockers=[Blocker(kind="rival", description="Tray has a head start", evidence=REAL)],
    )
    f = rate_call(calls["CALL-005"], calls, FakeLLM(out))
    text = ranking_text([f])
    assert "Strongest: Ember Financial (rival: Tray has a head start)." in text
    assert "no prospect has committed" in text
