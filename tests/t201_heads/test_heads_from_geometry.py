"""T-201: heads / sills from drawn geometry on a NON-Alsenan hand fixture (villa T201-V), normal and adverse cases.

Villa T201-V (hand truth, millimetres on the elevation, datum = the view's +-0.00 dimension-chain tick at y = 0):
- raised ground floor: FFL +0.90 (a 0.90 m podium), first floor FFL +4.40;
- facade plan positions (centres along the facade, m) and printed plan widths: A 2.000 / 1.20, B 4.500 / 0.60,
  C 7.250 / 1.50; the elevation draws them (x from the first drawn edge, mm): A 0 .. 1200, B 2800 .. 3400,
  C 5100 .. 6600 (drawn centre = plan position - 1.400 m; spacing 2.500 / 2.750 m reproduced to 0 mm);
- A: sill 1900 / head 3400 -> levels +1.90 / +3.40 -> 1.00 / 2.50 above the +0.90 floor, height 1.50, 1.800 m2;
- B: sill 2600 / head 3400 -> 1.70 / 2.50 above FFL, 0.80 high, 0.480 m2;
- C (first floor): sill 5400 / head 6900 -> 1.00 / 2.50 above +4.40, 1.500 x 1.500 = 2.250 m2.
The naive reading 'sill above the drawn ground line' gives A 1.90 (wrong by the 0.90 podium): the re-datum lesson.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t201"))

import heads_from_geometry as G                                        # noqa: E402

PLAN = [("A", 2.000, 1.20), ("B", 4.500, 0.60), ("C", 7.250, 1.50)]
DRAWN = [("a", 0, 1200), ("b", 2800, 3400), ("c", 5100, 6600)]
DAT = G.datum(0.0, 0.0, "mm", "T201-V elevation +-0.00 chain tick")


def _bind(plan=PLAN, drawn=DRAWN, **kw):
    b = G.bind([(p, x, w) for p, x, w in plan], drawn, **kw)
    return {k: v for k, v in b["bound"].items()}, b


def test_binding_solves_the_offset_and_checks_widths():
    bound, b = _bind()
    assert bound == {"A": "a", "B": "b", "C": "c"}
    assert b["offset_m"] == pytest.approx(-1.400, abs=1e-6)
    assert all(ok for _, _, ok in b["width_check"].values())


def test_normal_raised_floor_redatum():
    a = G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=0.90, current_issue=[0.006, -0.006, 0.0, 0.013], tol_m=0.04)
    assert (a["sill_level_m"], a["head_level_m"], a["height_m"]) == (1.90, 3.40, 1.5)
    assert (a["sill_above_ffl_m"], a["head_above_ffl_m"]) == (1.0, 2.5)
    assert a["status"] == G.DC_GEOM and a["issue_check"].startswith("AGREES")
    assert G.area(a, 1.20) == pytest.approx(1.800)
    b = G.head_record("B", 0.60, 2600, 3400, DAT, ffl_m=0.90)
    assert (b["sill_above_ffl_m"], b["head_above_ffl_m"], G.area(b, 0.60)) == (1.7, 2.5, 0.48)
    assert b["issue_check"] == "NOT CHECKED"                       # never silently agreed
    c = G.head_record("C", 1.50, 5400, 6900, DAT, ffl_m=4.40)
    assert (c["sill_above_ffl_m"], c["head_above_ffl_m"], G.area(c, 1.50)) == (1.0, 2.5, 2.25)


def test_adverse_ground_line_is_not_the_floor():
    # reading the sill above the drawn ground line (FFL 0.00) instead of the +0.90 podium floor would give 1.90:
    a = G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=0.0)
    assert a["sill_above_ffl_m"] == 1.9                            # the arithmetic is right; the datum choice is the test
    a2 = G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=0.90)
    assert a2["sill_above_ffl_m"] != a["sill_above_ffl_m"]
    # a floor ABOVE the drawn sill is refused (wrong floor / wrong datum)
    with pytest.raises(G.GeometryError):
        G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=4.40)


def test_unknown_ffl_holds_only_the_above_ffl_value():
    a = G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=None)
    assert a["status"] == G.DC_GEOM and a["height_m"] == 1.5 and a["sill_above_ffl_m"] is None
    assert G.area(a, 1.20) == pytest.approx(1.8)


def test_adverse_units_and_datum():
    with pytest.raises(G.GeometryError):
        G.datum(None, 0.0, "mm", "x")                              # no drawn datum: no default origin
    with pytest.raises(G.GeometryError):
        G.datum(0.0, 0.0, "mm", "")                                # no source
    with pytest.raises(G.GeometryError):
        G.datum(0.0, 0.0, "inch", "x")
    with pytest.raises(G.GeometryError):
        G.datum(0.0, 900.0, "m", "x")                              # a level in mm typed as metres
    dm = G.datum(0.0, 0.0, "m", "metre drawing")
    a = G.head_record("A", 1.20, 1.9, 3.4, dm, ffl_m=0.90)
    assert (a["sill_above_ffl_m"], a["head_above_ffl_m"]) == (1.0, 2.5)   # same answer in metres
    with pytest.raises(G.GeometryError):
        G.head_record("A", 1.20, 3400, 1900, DAT)                  # head below sill


def test_adverse_mirrored_elevation_binds_only_when_declared():
    mirrored = [("a", -1200, 0), ("b", -3400, -2800), ("c", -6600, -5100)]
    bound, b = _bind(drawn=mirrored, mirrored=True)
    assert bound == {"A": "a", "B": "b", "C": "c"}
    bound2, b2 = _bind(drawn=mirrored, mirrored=False)
    assert bound2 != {"A": "a", "B": "b", "C": "c"}                # undeclared mirror never binds all three


def test_adverse_symmetric_twins_are_ambiguous():
    plan = [("T1", 3.000, 1.00)]
    drawn = [("x", 0, 1000), ("y", 4000, 5000)]
    b = G.bind(plan, drawn, units="mm")
    assert b["status"] == "AMBIGUOUS" and b["bound"] == {}


def test_adverse_drawn_outline_not_the_opening_holds_with_candidates():
    # shutters drawn over the jambs: the frame outline is 0.12 m narrower than the printed plan width
    bound, b = _bind(plan=[("S", 2.000, 1.95), ("Z", 5.000, 0.60)], drawn=[("s", 58, 1897), ("z", 3677.5, 4277.5)])
    assert b["width_check"]["S"][2] is False and b["width_check"]["Z"][2] is True
    s = G.head_record("S", 1.95, 940, 2957, DAT, width_ok=False, candidates=["shutter extent 2.201", "frame 2.017"])
    assert s["status"] == G.HELD and G.area(s, 1.95) is None and s["candidates"]


def test_adverse_current_issue_differs_holds():
    a = G.head_record("A", 1.20, 1900, 3400, DAT, ffl_m=0.90, current_issue=[0.0, 0.0, 0.0, 0.150], tol_m=0.04)
    assert a["status"] == G.HELD and a["issue_check"].startswith("DIFFERS")
    assert G.area(a, 1.20) is None                                 # held never becomes 0 or a number


def test_section_cut_and_held_count():
    w = G.head_record("G", 6.0, 1000, 3200, G.datum(0, 0.0, "mm", "section tick"), ffl_m=1.0, cut_only=True)
    assert w["status"] == G.DC_GEOM and w["head_above_ffl_m"] == 2.2 and "cut" in w["why"]
    w2 = G.head_record("G", 6.0, 1000, 3200, G.datum(0, 0.0, "mm", "section tick"), ffl_m=1.0, cut_only=True,
                       count_held="one opening or two with a pier")
    assert w2["status"] == G.HELD and w2["height_m"] == 2.2 and G.area(w2, 6.0) is None


def test_missing_edges_hold_not_zero():
    r = G.head_record("P", 0.90, None, None, DAT)
    assert r["status"] == G.HELD and r["height_m"] is None and G.area(r, 0.90) is None
