"""T-333 R-T333-1 on a hand-calculated villa M (not Alsenan): rebinding a wall ledger to a new candidate's line ids,
placing parapet / plinth components once; normal and adverse cases.

Villa M, ground storey, panel height 3.000 m under the slab (hand):
  M-W1 0.20 WHITE 5.000 x 3.000 = 15.000 - door 1.000 x 2.100 = 12.900 m2 VERIFIED (Checker run 'C-9'); 2.580 m3
  M-W2 0.20 BLACK beam over it not printed -> HELD 'beam depth (RFI-3)', blank
  M-W3 0.20 BLACK 2.000 m under a sunken panel: 2.000 x 3.000 = 6.000 - 2.000 x d m2; 1.200 - 0.400 x d m3
  M-W4 0.15 BLACK 3.000 x 3.000 = 9.000 m2 DRAWING-CONFIRMED; 1.350 m3
Candidate a (old ids L-A*), candidate b (new ids L-B*), every masonry line BLOCKED (no quantity).
Parapet run P-1: 10.000 m x 0.500 m above a 0.30 RC upstand, t 0.20 -> block 0 .. 5.000 m2 (0 .. 1.000 m3), material
HELD; plinth course 10.000 m x 0.050 m = 0.500 m2 inside the GF 0.20 wall height.
GF 0.20 MAS.BLOCK after: '12.9000 determinate + (6.0000 - 2.0000 x d) drop walls + HELD [1 walls / pieces, blank] m2'.
"""
from __future__ import annotations

import copy
import random
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t333"))
sys.path.insert(0, str(ROOT / "research" / "agents_t291"))
import binding_fill as F        # noqa: E402
import wall_line_ledger as R    # noqa: E402

MB, VOL = "MAS.BLOCK", "ARCH.WALL_VOLUME"


def ln(lid, item, floor, fam, unit, q=None, st="BLOCKED_RFI"):
    return {"line_id": lid, "item_code": item, "floor": floor, "family": fam, "unit": unit, "measured_net": q,
            "evidence_state": st}


OLD = [ln("L-A15", MB, "GF", "0.15", "m2"), ln("L-A20", MB, "GF", "0.2", "m2"), ln("L-AV20", VOL, "GF", "0.2", "m3"),
       ln("L-AV15", VOL, "GF", "0.15", "m3")]
NEW = [ln("L-B15", MB, "GF", "0.15", "m2"), ln("L-B20", MB, "GF", "0.2", "m2"), ln("L-BV20", VOL, "GF", "0.2", "m3"),
       ln("L-BV15", VOL, "GF", "0.15", "m3"), ln("L-B1F20", MB, "1F", "0.2", "m2")]
T = {"M-W1": 0.2, "M-W2": 0.2, "M-W3": 0.2, "M-W4": 0.15}


def row(lid, item, unit, wid, st, carried=None, upper=None, coef=None, held=None, vb=None):
    return {"line_id": lid, "item_code": item, "unit": unit, "wall_id": wid, "share": 1.0, "status": st,
            "carried": carried, "upper": upper, "drop_coefficient": coef, "held_item": held, "verified_by": vb}


def rows(lines=("L-B20", "L-B15", "L-BV20", "L-BV15")):
    a20, a15, v20, v15 = lines
    return [
        row(a20, MB, "m2", "M-W1", "VERIFIED", carried=5.0 * 3.0 - 1.0 * 2.1, vb="C-9"),
        row(a20, MB, "m2", "M-W2", "HELD", held="beam depth (RFI-3)"),
        row(a20, MB, "m2", "M-W3", "HELD ON DROP", upper=2.0 * 3.0, coef=2.0, held="drop d (RFI-4)"),
        row(a15, MB, "m2", "M-W4", "DRAWING-CONFIRMED", carried=9.0),
        row(v20, VOL, "m3", "M-W1", "VERIFIED", carried=round(12.9 * 0.2, 6), vb="C-9"),
        row(v20, VOL, "m3", "M-W2", "HELD", held="beam depth (RFI-3)"),
        row(v20, VOL, "m3", "M-W3", "HELD ON DROP", upper=1.2, coef=0.4, held="drop d (RFI-4)"),
        row(v15, VOL, "m3", "M-W4", "DRAWING-CONFIRMED", carried=1.35),
    ]


def components(**over):
    c = [{"component_id": "PARAPET-BLOCK P-1", "run_or_zone": "P-1", "kind": "ALTERNATIVE_BLOCK", "line_id": None,
          "low": 0.0, "high": 10.0 * 0.5, "material_status": "HELD (designer)", "added": False},
         {"component_id": "PARAPET-RC P-1", "run_or_zone": "P-1", "kind": "ALTERNATIVE_RC", "line_id": None,
          "low": 10.0 * 0.3 * 0.2, "high": 10.0 * 0.8 * 0.2, "above_upstand_carried": False, "added": False},
         {"component_id": "PLINTH-COURSE S-1", "run_or_zone": "S-1", "kind": "CONTAINED", "line_id": "L-B20",
          "low": 10.0 * 0.05, "high": 10.0 * 0.05, "added": False}]
    for k, v in over.items():
        cid, fld = k.split("__")
        next(x for x in c if x["component_id"].startswith(cid.replace("_", "-")))[fld] = v
    return c


