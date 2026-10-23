"""The Anthropic judge backend, with a stand-in client (no network)."""

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))

import run_eval  # noqa: E402


class FakeMessages:
    def __init__(self, reply: dict):
        self.reply, self.kwargs = reply, None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(content=[SimpleNamespace(type="tool_use", input=self.reply)])


def test_anthropic_judge_forces_the_tool_and_parses_it():
    reply = {
        "facts": [{"n": 1, "core": "supported", "details_covered": [1], "reason": "states £80K"}],
        "bonus": [], "penalties": [], "correct": "yes", "correct_reason": "main point right", "declines": False,
    }
    client = SimpleNamespace(messages=FakeMessages(reply))
    j = run_eval.judge_anthropic("QUESTION ...", client=client)
    assert j.correct == "yes" and j.facts[0].details_covered == [1]
    kw = client.messages.kwargs
    assert kw["tool_choice"] == {"type": "tool", "name": "record_judgement"}
    assert kw["system"] == run_eval.JUDGE_SYSTEM


def test_judge_schema_is_self_contained():
    schema = run_eval.inline_refs(run_eval.Judgement.model_json_schema())
    assert "$defs" not in str(schema) and "$ref" not in str(schema)
    assert schema["properties"]["facts"]["items"]["properties"]["core"]["enum"] == ["supported", "missing", "contradicted"]
