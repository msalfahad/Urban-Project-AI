"""Phase 2B-8 acceptance: the door-standard reconciliation of ARCH_TAKEOFF_V2.7.1 (UP-DOOR-OPEN-003, owner decision
D-16 / OQ-05 unresolved). Every door keeps apart: the as-drawn wall opening (the band gap jamb to jamb), the measured
jamb span (the door symbol's own jamb lines), the door leaf, the finished clear width (not in a plan), the owner
minimum (ordinary 1.00 m, bathroom 0.90 m), a frame allowance only when evidenced (never the registry's 0.10 m by
default), the proposed enlargement and whether consultant / structural review is required. The CAD geometry the BOQ
measures is never changed to satisfy the minimum; the enlargement is a proposal, never applied.

Plans: p2b8_fixtures.bath_corridor_door (DOOR_TRUTH: the reference plan's pattern, a bathroom door 0.80 m in a 1.027 m
wall gap opening into an internal corridor) and the p2b6 PLAIN / DOUBLE plans (external doors)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))

ezdxf = pytest.importorskip("ezdxf")

import p2b8_fixtures as F                                     # noqa: E402
import p2b8_run as R                                          # noqa: E402

T = F.DOOR_TRUTH
TOL = 1e-6


@pytest.fixture(scope="module")
def work(tmp_path_factory):
    return tmp_path_factory.mktemp("p2b8_doors")


_cache = {}


def _out(work, plan, method=R.V271):
    if (plan, method) not in _cache:
        src = F.bath_corridor_door(work / "BATH_CORRIDOR.dxf") if plan == "BATH_CORRIDOR" else \
            F.wide_door_plan(work / "WIDE.dxf") if plan == "WIDE" else F.door_plan(work / f"{plan}.dxf", plan)
        _cache[(plan, method)] = R.run(src, work / f"o_{plan}_{method[-5:].replace('.', '')}", roles=F.ROLES,
                                       facts=True, method=method)
    return _cache[(plan, method)]


def _door(out):
    rows = [d for d in R.door_reconciliation(out) if d["category"] not in ("ELEVATOR",)]
    assert len(rows) == 1, rows
    return rows[0]


def test_bathroom_door_every_value_kept_apart(work):
    """the bathroom door of the 1.027 m gap: as drawn 1.027, jamb span 0.80, leaf 0.70, finished clear width not
    established, owner minimum 0.90 (bathroom), no allowance evidenced; the CAD symbol's 0.10 m between opening and
    leaf is reported as drawing geometry, not as an allowance."""
    d = _door(_out(work, "BATH_CORRIDOR"))
    assert d["category"] == T["category"]
    assert abs(d["as_drawn_wall_opening_m"] - T["as_drawn_wall_opening_m"]) < 1e-4
    assert abs(d["measured_jamb_span_m"] - T["jamb_span_m"]) < 1e-4
    assert d["jamb_basis"] == "NARROWED_TO_JAMB_SPAN"
    assert [round(x, 4) for x in d["door_leaf_m"]] == [T["leaf_m"]]
    assert d["finished_clear_width_m"] is None and d["finished_clear_width_state"].startswith("NOT_ESTABLISHED")
    assert d["owner_minimum_m"] == T["owner_minimum_m"]
    assert d["owner_minimum_reference"].startswith("UNRESOLVED")
    alw = d["frame_allowance"]
    assert alw["value_m"] is None and alw["state"] == "NOT_ESTABLISHED"
    assert abs(alw["drawn_symbol_difference_m"] - T["symbol_difference_m"]) < 1e-4
    assert "not an accepted allowance source" in alw["drawn_symbol_difference_note"]


def test_bathroom_door_proposed_enlargement_and_review(work):
    """structural reading: 0.90 - 0.80 = 0.10 m; leaf reading: the leaf is 0.20 m short, the opening grows 0.10 m (no
    allowance) to 0.20 m (with the registry's unconfirmed 0.10 m); both fit inside the 1.027 m wall gap, cutting into
    its 0.227 m remainder of wall (0.127 / 0.027 m left) - consultant and structural review are required (the drawn
    wall is cut, the lintel span grows). The status: below the minimum on every reading; nothing applied."""
    d = _door(_out(work, "BATH_CORRIDOR"))
    pe = d["proposed_enlargement"]
    assert abs(pe["STRUCTURAL_OPENING"]["m"] - T["structural_shortfall_m"]) < 1e-4
    assert abs(pe["STRUCTURAL_OPENING"]["required_opening_m"] - T["owner_minimum_m"]) < 1e-4
    assert abs(pe["DOOR_LEAF"]["leaf_shortfall_m"] - T["leaf_shortfall_m"]) < 1e-4
    assert abs(pe["DOOR_LEAF"]["low_m"] - T["structural_shortfall_m"]) < 1e-4
    assert abs(pe["DOOR_LEAF"]["high_m_with_unconfirmed_allowance"] - 0.20) < 1e-4
    assert pe["CLEAR_PASSAGE"]["state"] == "NOT_ESTABLISHED"
    assert abs(d["wall_remainder_m"] - T["remainder_m"]) < 1e-4
    assert d["within_as_drawn_gap"] == {"low": True, "high": True}
    assert abs(d["remainder_after_m"]["low"] - T["remainder_after_m"]) < 1e-4
    assert abs(d["remainder_after_m"]["high"] - 0.027) < 1e-4
    assert d["review"]["consultant"] == "REQUIRED" and d["review"]["structural"] == "REQUIRED"
    assert {"WALL_REMAINDER_CUT", "LINTEL_SPAN_INCREASE"} <= set(d["review"]["reasons"])
    assert d["status"] == "BELOW_MINIMUM_ON_EVERY_READING" and d["applied_to_boq"] is False


def test_the_cad_geometry_is_never_changed_to_meet_the_minimum(work):
    """the BOQ measures the 0.80 m door: the bathroom plaster deducts 0.80 x 2.10 = 1.68 m2 (9.354 x 3.00 - 1.68 =
    26.382 m2), the door set line carries 0.80 m; the BOQ of V2.7.1 equals V2.7's on this plan (no review space)."""
    out = _out(work, "BATH_CORRIDOR")
    d = _door(out)
    assert abs(d["boq_width_m"] - T["jamb_span_m"]) < 1e-4
    pl = [ln for ln in R.lines(out) if ln["item_code"] == "FIN.PLASTER" and
          (ln.get("location") or {}).get("room_name_en", "").startswith("Bathroom")]
    assert len(pl) == 1 and abs(pl[0]["measured_net"] - (2 * (1.677 + 3.0) * 3.0 - 0.80 * 2.10)) < 1e-4
    ded = [x for x in pl[0]["deductions"] if x["what"].startswith("door")]
    assert len(ded) == 1 and abs(ded[0]["width_m"] - 0.80) < 1e-6
    assert not R.diff(_out(work, "BATH_CORRIDOR", R.V27), out)


def test_a_door_whose_gap_is_the_door_needs_a_cut_beyond_the_drawn_opening(work):
    """PLAIN: an external door in a 0.80 m gap (min 1.00 m): as drawn = jamb span = 0.80; the enlargement 0.20 m
    (0.30 m with the unconfirmed allowance) lies outside the drawn opening - the wall is cut beyond it."""
    d = _door(_out(work, "PLAIN"))
    assert d["category"] == "EXTERNAL_ALUMINIUM" and d["owner_minimum_m"] == 1.0
    assert abs(d["as_drawn_wall_opening_m"] - 0.80) < 1e-4 and abs(d["measured_jamb_span_m"] - 0.80) < 1e-4
    assert d["jamb_basis"] == "GAP_IS_THE_DOOR"
    assert abs(d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"] - 0.20) < 1e-4
    assert d["within_as_drawn_gap"] == {"low": False, "high": False}
    assert d["review"]["structural"] == "REQUIRED" and "WALL_CUT_BEYOND_DRAWN_OPENING" in d["review"]["reasons"]


def test_a_compliant_door_needs_no_review(work):
    """WIDE: an external door of 1.10 m with a 1.00 m leaf (min 1.00): compliant on the structural and the leaf reading
    (1.00 + the unconfirmed 0.10 m allowance - 1.10 = 0); no enlargement, no review."""
    d = _door(_out(work, "WIDE"))
    assert d["category"] == "EXTERNAL_ALUMINIUM"
    assert abs(d["measured_jamb_span_m"] - 1.10) < 1e-4 and [round(x, 4) for x in d["door_leaf_m"]] == [1.0]
    assert d["status"] == "COMPLIES_ON_EVERY_READING"
    assert d["proposed_enlargement"]["STRUCTURAL_OPENING"]["m"] == 0
    assert d["proposed_enlargement"]["DOOR_LEAF"]["high_m_with_unconfirmed_allowance"] == 0
    assert {k: d["review"][k] for k in ("consultant", "structural", "reasons")} == \
        {"consultant": "NOT_REQUIRED", "structural": "NOT_REQUIRED", "reasons": []}


def test_a_main_entrance_has_no_ordinary_minimum(work):
    """DOUBLE: the 1.60 m pair of 0.75 m leaves is the main entrance (UP-DOOR-CLS-004: drawing and specification):
    no ordinary minimum, as drawn only, no review; its leaves are still kept (0.75 + 0.75)."""
    d = _door(_out(work, "DOUBLE"))
    assert d["category"].startswith("MAIN_ENTRANCE")
    assert abs(d["measured_jamb_span_m"] - 1.60) < 1e-4
    assert sorted(round(x, 4) for x in d["door_leaf_m"]) == [0.75, 0.75]
    assert d["owner_minimum_m"] is None and d["status"] == "AS_DRAWN_ONLY"
    assert d["review"]["consultant"] == "NOT_REQUIRED" and d["review"]["structural"] == "NOT_REQUIRED"


def test_owner_minimum_is_a_conditional_scenario_never_in_the_main_boq(work):
    """the owner-minimum enlargement is reported as a CONDITIONAL scenario set (it depends on D-16 / OQ-05 and on an
    approved modification); no BOQ line carries an enlarged width."""
    out = _out(work, "BATH_CORRIDOR")
    rep = R.release_report(out)
    sets = {s["set_id"]: s for s in rep["categories"]["CONDITIONAL"]["scenario_sets"]}
    door_sets = [s for k, s in sets.items() if k.startswith("DOOR_OWNER_MINIMUM")]
    assert len(door_sets) == 1 and door_sets[0]["depends_on"] == ["D-16"]
    assert door_sets[0]["mutually_exclusive"] is True
    for ln in R.lines(out):
        w = ((ln.get("calculation") or {}).get("inputs") or {}).get("width_m")
        if ln["item_code"].startswith("DOOR.") and w is not None:
            assert abs(w - 0.80) < 1e-4