# ---- normal ----------------------------------------------------------------------------------------------------
def test_rebind_maps_each_old_line_to_the_new_id_and_lists_the_new_line():
    m, unbound, act = F.rebind(OLD, NEW)
    assert {k: v["line_id"] for k, v in m.items()} == {"L-A15": "L-B15", "L-A20": "L-B20", "L-AV20": "L-BV20",
                                                        "L-AV15": "L-BV15"}
    assert unbound == ["L-B1F20"]                              # listed, never filled by guess
    assert set(act.values()) == {"REPLACE_BLANK"}


def test_hand_totals_of_the_gf_020_line():
    rs = rows()
    assert F.check_rows(rs, T)
    t = F.line_totals([r for r in rs if r["line_id"] == "L-B20"], "m2")
    assert t["determinate"] == pytest.approx(12.9) and t["verified"] == pytest.approx(12.9)
    assert t["drop_upper_at_d0"] == pytest.approx(6.0) and t["drop_coefficient"] == pytest.approx(2.0)
    assert t["held"] == ["M-W2"]
    assert t["expression"] == "12.9000 determinate + (6.0000 - 2.0000 x d) drop walls + HELD [1 walls / pieces, blank] m2"
    v = F.line_totals([r for r in rs if r["line_id"] == "L-BV20"], "m3")
    assert v["determinate"] == pytest.approx(2.58) and v["drop_coefficient"] == pytest.approx(0.4)


def test_a_line_that_now_has_a_figure_is_corrected_not_replaced():
    new = copy.deepcopy(NEW)
    new[1]["measured_net"], new[1]["evidence_state"] = 30.0, "PROVISIONAL"
    _, _, act = F.rebind(OLD, new)
    assert act["L-B20"] == "CORRECT_FIGURE" and act["L-B15"] == "REPLACE_BLANK"


def test_components_placed_once():
    assert F.check_components(components())


def test_order_and_mirror_invariant_totals():
    rs = rows()
    sh = rs[:]
    random.Random(7).shuffle(sh)
    a = F.line_totals([r for r in rs if r["line_id"] == "L-B20"], "m2")
    b = F.line_totals([r for r in sh if r["line_id"] == "L-B20"], "m2")
    assert a == b                          # a mirrored plan gives the same walls and lengths: the fill is the same


# ---- adverse -----------------------------------------------------------------------------------------------------
def test_wall_under_two_ids_refused():
    rs = rows()
    rs.append(row("L-B15", MB, "m2", "M-W1", "VERIFIED", carried=12.9, vb="C-9"))
    with pytest.raises(F.FillError, match="^WALL_TWO_IDS"):
        F.check_rows(rs, T)


def test_one_id_twice_refused():
    rs = rows()
    rs.append(dict(rs[0]))
    with pytest.raises(F.FillError, match="^WALL_TWO_IDS"):
        F.check_rows(rs, T)


def test_held_wall_as_zero_refused():
    rs = rows()
    rs[1]["carried"] = 0.0
    with pytest.raises(F.FillError, match="^HELD_AS_ZERO"):
        F.check_rows(rs, T)


def test_held_wall_without_item_refused():
    rs = rows()
    rs[1]["held_item"] = None
    with pytest.raises(F.FillError, match="^HELD_AS_ZERO"):
        F.check_rows(rs, T)


def test_drop_term_evaluated_refused():
    rs = rows()
    rs[2]["carried"] = 6.0
    with pytest.raises(F.FillError, match="^DROP_EVALUATED"):
        F.check_rows(rs, T)


def test_volume_not_area_times_thickness_refused():
    rs = rows()
    rs[4]["carried"] = 12.9 * 0.15                # booked at the wrong thickness
    with pytest.raises(F.FillError, match="^VOLUME_MISMATCH"):
        F.check_rows(rs, T)


def test_parapet_run_as_block_and_rc_refused():
    with pytest.raises(F.FillError, match="^PARAPET_BOTH"):
        F.check_components(components(PARAPET_BLOCK__line_id=None, PARAPET_BLOCK__material_status="",
                                      PARAPET_BLOCK__added=True, PARAPET_RC__above_upstand_carried=True))


def test_held_parapet_block_bound_to_a_wall_line_refused():
    with pytest.raises(F.FillError, match="^PARAPET_BOTH"):
        F.check_components(components(PARAPET_BLOCK__line_id="L-B20"))


def test_held_parapet_block_as_zero_refused():
    with pytest.raises(F.FillError, match="^HELD_AS_ZERO"):
        F.check_components(components(PARAPET_BLOCK__high=0.0))


