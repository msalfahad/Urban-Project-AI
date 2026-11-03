"""T-481 skirting remainder rules R-T481-1 .. 3.

Hand villa K481 (not Alsenan). Bedroom 4.00 x 3.50 m, FFL +0.45, one door 0.90 (D-K1), three windows:
  K-W1 1.20 wide, section prints its base +1.35 -> 0.90 above the floor -> SKIRTED (wall below)
  K-W2 2.00 wide, base on the +0.45 floor line (frame rail 0.05 above it) -> NOT_SKIRTED (floor glazing)
  K-W3 1.00 wide, no view prints its base -> HELD (edge whole in the range, never 0)
By hand: gross 2 x (4.00 + 3.50) = 15.00; door 0.90 -> 14.10. Engine before: all three edges held, net 14.10 - 4.20 =
9.90, range 0 .. 4.20. After: net 9.90 + 1.20 = 11.10, closing on 15.00 - door 0.90 - K-W2 2.00 - K-W3 1.00 = 11.10;
range 0 .. 1.00 (K-W3 only).
Cell K-DR 1.50 x 2.00 with a 0.70 door and a 0.90 arch, a wardrobe box on one long side: 7.00 - 1.60 = 5.40 lm.
Shaft face 5.00 m: flight F-K1 (+0.45 -> +3.45) from s 0.00 to 3.60 (its first nosing at 3.60), floor zone 3.60 ..
5.00 -> STAIR 3.60, ROOM 1.40.
"""
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RES = ROOT / "research" / "agents_t481"
sys.path.insert(0, str(RES))
import t481_skirting_rules as R  # noqa: E402


# ------------------------------------------------------------------ R-T481-1 normal
def test_k481_three_windows_by_hand():
    s1 = R.sill_above_ffl(1.35, 0.45, "section K-K marker +0.45")
    s2 = R.sill_above_ffl(0.45, 0.45, "section K-K marker +0.45")
    assert s1 == pytest.approx(0.90) and s2 == 0.0
    assert R.decide([("K-K", s1)])["decision"] == R.SKIRTED
    assert R.decide([("K-K", s2)])["decision"] == R.NOT_SKIRTED
    assert R.decide([("plan", None)])["decision"] == R.HELD
    net, hi = 9.90, 4.20
    a = R.line_effect(R.SKIRTED, net, hi, 1.20, gross=15.00, listed_doors=0.90 + 2.00 + 1.00)
    assert a == {"net": pytest.approx(11.10), "range_hi": pytest.approx(3.00)}
    b = R.line_effect(R.NOT_SKIRTED, a["net"], a["range_hi"], 2.00)
    assert b == {"net": pytest.approx(11.10), "range_hi": pytest.approx(1.00)}
    c = R.line_effect(R.HELD, b["net"], b["range_hi"], 1.00)
    assert c == {"net": pytest.approx(11.10), "range_hi": pytest.approx(1.00)}  # held: whole edge stays, never 0


def test_frame_rail_is_not_a_sill():
    # the masonry opening base decides; a 0.05 bottom rail above the floor is a frame member
    assert R.window_base(R.sill_above_ffl(0.45, 0.45, "m")) == R.NOT_SKIRTED
    assert R.window_base(0.02) == R.NOT_SKIRTED          # at the tolerance: floor glazing
    assert R.window_base(0.021) == R.SKIRTED


def test_views_agreeing_on_decision_with_spread():
    d = R.decide([("section", 0.70), ("elevation ground a", 0.55), ("elevation ground b", 0.70)])
    assert d["decision"] == R.SKIRTED and d["spread_m"] == pytest.approx(0.15)


# ------------------------------------------------------------------ R-T481-1 adverse
def test_views_split_decision_is_held():
    assert R.decide([("a", 0.0), ("b", 0.60)])["decision"] == R.HELD


def test_no_datum_refused():
    with pytest.raises(R.RuleError):
        R.sill_above_ffl(1.35, 0.45, "")


def test_missing_floor_level_refused():
    with pytest.raises(R.RuleError):
        R.sill_above_ffl(1.35, None, "marker")


def test_millimetres_refused():
    with pytest.raises(R.RuleError):
        R.sill_above_ffl(1350, 450, "marker")
    with pytest.raises(R.RuleError):
        R.window_base(900)


def test_base_below_floor_refused():
    with pytest.raises(R.RuleError):
        R.sill_above_ffl(0.30, 0.45, "marker")


def test_release_must_close_on_gross():
    with pytest.raises(R.RuleError):
        R.line_effect(R.SKIRTED, 9.90, 4.20, 1.20, gross=15.00, listed_doors=0.90)


def test_edge_larger_than_range_refused():
    with pytest.raises(R.RuleError):
        R.line_effect(R.NOT_SKIRTED, 9.90, 1.00, 2.00)


def test_release_without_net_refused():
    with pytest.raises(R.RuleError):
        R.line_effect(R.SKIRTED, None, 4.20, 1.20)


