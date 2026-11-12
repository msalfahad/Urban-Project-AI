"""R-T728-1 on a synthetic villa W728 (not the development villa), hand-made: four plastered rooms and one facade.

W728 host lines (m2): R1 RELEASED 40.00; R2 HELD 30.00 .. 34.00 (roof build-up not printed); R3 HELD 25.00 .. 25.00
(point bound, held on a designer item); FAC HELD blank (exterior face rows queued); X EXCLUDED.
Beads by hand (m): R1 corner 2.95 (G1 2.95 x 1); R2 door ring 2 x 2.20 + 0.90 = 5.30; R3 two corners 2 x 3.10 = 6.20;
FAC corner 3 x 3.40 = 10.20; R2 arch HELD blank (springing not printed); R3 landing corner HELD 2.40 .. 2.60.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t728"))
import t728_rules as R  # noqa: E402

LINES = {
    "R1": {"line_id": "R1", "class": "RELEASED", "measured_net": 40.0, "held_low": None, "held_high": None, "unit": "m2"},
    "R2": {"line_id": "R2", "class": "HELD", "measured_net": None, "held_low": 30.0, "held_high": 34.0, "unit": "m2"},
    "R3": {"line_id": "R3", "class": "HELD", "measured_net": None, "held_low": 25.0, "held_high": 25.0, "unit": "m2"},
    "FAC": {"line_id": "FAC", "class": "HELD", "measured_net": None, "held_low": None, "held_high": None, "unit": "m2"},
    "X": {"line_id": "X", "class": "EXCLUDED", "measured_net": None, "held_low": None, "held_high": None, "unit": "m2"},
}


def restate(host, *, length=None, low=None, high=None, own="", hcause="host cause"):
    hs = R.host_state(LINES[host])
    return R.bead_state(*R.ledger_form(length=length, low=low, high=high), hs, own_cause=own, host_cause=hcause)


def row(eid, host, b):
    return {"edge_id": eid, "host_line": host, "host_state": R.host_state(LINES[host]), "owner_trade": R.OWNER_TRADE,
            "bead_state": b["state"], "value": b["value"], "low": b["low"], "high": b["high"]}


# ---- host states -------------------------------------------------------------------------------------------------
def test_host_states():
    assert [R.host_state(LINES[k]) for k in ("R1", "R2", "R3", "FAC")] == [R.RELEASED, R.BOUNDED, R.BOUNDED, R.BLANK]


def test_point_bound_host_is_held_not_released():
    assert R.host_state(LINES["R3"]) == R.BOUNDED
    assert R.host_bound_text(LINES["R3"], R.BOUNDED) == "HELD 25.0 .. 25.0 m2"


@pytest.mark.parametrize("bad", [None, LINES["X"],
                                 {"line_id": "Z", "class": "HELD", "held_low": None, "held_high": 3.0},
                                 {"line_id": "Z", "class": "HELD", "held_low": 5.0, "held_high": 3.0},
                                 {"line_id": "Z", "class": "RELEASED", "measured_net": 0.0}])
def test_adverse_host_absent_excluded_or_malformed(bad):
    with pytest.raises(R.BeadStateError):
        R.host_state(bad)


# ---- normal: the state table --------------------------------------------------------------------------------------
def test_released_host_releases_measured_bead():
    b = restate("R1", length=2.95)
    assert (b["state"], b["value"], b["low"], b["high"]) == (R.RELEASED, 2.95, None, None)


def test_bounded_host_holds_measured_bead_at_its_own_length():
    b = restate("R2", length=2 * 2.20 + 0.90)
    assert (b["state"], b["low"], b["high"], b["value"]) == (R.HELD_BOUND, 5.3, 5.3, None)
    assert "host cause" in b["cause"]


def test_point_host_holds_bead_never_releases():
    b = restate("R3", length=2 * 3.10)
    assert b["state"] == R.HELD_BOUND and b["low"] == b["high"] == 6.2


def test_held_bead_bound_kept_on_bounded_host_with_both_causes():
    b = restate("R3", low=2.40, high=2.60, own="under a landing")
    assert (b["low"], b["high"]) == (2.4, 2.6)
    assert "bead: under a landing" in b["cause"] and "host: host cause" in b["cause"]


def test_held_bead_bound_on_released_host_stays_held_own_cause():
    b = restate("R1", low=2.40, high=2.60, own="under a landing")
    assert (b["state"], b["low"], b["high"], b["cause"]) == (R.HELD_BOUND, 2.4, 2.6, "under a landing")


# ---- adverse ------------------------------------------------------------------------------------------------------
def test_bead_on_blank_host_stays_blank_ledger_as_text_only():
    b = restate("FAC", length=3 * 3.40, hcause="face rows queued")
    assert b["state"] == R.HELD_BLANK
    assert (b["value"], b["low"], b["high"]) == (None, None, None)
    assert b["ledger_ref"].startswith("ledger 10.2 m") and "not a quantity" in b["ledger_ref"]


def test_held_bound_bead_on_blank_host_stays_blank():
    b = restate("FAC", low=0.0, high=1.20, own="stop-end parts not printed")
    assert b["state"] == R.HELD_BLANK and b["low"] is None and "0.0 .. 1.2" in b["ledger_ref"]


def test_blank_bead_stays_blank_on_every_host():
    for h in ("R1", "R2", "R3", "FAC"):
        b = restate(h, own="springing not printed")
        assert b["state"] == R.HELD_BLANK and b["value"] is None and b["low"] is None


@pytest.mark.parametrize("kw", [{"length": 0.0}, {"length": -1.0}, {"low": 0.0, "high": 0.0},
                                {"low": 2.0, "high": 1.0}, {"low": 1.0}, {"length": 2.0, "low": 1.0, "high": 2.0},
                                {"low": -0.5, "high": 1.0}])
def test_adverse_zero_negative_or_malformed_ledger(kw):
    with pytest.raises(R.BeadStateError):
        R.ledger_form(**kw)


def test_zero_low_with_nonzero_high_is_a_bound_not_zero():
    assert R.ledger_form(low=0.0, high=11.9) == (R.HELD_BOUND, None, 0.0, 11.9)


def test_rows_check_normal():
    rows = [row("R1#V1", "R1", restate("R1", length=2.95)), row("R2#D1", "R2", restate("R2", length=5.3)),
            row("FAC#C1", "FAC", restate("FAC", length=10.2))]
    assert R.check_rows(rows) == 3


def test_adverse_arris_counted_twice_or_under_two_hosts():
    a = row("R2#V1", "R2", restate("R2", length=3.1))
    with pytest.raises(R.BeadStateError, match="twice"):
        R.check_rows([a, dict(a)])
    with pytest.raises(R.BeadStateError, match="twice"):
        R.check_rows([a, row("R2#V1", "R3", restate("R3", length=3.1))])


def test_adverse_released_bead_on_held_host_refused():
    r = row("R2#V2", "R2", restate("R2", length=3.1))
    r.update(bead_state=R.RELEASED, value=3.1, low=None, high=None)
    with pytest.raises(R.BeadStateError, match="RELEASED on a BOUNDED host"):
        R.check_rows([r])


def test_adverse_blank_bead_with_number_or_held_as_zero_refused():
    r = row("FAC#C2", "FAC", restate("FAC", length=3.4))
    r["low"] = 0.0
    with pytest.raises(R.BeadStateError):
        R.check_rows([r])
    with pytest.raises(R.BeadStateError):
        R.check_one({"state": R.HELD_BOUND, "value": None, "low": 0.0, "high": 0.0})


def test_adverse_owner_trade_missing():
    r = row("R1#V3", "R1", restate("R1", length=2.95))
    r["owner_trade"] = "paint"
    with pytest.raises(R.BeadStateError, match="owner trade"):
        R.check_rows([r])


def test_mirror_order_independent():
    rows = [row("R1#V1", "R1", restate("R1", length=2.95)), row("R3#V1", "R3", restate("R3", length=3.1))]
    assert R.check_rows(rows) == R.check_rows(list(reversed(rows)))