def test_plinth_course_added_again_refused():
    with pytest.raises(F.FillError, match="^CONTAINED_ADDED"):
        F.check_components(components(PLINTH_COURSE__added=True))


def test_lost_and_ambiguous_lines_and_unknown_state_refused():
    with pytest.raises(F.FillError, match="^LINE_LOST"):
        F.rebind(OLD, [x for x in NEW if x["line_id"] != "L-B20"])
    with pytest.raises(F.FillError, match="^KEY_AMBIGUOUS"):
        F.rebind(OLD, NEW + [ln("L-B20b", MB, "GF", "0.2", "m2")])
    bad = copy.deepcopy(NEW)
    bad[0]["evidence_state"] = "WHATEVER"
    with pytest.raises(F.FillError, match="^STATE_UNKNOWN"):
        F.rebind(OLD, bad)


def test_thickness_in_millimetres_refused():
    with pytest.raises(R.LedgerError, match="^BAD_UNITS"):
        R.family_key(150)


# --- rule 6 (r2, D-T333-1): a fallback-height deduction keeps the net ASSUMED — OWNER-APPROVED -----------------------
# Villa M, 1F, established part of M-P1 0.20: 4.000 x 3.000 = 12.000 m2 built; held piece 'beam B9 depth (RFI-7)'.
#   case W (normal): window W-1 printed 1.200 x 1.000 = 1.200 -> part 10.800 m2 stays DRAWING-CONFIRMED
#   case D (adverse): door D-1 0.900 wide, no printed height, Q-55 fallback 2.20 -> 0.900 x 2.200 = 1.980
#                     -> part 10.020 m2 ASSUMED — OWNER-APPROVED; labelling it DRAWING-CONFIRMED is refused
PART = "ESTABLISHED PART + HELD"


def part_row(carried, ps="DRAWING-CONFIRMED", wid="M-P1", st=PART):
    r = row("L-B1F20", MB, "m2", wid, st, carried=carried, held="beam B9 depth (RFI-7)")
    r["part_status"] = ps
    return r


def test_rule6_window_only_part_stays_drawing_confirmed():
    ded = {"M-P1": [{"opening_id": "W-1", "height_basis": "DRAWING-CONFIRMED"}]}
    out = F.apply_fallback_labels([part_row(4.0 * 3.0 - 1.2 * 1.0)], ded)
    assert out[0]["part_status"] == "DRAWING-CONFIRMED"
    assert out[0]["carried"] == pytest.approx(10.8, abs=1e-9)
    assert F.apply_fallback_labels([part_row(12.0)], {})[0]["part_status"] == "DRAWING-CONFIRMED"   # no opening


def test_rule6_q55_door_part_is_owner_approved_and_quantity_unchanged():
    ded = {"M-P1": [{"opening_id": "W-1", "height_basis": "DRAWING-CONFIRMED"},
                    {"opening_id": "D-1", "height_basis": F.OWNER_APPROVED}]}
    r = part_row(4.0 * 3.0 - 0.9 * 2.2)
    out = F.apply_fallback_labels([r], ded)
    assert out[0]["part_status"] == F.OWNER_APPROVED
    assert out[0]["carried"] == r["carried"] == pytest.approx(10.02, abs=1e-9)
    assert r["part_status"] == "DRAWING-CONFIRMED"           # input not mutated
    assert F.line_totals(out, "m2")["established_parts"] == F.line_totals([r], "m2")["established_parts"]


def test_rule6_adverse_q55_door_part_labelled_drawing_confirmed_refused():
    ded = {"M-P1": [{"opening_id": "D-1", "height_basis": F.OWNER_APPROVED}]}
    with pytest.raises(F.FillError, match="^FALLBACK_HIDDEN"):
        F.check_fallback_labels([part_row(10.02)], ded)
    with pytest.raises(F.FillError, match="^FALLBACK_HIDDEN"):
        F.check_fallback_labels([part_row(10.02, ps="VERIFIED")], ded)


def test_rule6_adverse_whole_wall_verified_over_a_q55_door_refused():
    ded = {"M-W1": [{"opening_id": "D-2", "height_basis": F.OWNER_APPROVED}]}
    r = row("L-B20", MB, "m2", "M-W1", "VERIFIED", carried=12.9, vb="C-9")
    with pytest.raises(F.FillError, match="^FALLBACK_HIDDEN"):
        F.apply_fallback_labels([r], ded)
    ok = dict(r, status=F.OWNER_APPROVED, part_status=None)
    assert F.apply_fallback_labels([ok], ded)[0]["status"] == F.OWNER_APPROVED


def test_rule6_adverse_deducted_opening_without_height_basis_refused():
    for bad in (None, "HELD", "UNKNOWN"):
        with pytest.raises(F.FillError, match="^STATE_UNKNOWN"):
            F.apply_fallback_labels([part_row(10.02)], {"M-P1": [{"opening_id": "D-1", "height_basis": bad}]})
