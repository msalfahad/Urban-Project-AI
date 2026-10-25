"""T-170 hand-calculated fixture, villa T170-K (NOT Alsenan): three isolated footings (one drawn turned 90 deg), one
ground beam, existing ground sloping across footing A, one existing-ground corner missing at footing C, a printed
formation of -1.80 under a printed 'not less than 1.50 m' limit, working space stated as a project fact (0.30 m).

Hand calculation (detail: blinding 0.10 projecting 0.10, underlay 0.07):
  A 2.00 x 1.50 x 0.40 at (0, 0); EG corners 0.00 / 0.00 / -0.10 / -0.10 -> mean -0.05; D = -0.05 + 1.80 = 1.75
    neat (2.20 x 1.70) = 3.74; with ws (2.80 x 2.30) = 6.44; excavation 6.44 x 1.75 = 11.27 m3
    chain above F: 0.10 / 0.17 / 0.57 -> absolute -1.70 / -1.63 / -1.23
    buried: blinding 0.374, underlay 3.00 x 0.07 = 0.21, footing 1.20, neck 0.30 (stated), GB in pit 0.12 (stated)
    backfill 11.27 - 2.204 = 9.066 m3
  B 1.20 x 1.20 x 0.30 at (3.0, 0); EG -0.20; D = 1.60; plan (2.0)^2 = 4.00; excavation 6.40 m3; neck not stated ->
    backfill HELD
  C 1.00 x 2.40 x 0.50 drawn 2.40 x 1.00 at (0, 1.6); one EG corner missing -> excavation HELD (not 0)
  neat A / C: x -0.1 .. 2.1 vs -0.1 .. 2.5 (2.2), y -0.1 .. 1.6 vs 1.5 .. 2.7 (0.1) -> 0.22 m2; footings do not touch
  A / B: neat gap 3.0 - 0.1 - 2.1 = 0.8 -> pits merge for ws > 0.40
  G1 0.30 x 3.00, depth 0.40, top -0.20, EG 0.00 -> blinding bottom -0.70, neat 3.00 x 0.50 = 1.50, 1.05 m3
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t170"))
import excavation_ledger_v1 as X  # noqa: E402

DET = {"P": {"blinding_m": 0.10, "underlay_m": 0.07, "projection_m": 0.10}}


def fac(v):
    return {"value": v, "status": "DRAWING-CONFIRMED"}


def villa():
    fts = [
        {"id": "A", "type": "K1", "detail": "P", "L_m": X.to_m(200, "cm"), "W_m": X.to_m(150, "cm"), "H_m": 0.40,
         "x0_m": 0.0, "y0_m": 0.0, "dx_m": X.to_m(2000, "mm"), "dy_m": X.to_m(1500, "mm"),
         "gb_in_pit_m3_known": True, "gb_in_pit_m3": 0.12},
        {"id": "B", "type": "K2", "detail": "P", "L_m": 1.2, "W_m": 1.2, "H_m": 0.30,
         "x0_m": 3.0, "y0_m": 0.0, "dx_m": 1.2, "dy_m": 1.2},
        {"id": "C", "type": "K3", "detail": "P", "L_m": 1.0, "W_m": 2.4, "H_m": 0.50,
         "x0_m": 0.0, "y0_m": 1.6, "dx_m": 2.4, "dy_m": 1.0},
    ]
    beams = [{"id": "G1", "detail": "P", "width_m": 0.30, "length_m": 3.0, "depth_m": 0.40, "top": fac(-0.20)}]
    levels = {"details": DET, "formation": {"value": -1.80, "bound": "AT_MOST", "limit": -1.50},
              "existing_ground": fac(0.0),
              "existing_ground_at": {"A": {"corners": [fac(0.0), fac(0.0), fac(-0.10), fac(-0.10)]},
                                     "B": fac(-0.20),
                                     "C": {"corners": [fac(0.0), fac(0.0), None, fac(0.0)]}},
              "working_space_m": fac(0.30), "neck": {"A": fac(0.30)}}
    return fts, beams, levels


def pit(led, i):
    return next(p for p in led["pits"] if p["id"] == i)


def test_normal_hand_calculation():
    led = X.ledger(*villa())
    a = pit(led, "A")
    assert a["neat_plan_m2"] == pytest.approx(3.74) and a["working_space_plan_m2"] == pytest.approx(6.44)
    assert a["depth_m"] == pytest.approx(1.75) and a["excavation_m3"] == pytest.approx(11.27)
    assert a["above_formation_m"] == {"blinding_top": 0.10, "footing_bottom": 0.17, "footing_top": 0.57}
    assert a["absolute_m"] == {"blinding_top": -1.70, "footing_bottom": -1.63, "footing_top": -1.23}
    assert a["buried"] == {"blinding_m3": 0.374, "underlay_m3": 0.21, "footing_m3": 1.2, "neck_m3": 0.3}
    assert a["backfill_m3"] == pytest.approx(9.066) and a["backfill_status"] == X.DRAWING_CONFIRMED
    b = pit(led, "B")
    assert b["excavation_m3"] == pytest.approx(6.40)
    assert b["backfill_m3"] is None and "NECK_VOLUME_HELD" in b["backfill_why"]
    g = led["trenches"][0]
    assert g["neat_plan_m2"] == pytest.approx(1.5) and g["depth_m"] == pytest.approx(0.70)
    assert g["excavation_m3"] == pytest.approx(1.05)


def test_sloping_ground_missing_corner_is_held_never_zero():
    led = X.ledger(*villa())
    c = pit(led, "C")
    assert c["excavation_m3"] is None and c["excavation_status"] == X.HELD
    assert "EXISTING_GROUND_CORNER_MISSING" in c["excavation_why"]
    assert c["neat_plan_m2"] == pytest.approx(2.6 * 1.2)        # the plan stays DRAWING-CONFIRMED
    t = led["totals"]["excavation_m3"]
    assert t["DRAWING-CONFIRMED"] == pytest.approx(11.27 + 6.40 + 1.05) and t["HELD_lines"] == 1


def test_turned_footing_uses_drawn_outline_for_position_schedule_for_size():
    led = X.ledger(*villa())
    ov = {(o["a"], o["b"]): o for o in led["overlaps"]}
    assert ov[("A", "C")]["neat_overlap_m2"] == pytest.approx(0.22)
    assert ov[("A", "C")]["footing_overlap_m2"] == 0.0
    assert ov[("A", "B")]["w_star_m"] == pytest.approx(0.40)


def test_mirror_keeps_overlaps_and_plans():
    fts, beams, levels = villa()
    m = copy.deepcopy(fts)
    for f in m:
        f["x0_m"] = -(f["x0_m"] + f["dx_m"])
    a, b = X.ledger(fts, beams, levels), X.ledger(m, beams, levels)
    key = lambda L: sorted((o["a"], o["b"], o["neat_overlap_m2"], o["w_star_m"]) for o in L["overlaps"])  # noqa: E731
    assert key(a) == key(b)
    assert [p["excavation_m3"] for p in a["pits"]] == [p["excavation_m3"] for p in b["pits"]]


def test_formation_only_a_bound_holds_every_volume():
    fts, beams, levels = villa()
    levels["formation"] = {"value": None, "bound": "AT_MOST", "limit": -1.50}
    led = X.ledger(fts, beams, levels)
    for p in led["pits"]:
        assert p["excavation_m3"] is None and "FORMATION_ONLY_A_BOUND" in p["excavation_why"]
        assert p["absolute_m"]["footing_top"] is None           # relative chain kept, absolute HELD
        assert p["above_formation_m"]["footing_bottom"] == pytest.approx(0.17)
    assert led["totals"]["excavation_m3"]["DRAWING-CONFIRMED"] == pytest.approx(1.05)   # only the beam (own top)


def test_formation_above_the_printed_limit_is_refused():
    fts, beams, levels = villa()
    levels["formation"] = {"value": -1.40, "bound": "AT_MOST", "limit": -1.50}
    with pytest.raises(X.LedgerError, match="FORMATION_ABOVE_PRINTED_LIMIT"):
        X.ledger(fts, beams, levels)


def test_working_space_not_stated_holds_volume_but_not_the_neat_plan():
    fts, beams, levels = villa()
    levels["working_space_m"] = None
    a = pit(X.ledger(fts, beams, levels), "A")
    assert a["excavation_m3"] is None and "WORKING_SPACE_M_NOT_PRINTED" in a["excavation_why"]
    assert a["neat_plan_m2"] == pytest.approx(3.74) and a["m3_per_m_depth_neat"] == pytest.approx(3.74)


def test_unprinted_underlay_and_projection_hold_by_name():
    fts, beams, levels = villa()
    levels["details"]["Q"] = {"blinding_m": 0.10, "underlay_m": None, "projection_m": None}
    fts[1]["detail"] = "Q"
    b = pit(X.ledger(fts, beams, levels), "B")
    assert b["neat_plan_m2"] is None and b["neat_status"] == X.HELD
    assert "UNDERLAY_NOT_PRINTED" in b["held"] and "BLINDING_PROJECTION_NOT_PRINTED" in b["held"]
    assert b["above_formation_m"]["footing_top"] is None


def test_units_must_be_declared():
    assert X.to_m(250, "cm") == pytest.approx(2.5) and X.to_m(2500, "mm") == pytest.approx(2.5)
    with pytest.raises(X.LedgerError, match="UNIT_NOT_DECLARED"):
        X.to_m(2.5, "ft")


def test_conflicting_footing_is_held_and_left_out_of_overlaps():
    fts, beams, levels = villa()
    fts[2]["conflict"] = "two tags on one outline"
    led = X.ledger(fts, beams, levels)
    c = pit(led, "C")
    assert c["neat_plan_m2"] is None and c["excavation_m3"] is None
    assert all("C" not in (o["a"], o["b"]) for o in led["overlaps"])


def test_formation_at_or_above_existing_ground_is_refused():
    fts, beams, levels = villa()
    levels["formation"] = {"value": 0.10}
    with pytest.raises(X.LedgerError, match="FORMATION_NOT_BELOW_EXISTING_GROUND"):
        X.ledger(fts, beams, levels)


def test_beam_without_printed_top_is_held():
    fts, beams, levels = villa()
    beams[0]["top"] = None
    g = X.ledger(fts, beams, levels)["trenches"][0]
    assert g["excavation_m3"] is None and "GB_TOP_NOT_PRINTED" in g["excavation_why"]
    assert g["neat_plan_m2"] == pytest.approx(1.5)