# ------------------------------------------------------------------ R-T481-2
def cell(mirror=False):
    sides = [
        {"id": "A", "length": 2.00, "stretches": [{"kind": "WALL", "length": 0.60, "ref": "a1"},
                                                   {"kind": "DOOR", "length": 0.70, "ref": "D-K2"},
                                                   {"kind": "WALL", "length": 0.70, "ref": "a2"}]},
        {"id": "B", "length": 2.00, "stretches": [{"kind": "WALL", "length": 2.00, "ref": "b"}]},
        {"id": "C", "length": 1.50, "stretches": [{"kind": "WALL", "length": 1.50, "ref": "c"}]},
        {"id": "D", "length": 1.50, "stretches": [{"kind": "WALL", "length": 0.30, "ref": "d1"},
                                                   {"kind": "PASSAGE", "length": 0.90, "ref": "A-K1"},
                                                   {"kind": "WALL", "length": 0.30, "ref": "d2"}]},
    ]
    if mirror:
        sides = [dict(s, stretches=list(reversed(s["stretches"]))) for s in reversed(sides)]
    return sides


@pytest.mark.parametrize("mirror", [False, True])
def test_cell_walk_by_hand(mirror):
    w = R.walk_cell(cell(mirror), joinery=[{"length": 2.00}, {"length": 0.50}])
    assert w["skirting_lm"] == pytest.approx(5.40) and w["gross_lm"] == pytest.approx(7.00)
    assert w["deductions"] == {"D-K2": 0.70, "A-K1": 0.90}
    assert w["joinery_backed_lm"] == pytest.approx(2.50)   # reported, never deducted


def test_cell_side_not_closing_refused():
    s = cell()
    s[0]["stretches"][0]["length"] = 0.50
    with pytest.raises(R.RuleError):
        R.walk_cell(s)


def test_joinery_as_boundary_refused():
    s = cell()
    s[1]["stretches"] = [{"kind": "JOINERY", "length": 2.00}]
    with pytest.raises(R.RuleError):
        R.walk_cell(s)


def test_opening_deducted_twice_refused():
    s = cell()
    s[3]["stretches"][1]["ref"] = "D-K2"
    with pytest.raises(R.RuleError):
        R.walk_cell(s)


# ------------------------------------------------------------------ R-T481-3
def face(**kw):
    f = {"id": "K-shaft", "length": 5.00, "walls": [(0.0, 5.00, "k")], "windows": [],
         "floor_zone": [(3.60, 5.00)], "flights": [(0.0, 3.60, "F-K1", (0.45, 3.45))]}
    f.update(kw)
    return f


def test_shaft_face_by_hand():
    r = R.shaft_owners(face(), 0.45)
    assert r["lm"] == {"ROOM": pytest.approx(1.40), "STAIR": pytest.approx(3.60), "UNKNOWN": 0.0}


def test_stacked_flight_other_level_no_conflict_counted_once():
    f = face(flights=[(0.0, 3.60, "F-K1", (0.45, 3.45)), (0.0, 1.20, "LD-K2", (6.45, 6.45))])
    r = R.shaft_owners(f, 0.45)
    assert r["lm"]["STAIR"] == pytest.approx(3.60) and r["lm"]["ROOM"] == pytest.approx(1.40)


def test_two_owners_same_level_refused():
    with pytest.raises(R.RuleError):
        R.shaft_owners(face(flights=[(0.0, 3.80, "F-K1", (0.45, 3.45))]), 0.45)


def test_uncovered_wall_is_unknown_never_assigned():
    r = R.shaft_owners(face(flights=[(0.0, 3.00, "F-K1", (0.45, 3.45))]), 0.45)
    assert r["lm"]["UNKNOWN"] == pytest.approx(0.60)


def test_window_not_counted_as_wall():
    r = R.shaft_owners(face(walls=[(0.0, 1.0, "k1"), (2.0, 5.0, "k2")], windows=[(1.0, 2.0, "K-W9")]), 0.45)
    assert r["lm"]["STAIR"] == pytest.approx(2.60)


# ------------------------------------------------------------------ development villa ledger
def test_alsenan_ledger_reproduces():
    out = subprocess.run([sys.executable, "-I", str(RES / "t481_alsenan.py"), "--check"], capture_output=True,
                         text=True)
    assert out.returncode == 0, out.stdout + out.stderr


def test_alsenan_figures():
    sys.path.insert(0, str(RES))
    import t481_alsenan as A
    _, lines, _, s = A.build()
    t = s["totals"]
    assert t["certain_after"] == pytest.approx(189.818752 + 3.909839 + 5.100)
    assert t["held_high_after"] == 0.0
    assert s["dressing"]["skirting_lm"] == pytest.approx(5.100)
    assert s["shaft"]["stair_owned_lm"] == pytest.approx(9.050)
    assert abs(s["shaft"]["walk_closure_residual_lm"]) < 0.01
    dew = [r for r in lines if r["line"].startswith("L-d3241491")][0]
    assert dew["net_after"] == pytest.approx(18.127876)
