"""Tests for the orchestrator / event bus (A9)."""

import pytest

from pipeline.orchestrator import Orchestrator, Event


def test_chain_of_events_runs_in_order():
    orch = Orchestrator()
    # drawing_uploaded -> extract -> audit -> priced
    orch.on("drawing_uploaded", "A1", lambda e: [Event("takeoff_ready", {"n": 5})])
    orch.on("takeoff_ready", "E7", lambda e: [Event("audit_passed", e.payload)])
    orch.on("audit_passed", "E3", lambda e: [Event("priced", e.payload)])
    seen = []
    orch.on("priced", "done", lambda e: seen.append(e.payload["n"]) or [])

    orch.emit(Event("drawing_uploaded", {"file": "ST7757"}))
    handlers = [d.handler for d in orch.log]
    assert handlers == ["A1", "E7", "E3", "done"]
    assert seen == [5]


def test_causality_is_recorded():
    orch = Orchestrator()
    orch.on("a", "h1", lambda e: [Event("b")])
    orch.on("b", "h2", lambda e: [])
    orch.emit(Event("a", id="root"))
    tr = orch.trace()
    b = [t for t in tr if t["event"] == "b"][0]
    assert b["caused_by"] == "root"   # walk backwards from any record


def test_unhandled_event_is_logged_not_lost():
    orch = Orchestrator()
    orch.emit(Event("mystery"))
    assert orch.log[0].handler == "(unhandled)"


def test_multiple_handlers_for_one_event():
    orch = Orchestrator()
    calls = []
    orch.on("evt", "A", lambda e: calls.append("A") or [])
    orch.on("evt", "B", lambda e: calls.append("B") or [])
    orch.emit(Event("evt"))
    assert calls == ["A", "B"]


def test_runaway_loop_is_stopped():
    orch = Orchestrator(max_steps=50)
    orch.on("ping", "loop", lambda e: [Event("ping")])
    with pytest.raises(RuntimeError):
        orch.emit(Event("ping"))


def test_handler_error_is_recorded_and_raised():
    orch = Orchestrator()
    def boom(e):
        raise ValueError("nope")
    orch.on("x", "bad", boom)
    with pytest.raises(ValueError):
        orch.emit(Event("x"))
    assert orch.log[-1].error.startswith("ValueError")
