"""T-719: void register (R-T719-1 .. -5). Villa K719 is hand-made (not the development villa):
GF hall 8.00 x 5.00 under a 1F slab with a double-height void 4.00 x 3.00 (12.00 m2) in one corner of the 1F landing
room 8.00 x 5.00 (40.00 m2); a straight stair 1.00 wide with 10 goings of 0.30 (3.00 m2 of treads) rises from the GF
along the void's long side and arrives at 1F; on the 1F plan the flight is 'seen' inside the slab opening, so the
opening is the void 12.00 + the flight 3.00 = 15.00 m2; a corner landing 1.00 x 1.00 at mid-height sits in the opening
(1.00 m2). Hand: 1F floor finish = 40.00 - 15.00 - 1.00 = 24.00; GF ceiling at its own level = 40.00 - 16.00 = 24.00.
The last tests rebuild the development-villa register from committed files."""
from __future__ import annotations

import json
import math
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t719"))
import t719_rules as R  # noqa: E402

VOID = [(0, 0), (4, 0), (4, 3), (0, 3)]
FLIGHT = [(0, -1), (3, -1), (3, 0), (0, 0)]           # 10 goings x 0.30, 1.00 wide, along the void's south side
LANDING = [(3, -1), (4, -1), (4, 0), (3, 0)]
OPENING_FACE = X("16.00")                               # void + flight + landing, all inside the 1F room face


def _rot(pts, deg, mirror=False):
    a = math.radians(deg)
    out = []
    for x, y in pts:
        x = -x if mirror else x
        out.append((round(x * math.cos(a) - y * math.sin(a), 12), round(x * math.sin(a) + y * math.cos(a), 12)))
    return out


def test_normal_hand_figures():
    assert R.shoelace(VOID) == X("12") and R.shoelace(FLIGHT) == X("3") and R.shoelace(LANDING) == X("1")
    res, r = R.floor_check(OPENING_FACE, [("void", "12.00"), ("flight seen", "3.00"), ("corner landing", "1.00")])
    assert (res, r) == ("DEDUCTED_ONCE", X("0.000000"))
    assert X("40.00") - OPENING_FACE == X("24.00")                       # 1F floor finish by hand
    gres, gr = R.floor_check(OPENING_FACE, [("no ceiling", "12.00"), ("stair zone", "4.00")])
    assert gres == "DEDUCTED_ONCE" and X("40.00") - OPENING_FACE == X("24.00")


def test_adverse_deducted_twice_overlapping_footprints():
    # the flight read one 0.05 strip into the landing: two footprints summed where they overlap
    flight_long = [(0, -1), (3.05, -1), (3.05, 0), (0, 0)]
    assert R.shoelace(flight_long) == X("3.05")
    res, r = R.floor_check(OPENING_FACE, [("void", "12.00"), ("flight", "3.05"), ("landing", "1.00")])
    assert res == "DEDUCTED_TWICE" and r == X("-0.050000")
    ex, twice = R.overlap_excess(["3.05", "1.00"], "4.00")
    assert ex == X("0.050000") and twice


def test_adverse_not_deducted_landing_carried():
    res, r = R.floor_check(OPENING_FACE, [("void", "12.00"), ("flight", "3.00")])
    assert res == "NOT_DEDUCTED" and r == X("1.000000")       # the landing would still be floor finish


def test_within_tolerance_is_once():
    res, r = R.floor_check(OPENING_FACE, [("void", "12.00"), ("flight", "3.00"), ("landing", "0.996")])
    assert res == "DEDUCTED_ONCE" and r == X("0.004000")
    res, _ = R.floor_check(OPENING_FACE, [("void", "12.00"), ("flight", "3.00"), ("landing", "0.99")])
    assert res == "NOT_DEDUCTED"


def test_stair_well_is_a_void_of_the_upper_floor_only():
    up, below = R.placement({"pierces": "1F", "below": "GF", "kind": "STAIR_WELL"})
    assert (up, below) == ("1F", "GF")
    # on GF the same flight is stair finish, never a void: a GF floor check over the flight finds no void deduction
    res, r = R.floor_check(X("3.00"), [("stair treads (marble, counted on GF)", "3.00")])
    assert res == "DEDUCTED_ONCE"
    with pytest.raises(ValueError):
        R.placement({"below": "GF"})


