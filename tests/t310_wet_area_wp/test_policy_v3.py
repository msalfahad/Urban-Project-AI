"""T-310: waterproofing policy V3 = V2 rows + the F-C-T458-2 fix (an all-held item prints HELD, never a 0.0
subtotal). Hand room: 3.00 x 2.00 m, one door 0.80 m in a 0.20 m wall (as the T-458 tests): floor 6.000 + doorway
piece 0.160 = 6.160 m2; upturn run (10.000 - 0.800) x 0.20 = 1.840 m2, the doorway segment HELD while the detail is
not known (PARTIAL), billed 0.160 beside the piece for a separate return (MEASURED 2.000)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import waterproofing_policy_v2 as WP2  # noqa: E402
from engine.source import waterproofing_policy_v3 as WP3  # noqa: E402

DOOR = {"id": "D1", "width_m": 0.80, "wall_t_m": 0.20}


def test_rows_are_v2_rows():
    for det in (None, WP3.COVERAGE_INSIDE_PIECE, WP3.SEPARATE_RETURN):
        kw = dict(floor_m2=6.0, boundary_lm=10.0, doors=[dict(DOOR, doorway_detail=det)], room="r")
        assert WP3.wet(**kw)["items"] == WP2.wet(**kw)["items"]


def test_normal_subtotals():
    r = WP3.wet(floor_m2=6.0, boundary_lm=10.0, doors=[dict(DOOR, doorway_detail=None)], room="r")
    assert r["totals"]["FIN.WP.FLOOR"] == {"measured_m2": pytest.approx(6.16), "measured_rows": 2, "held_rows": 0,
                                           "not_billed_rows": 0, "state": "MEASURED"}
    up = r["totals"]["FIN.WP.UPTURN"]
    assert up["measured_m2"] == pytest.approx(1.84) and up["state"] == "PARTIAL" and up["held_rows"] == 1
    sep = WP3.wet(floor_m2=6.0, boundary_lm=10.0, doors=[dict(DOOR, doorway_detail=WP3.SEPARATE_RETURN)], room="r")
    assert sep["totals"]["FIN.WP.UPTURN"]["measured_m2"] == pytest.approx(2.0)
    assert sep["totals"]["FIN.WP.UPTURN"]["state"] == "MEASURED"


def test_all_held_item_prints_held_not_zero():   # F-C-T458-2, the adverse case
    r = WP3.wet(floor_m2=None, boundary_lm=None, doors=[{"id": "D1", "width_m": None, "wall_t_m": None}], room="r")
    assert r["state"] == "HELD"
    for t in r["totals"].values():
        assert t["measured_m2"] is None and t["state"] == "HELD" and t["held_rows"]
    v2 = WP2.wet(floor_m2=None, boundary_lm=None, doors=[{"id": "D1", "width_m": None, "wall_t_m": None}], room="r")
    assert all(t["measured_m2"] == 0.0 for t in v2["totals"].values())   # V2 kept unchanged as history


def test_not_billed_only_item():
    items = [{"item": "X", "component": "c", "state": WP3.NOT_BILLED, "m2": None}]
    assert WP3.subtotals(items)["X"]["state"] == WP3.NOT_BILLED


def test_bad_rows_refused():
    with pytest.raises(ValueError, match="without a figure"):
        WP3.subtotals([{"item": "X", "component": "c", "state": WP3.MEASURED, "m2": None}])
    with pytest.raises(ValueError, match="held is blank"):
        WP3.subtotals([{"item": "X", "component": "c", "state": WP3.HELD, "m2": 0.0}])
    with pytest.raises(ValueError, match="unknown row state"):
        WP3.subtotals([{"item": "X", "component": "c", "state": "GUESS", "m2": 1.0}])


def test_upturn_run_window_free_and_held_without_width():
    r = WP3.upturn_run(boundary_lm=8.7, door_widths_m=[0.8], room="bath")
    assert (r["run_m2"], r["run_lm"], r["upturn_m"]) == (1.58, 7.9, 0.2)
    assert r["segments"] == [{"state": "HELD", "reason": "DOORWAY_CONTINUATION_NOT_ESTABLISHED", "if_billed_m2": 0.16}]
    with pytest.raises(ValueError, match="exceed the boundary"):
        WP3.upturn_run(boundary_lm=0.5, door_widths_m=[0.8], room="bath")


def test_distinct_policy_id():
    assert WP3.POLICY_ID not in (WP2.POLICY_ID, "WATERPROOFING_POLICY_V1")
