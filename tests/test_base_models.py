"""Model policy in agents/base.py — tiers, the cheap-first ladder, refusals."""

import json
from types import SimpleNamespace

import pytest

from agents import base
from agents.base import (
    BEST, CHEAP, REASONING, ModelRefused, best, ladder, run_json_agent, tiered,
)


def _parse(data):
    if "ok" not in data:
        raise ValueError("missing ok")
    return data


# ---- run_json_agent accepts one model or a ladder ------------------------------
def test_single_model_function(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("sys")
    out = run_json_agent(prompt, "u", _parse, model=lambda s, u: '{"ok": 1}')
    assert out == {"ok": 1}


def test_ladder_escalates_only_when_the_cheap_answer_is_unusable(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("sys")
    calls = []

    def cheap(s, u):
        calls.append("cheap")
        return "not json at all"

    def strong(s, u):
        calls.append("strong")
        return '{"ok": 2}'

    assert run_json_agent(prompt, "u", _parse, model=[cheap, strong]) == {"ok": 2}
    assert calls == ["cheap", "strong"]


def test_ladder_stops_at_the_first_good_answer(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("sys")
    calls = []

    def cheap(s, u):
        calls.append("cheap")
        return '{"ok": 1}'

    def strong(s, u):
        calls.append("strong")
        return '{"ok": 2}'

    assert run_json_agent(prompt, "u", _parse, model=[cheap, strong]) == {"ok": 1}
    assert calls == ["cheap"]


def test_ladder_raises_the_last_failure_when_every_rung_fails(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("sys")
    with pytest.raises(ValueError, match="missing ok"):
        run_json_agent(prompt, "u", _parse, model=[lambda s, u: "{}", lambda s, u: '{"no": 1}'])


def test_empty_ladder_rejected(tmp_path):
    prompt = tmp_path / "p.md"
    prompt.write_text("sys")
    with pytest.raises(ValueError, match="at least one model"):
        run_json_agent(prompt, "u", _parse, model=[])


def test_default_ladder_is_cheap_then_reasoning(monkeypatch):
    seen = []
    monkeypatch.setattr(base, "anthropic_model",
                        lambda s, u, **kw: seen.append(kw) or '{"ok": 1}')
    for fn in ladder(max_tokens=32000):
        fn("s", "u")
    assert [k["model"] for k in seen] == [CHEAP, REASONING]
    assert all(k["max_tokens"] == 32000 for k in seen)
    assert seen[0]["effort"] is None            # the cheap tier rejects the knob


def test_best_is_fable_at_high_effort(monkeypatch):
    seen = {}
    monkeypatch.setattr(base, "anthropic_model", lambda s, u, **kw: seen.update(kw) or "x")
    best(effort="xhigh", max_tokens=24000)("s", "u")
    assert seen == {"model": BEST, "effort": "xhigh", "max_tokens": 24000}


def test_tier_ids_are_undated():
    for tier in (CHEAP, REASONING, BEST):
        assert not tier[-8:].isdigit(), f"{tier} carries a date suffix"


# ---- the live call surface -----------------------------------------------------
def _effort_400():
    """A BadRequestError as the API raises it, without the SDK's HTTP plumbing."""
    import anthropic

    exc = anthropic.BadRequestError.__new__(anthropic.BadRequestError)
    Exception.__init__(exc, "This model does not support the effort parameter")
    exc.message = "This model does not support the effort parameter"
    return exc


class _FakeResp:
    def __init__(self, text, stop_reason="end_turn", category=None):
        self.content = [SimpleNamespace(type="text", text=text)]
        self.stop_reason = stop_reason
        self.stop_details = SimpleNamespace(category=category) if category else None


class _FakeClient:
    def __init__(self, responses, raise_on_effort=False):
        self.responses = list(responses)
        self.raise_on_effort = raise_on_effort
        self.calls = []

        class _Messages:
            def create(inner, **kw):
                self.calls.append(kw)
                if self.raise_on_effort and "output_config" in kw:
                    raise _effort_400()
                return self.responses.pop(0)

        self.messages = _Messages()


@pytest.fixture
def fake_anthropic(monkeypatch):
    import anthropic
    holder = {}

    def factory(*a, **k):
        return holder["client"]

    monkeypatch.setattr(anthropic, "Anthropic", factory)
    return holder


def test_refusal_raises_instead_of_returning_empty(fake_anthropic):
    fake_anthropic["client"] = _FakeClient([_FakeResp("", stop_reason="refusal", category="cyber")])
    with pytest.raises(ModelRefused, match="cyber"):
        base.anthropic_model("s", "u", model=BEST)


def test_effort_is_dropped_for_models_that_reject_it(fake_anthropic):
    client = _FakeClient([_FakeResp("hello")], raise_on_effort=True)
    fake_anthropic["client"] = client
    assert base.anthropic_model("s", "u", model=CHEAP, effort="low") == "hello"
    assert "output_config" in client.calls[0] and "output_config" not in client.calls[1]


def test_text_blocks_are_joined(fake_anthropic):
    resp = _FakeResp("a")
    resp.content.append(SimpleNamespace(type="thinking", thinking="…"))
    resp.content.append(SimpleNamespace(type="text", text="b"))
    fake_anthropic["client"] = _FakeClient([resp])
    assert base.anthropic_model("s", "u") == "ab"