@pytest.mark.parametrize("deg,mirror", [(0, False), (90, False), (30, False), (-73, True), (180, True)])
def test_mirror_rotation_units(deg, mirror):
    for poly, want in ((VOID, X("12")), (FLIGHT, X("3")), (LANDING, X("1"))):
        assert abs(R.shoelace(_rot(poly, deg, mirror)) - want) < X("1e-9")
    mm = [(x * 1000, y * 1000) for x, y in _rot(VOID, deg, mirror)]
    assert abs(R.shoelace(mm) / 1000000 - X("12")) < X("1e-9")      # millimetre drawing -> m2


def test_missing_outline_is_held_never_zero():
    row = R.register_row("V-X", "1F", "GF", None, "VOID word, no outline", [])
    assert row["status"] == "HELD" and row["result"] == "VOID_EXTENT_UNRESOLVED" and row["outline_m2"] is None
    assert R.floor_check(None, [])[0] == "VOID_EXTENT_UNRESOLVED"


def test_exterior_void_touches_no_internal_line():
    assert R.floor_check(0, []) == ("EXTERIOR", X("0.000000"))


def test_ceiling_top_once():
    assert R.ceiling_top_lines([("group", "51.0")]) == "DEDUCTED_ONCE"
    assert R.ceiling_top_lines([("group", "51.0"), ("over void", None)]) == "DOUBLE_COUNT_RISK"
    assert R.ceiling_top_lines([("group", "51.0"), ("over void", "16.0")]) == "DEDUCTED_TWICE"
    assert R.ceiling_top_lines([]) == "NOT_DEDUCTED"


# ---- development villa (committed files only) ----------------------------------------------------------------------
B = ROOT / "research" / "agents_t719"


def test_builder_reproduces_outputs():
    p = subprocess.run([sys.executable, "-I", str(B / "t719_alsenan.py"), "--check"], capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "identical: True" in p.stdout


def test_register_key_figures():
    doc = json.loads((B / "out" / "T719_VOIDS.json").read_text(encoding="utf-8"))
    reg = {r["void"]: r for r in doc["register"]}
    assert set(reg) == {"V-01", "V-02", "V-03", "V-04", "V-05", "V-06", "V-07"}
    v1 = reg["V-01"]
    assert v1["outline_m2"] == "26.240000"                      # 7.02 x 4.00 - 1.15 x 1.60
    assert v1["floor_1F"]["result"] == "DEDUCTED_TWICE"
    assert X(v1["floor_1F"]["residual_after_overlap_m2"]).copy_abs() <= R.TOL_M2   # the overlap explains it all
    assert v1["ceiling_GF"]["result"] == "DEDUCTED_ONCE"
    assert v1["ceiling_top"]["result"] == "DOUBLE_COUNT_RISK"
    assert reg["V-02"]["result"] == "EXTERIOR" and reg["V-03"]["result"] == "DEDUCTED_ONCE"
    assert all(c["result"].startswith("DEDUCTED_ONCE") for k in ("V-05", "V-06") for c in reg[k]["ceiling_below"])
    assert reg["V-07"]["status"] == "HELD" and reg["V-07"]["outline_m2"] is None   # never 0
    assert doc["moved"].startswith("none")


def test_drawn_file_holds_no_coordinates_or_names():
    txt = (B / "T719_DRAWN.json").read_text(encoding="utf-8")
    doc = json.loads(txt)

    def nums(o):
        if isinstance(o, dict):
            for v in o.values():
                yield from nums(v)
        elif isinstance(o, list):
            for v in o:
                yield from nums(v)
        elif isinstance(o, (int, float)) and not isinstance(o, bool):
            yield o
    assert max(abs(v) for v in nums(doc)) < 200            # lengths / areas / votes only, no drawing coordinate
    assert "senan" not in txt.lower()
