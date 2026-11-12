"""R-T748-1 on a hand-built synthetic villa W748 (not the development villa): restatement on a newer index, merged-hub
wiring, blocker refresh, released lines unchanged, downgrade records, one hub per target, no-line families. Every
expected value below is written by hand from the fixture, never from the module."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t748"))
import t748_rules as R  # noqa: E402

A = "L-" + "a1" * 10
B = "L-" + "b2" * 10
B2 = "L-" + "b2" * 9 + "c3"          # a neighbour sharing B's first 18 hex digits
C = "L-" + "c3" * 10


def ln(cls="HELD", value=None, low=None, high=None, unit="m2", code="FIN.PAINT"):
    return {"class": cls, "measured_net": value, "held_low": low, "held_high": high, "unit": unit, "item_code": code}


OLD = {A: ln(low=10.0, high=12.0), B: ln("RELEASED", 56.0131), B2: ln(low=1.0, high=2.0)}
NEW = {A: ln(low=10.5, high=12.0), B: ln("RELEASED", 56.0131), B2: ln(low=1.0, high=2.0), C: ln(code="FIN.WP.ROOF")}


# rule 7 (ids) through resolve
def test_full_and_unique_prefix_resolve():
    assert R.resolve(A, NEW.keys()) == A
    assert R.resolve("L-a1a1a1a1", NEW.keys()) == A


def test_adverse_absent_id_never_mapped_to_neighbour():
    gone = "L-" + "b2" * 9 + "ff"
    with pytest.raises(R.ReadinessError, match="STALE"):
        R.resolve(gone, NEW.keys())
    with pytest.raises(R.ReadinessError, match="ambiguous"):
        R.resolve("L-b2b2b2b2b2", NEW.keys())
    with pytest.raises(R.ReadinessError, match="short"):
        R.resolve("L-a1a1", NEW.keys())


# rule 1
def test_host_unchanged_and_changed_by_named_package():
    assert R.host_status(B, OLD, NEW, {}) == ("UNCHANGED", [])
    assert R.host_status(A, OLD, NEW, {A: {"T-900"}}) == ("HOST_CHANGED", ["T-900"])
    assert R.host_status(C, OLD, NEW, {C: {"T-901"}}) == ("HOST_ADDED", ["T-901"])


def test_adverse_host_moved_without_package_or_absent():
    with pytest.raises(R.ReadinessError, match="no package"):
        R.host_status(A, OLD, NEW, {})
    with pytest.raises(R.ReadinessError, match="STALE"):
        R.host_status("L-" + "dd" * 10, OLD, NEW, {})


# rule 3
def test_blockers_refreshed_against_the_board():
    board = {"T-900": "MERGED", "T-901": "READY", "T-902": "QUEUED"}
    open_, cleared = R.refresh_blockers(["WAITS T-900 (x)", "PENDING_ON T-901", "WAITS T-902 (y)", "RULING ORR-1"], board)
    assert cleared == ["WAITS T-900 (x) -> CLEARED (T-900 MERGED)"]
    assert open_ == ["PENDING_ON T-901 (READY)", "WAITS T-902 (QUEUED) (y)", "RULING ORR-1"]


def test_adverse_blocker_on_unknown_row():
    with pytest.raises(R.ReadinessError, match="absent from the board"):
        R.refresh_blockers(["WAITS T-999"], {})


# rule 4: 56.0131 released, a ledger 56.01315 (0.00005 apart, cause named)
def test_released_line_kept_within_named_rounding():
    assert R.released_action(56.0131, "56.013150", True) == ("KEEP_RELEASED", "0.000050")
    assert R.released_action(56.0131, "56.0131", False) == ("KEEP", "0")


def test_adverse_released_change_flagged():
    assert R.released_action(56.0131, "56.013150", False)[0] == "CHANGE_RELEASED"   # rounding not named
    assert R.released_action(56.0131, "56.5131", True) == ("CHANGE_RELEASED", "0.5000")


# rule 5
REC = {"downgrade_id": "DG-1234567890abcdef", "line_ids": [C], "state": "HELD", "engine_qty": 9.5}


def test_downgrade_not_applied_and_applied():
    rows, f = R.downgrade_rows([REC], NEW, set())
    assert rows[0]["status"] == "NOT_APPLIED_IN_INDEX" and rows[0]["line_id"] == C and f == []
    rows, _ = R.downgrade_rows([REC], NEW, {"DG-1234567890abcdef"})
    assert rows[0]["status"] == "APPLIED"


def test_adverse_cited_id_without_record_and_absent_line():
    _, f = R.downgrade_rows([REC], NEW, set(), ("DG-12345678", "DG-ffff0000"))
    assert f == ["DG-ffff0000: cited on the board, no record with this id (record ids: DG-1234567890abcdef)"]
    with pytest.raises(R.ReadinessError, match="absent"):
        R.downgrade_rows([{**REC, "line_ids": ["L-" + "ee" * 10]}], NEW, set())


# rule 6
def test_one_hub_per_target_normal_and_mirror():
    rows = [{"target": A, "hub": "P1", "action": "CHANGE"}, {"target": A, "hub": "P1", "action": "TEXT"},
            {"target": B, "hub": "P2", "action": "ADD"}, {"target": C, "hub": "P3", "action": "KEEP"}]
    assert R.one_hub_per_target(rows) == {A: "P1", B: "P2"}
    assert R.one_hub_per_target(list(reversed(rows))) == {A: "P1", B: "P2"}


def test_adverse_two_hubs_on_one_line():
    rows = [{"target": A, "hub": "P1", "action": "CHANGE"}, {"target": A, "hub": "P2", "action": "DOWNGRADE"}]
    with pytest.raises(R.ReadinessError, match="two hubs"):
        R.one_hub_per_target(rows)
    assert R.one_hub_per_target(rows, {A: "decider T-903"}) == {A: "P1"}


# rule 7
def test_no_line_family_kept_held_with_hub_or_named():
    r = R.add_family("B9-05", "ROOF-1", None, True, "0.000000", "14.5")
    assert r["target"] == "B9-05@ROOF-1" and r["hub"] == "NO_PACKAGE_ROW" and r["action"] == "ADD_FAMILY"


def test_adverse_held_family_as_zero_or_inverted():
    with pytest.raises(R.ReadinessError, match="0 .. 0"):
        R.add_family("B9-05", "ROOF-1", "P9", True, "0", "0.000")
    with pytest.raises(R.ReadinessError, match="low above high"):
        R.add_family("B9-05", "ROOF-1", "P9", True, "3", "2")
