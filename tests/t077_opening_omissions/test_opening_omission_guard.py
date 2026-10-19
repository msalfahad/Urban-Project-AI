"""T-077: every drawn window and door appears once (MEASURED or HELD with its traced cause), never silently lost.

Hand-calculated synthetic villa frame (NOT the development villa): a straight wall band along the x axis, wall 0.20 m
thick (faces y = 0 and y = 0.20 m), drawn in metres, then the same frame mirrored, rotated 30 degrees and in mm.

    A  window 1.20 m, jambs at x = 1.00 and 2.20, glazing two lines inside      -> engine opening OP-001: MEASURED
    B  window 0.50 m, jambs at x = 4.00 and 4.50, a column 4.47 .. 5.20 overlaps
       the gap by 0.03 m; a printed dimension 0.50 from jamb to jamb            -> engine has nothing (the column cut
       leaves 0.47 < 0.50 m): HELD COLUMN_CUT_PIECE_UNDER_MIN_GAP, jamb to jamb 0.50, clear 0.47, printed 0.50
    C  curved glazing between jambs x = 7.00 and 10.00 (chord 3.00 m), two concentric arcs bulging outwards (y < 0),
       radii 1.95 and 2.00 m on one centre, each over the full chord angle of the 2.00 m arc (whose ends sit on the
       jamb lines):
           half angle a = asin(1.50 / 2.00) = 0.848062079 rad, sweep 2a = 1.696124158 rad
           arc 1.95 m: 1.95 x 1.696124158 = 3.3074 m; arc 2.00 m: 2.00 x 1.696124158 = 3.3922 m
       no wall arc on that centre                                                -> HELD
       CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND, jamb to jamb 3.00
    D  glazing drawn on a wall with no jamb line across it (x = 12.0 .. 13.0)    -> HELD NO_JAMB_AT_BOTH_ENDS
    E  0.45 m gap with glazing (jambs x = 15.00, 15.45)                           -> HELD GAP_UNDER_MIN_GAP
    doors: a block swing used by a released element (MEASURED, BLOCK), a loose-arc swing used by a held element
    (HELD, LOOSE_ARC), a swing no element uses (HELD SWING_NOT_IN_ENGINE)
Totals: windows drawn 5 = 1 engine + 4 held; doors drawn 3 = 1 released + 2 held; silent omissions 0.
"""

from __future__ import annotations

import inspect
import math

import pytest

from engine.source import lintel_measure as LM
from engine.source import opening_omission_guard as G

A_HALF = math.asin(1.5 / 2.0)
SWEEP = 2 * A_HALF


# ------------------------------------------------------------------------------------------- the transformed frame
class T:
    def __init__(self, rot_deg=0.0, mirror=False, scale=1.0, shift=(0.0, 0.0)):
        self.c, self.s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
        self.mirror, self.k, self.shift = mirror, scale, shift

    def p(self, x, y):
        if self.mirror:
            x = -x
        return (self.k * (self.c * x - self.s * y) + self.shift[0], self.k * (self.s * x + self.c * y) + self.shift[1])

    def v(self, x, y):
        if self.mirror:
            x = -x
        return (self.c * x - self.s * y, self.s * x + self.c * y)

    def seg(self, i, a, b):
        return {"id": i, "a": self.p(*a), "b": self.p(*b)}

    def arc(self, i, c, r, a0, a1):
        """CCW arc of radius r (local metres) from angle a0 to a1; a mirror turns it CW."""
        s = (c[0] + r * math.cos(a0), c[1] + r * math.sin(a0))
        e = (c[0] + r * math.cos(a1), c[1] + r * math.sin(a1))
        return {"id": i, "c": self.p(*c), "r": r * self.k, "s": self.p(*s), "e": self.p(*e),
                "dir": "CW" if self.mirror else "CCW"}

    def opening(self, oid, kind, x0, x1, width_m):
        u, n = self.v(1, 0), self.v(0, 1)
        pts = [self.p(x, y) for x in (x0, x1) for y in (0.0, 0.2)]
        ss = [q[0] * u[0] + q[1] * u[1] for q in pts]
        oo = [q[0] * n[0] + q[1] * n[1] for q in pts]
        return {"opening_id": oid, "kind": kind, "u": u, "n": n, "s0": min(ss), "s1": max(ss), "o0": min(oo),
                "o1": max(oo), "width_m": width_m}


def frame(t):
    walls = [t.seg("W-A0", (0.0, 0.0), (1.0, 0.0)), t.seg("W-A1", (0.0, 0.2), (1.0, 0.2)),
             t.seg("J-A0", (1.0, 0.0), (1.0, 0.2)), t.seg("J-A1", (2.2, 0.0), (2.2, 0.2)),
             t.seg("W-B0", (2.2, 0.0), (4.0, 0.0)), t.seg("W-B1", (2.2, 0.2), (4.0, 0.2)),
             t.seg("J-B0", (4.0, 0.0), (4.0, 0.2)), t.seg("J-B1", (4.5, 0.0), (4.5, 0.2)),
             t.seg("W-C0", (4.5, 0.0), (7.0, 0.0)), t.seg("W-C1", (4.5, 0.2), (7.0, 0.2)),
             t.seg("J-C0", (7.0, 0.0), (7.0, 0.2)), t.seg("J-C1", (10.0, 0.0), (10.0, 0.2)),
             t.seg("W-D0", (10.0, 0.0), (15.0, 0.0)), t.seg("W-D1", (10.0, 0.2), (15.0, 0.2)),
             t.seg("J-E0", (15.0, 0.0), (15.0, 0.2)), t.seg("J-E1", (15.45, 0.0), (15.45, 0.2)),
             t.seg("W-E0", (15.45, 0.0), (18.0, 0.0)), t.seg("W-E1", (15.45, 0.2), (18.0, 0.2))]
    cx, cy = 8.5, math.sqrt(2.0 ** 2 - 1.5 ** 2) + 0.1        # the centre above the wall line, arcs bulge to y < 0
    th0, th1 = -math.pi / 2 - A_HALF, -math.pi / 2 + A_HALF
    glazing = {
        "segments": [t.seg("G-A0", (1.0, 0.08), (2.2, 0.08)), t.seg("G-A1", (1.0, 0.12), (2.2, 0.12)),
                     t.seg("G-Ac", (1.0, 0.08), (1.0, 0.12)),
                     t.seg("G-B0", (4.0, 0.08), (4.5, 0.08)), t.seg("G-B1", (4.0, 0.12), (4.5, 0.12)),
                     t.seg("G-Bc", (4.0, 0.08), (4.0, 0.12)),
                     t.seg("G-Cc", (cx + 2.0 * math.cos(th0), cy + 2.0 * math.sin(th0)),
                           (cx + 1.95 * math.cos(th0), cy + 1.95 * math.sin(th0))),
                     t.seg("G-D0", (12.0, 0.08), (13.0, 0.08)), t.seg("G-D1", (12.0, 0.12), (13.0, 0.12)),
                     t.seg("G-Dc", (12.0, 0.08), (12.0, 0.12)),
                     t.seg("G-E0", (15.0, 0.08), (15.45, 0.08)), t.seg("G-E1", (15.0, 0.12), (15.45, 0.12)),
                     t.seg("G-Ec", (15.0, 0.08), (15.0, 0.12))],
        "arcs": [t.arc("G-C0", (cx, cy), 2.0, th0, th1), t.arc("G-C1", (cx, cy), 1.95, th0, th1)]}
    columns = [[t.p(4.47, -0.05), t.p(5.2, -0.05), t.p(5.2, 0.25), t.p(4.47, 0.25)]]
    dims = [{"id": "DIM-B", "kind": "LINEAR", "value_du": 0.5 * t.k, "p1": t.p(4.0, 1.0), "p2": t.p(4.5, 1.0)},
            {"id": "DIM-X", "kind": "LINEAR", "value_du": 0.6 * t.k, "p1": t.p(4.0, 1.0), "p2": t.p(4.6, 1.0)}]
    openings = [t.opening("OP-001", "WINDOW", 1.0, 2.2, 1.2)]
    swings = {"I1|A1@I1:0": {"hinge": t.p(20, 0), "radius": 0.9 * t.k},
              "A2:0|A2:0": {"hinge": t.p(22, 0), "radius": 0.7 * t.k},
              "I3|A3@I3:0": {"hinge": t.p(24, 0), "radius": 0.8 * t.k}}
    elements = [{"element_id": "DOOR-1", "swings": ["I1|A1@I1:0"], "released": True, "section": "RELEASED",
                 "structural_opening_width_m": 1.0},
                {"element_id": "DOOR-2", "swings": ["A2:0|A2:0"], "released": False,
                 "section": "PROVISIONAL_NOT_RELEASED", "structural_opening_width_m": 0.8}]
    return dict(openings=openings, glazing=glazing, swings=swings, door_elements=elements, walls=walls,
                columns=columns, dims=dims)


CASES = [("plain_m", T(), 1.0), ("mirrored_m", T(mirror=True), 1.0), ("rotated30_m", T(rot_deg=30.0), 1.0),
         ("rotated30_mirrored_mm", T(rot_deg=30.0, mirror=True, scale=1000.0, shift=(-164000.0, -805000.0)), 0.001),
         ("mm_far", T(scale=1000.0, shift=(-209565.0, -811916.0)), 0.001)]


def _held(res):
    return sorted((w for w in res["windows"] if w["status"] == "HELD"),
                  key=lambda w: w["diagnosis"].get("spans", {}).get("jamb_to_jamb_m") or 0.0)


@pytest.mark.parametrize("name,t,unit", CASES, ids=[c[0] for c in CASES])
def test_hand_fixture(name, t, unit):
    res = G.guard(frame=name, unit_m=unit, **frame(t))
    s = res["summary"]
    assert s["windows_drawn"] == 5 and s["windows_engine"] == 1 and s["windows_held"] == 4
    assert s["held_by_cause"] == {"COLUMN_CUT_PIECE_UNDER_MIN_GAP": 1, "CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND": 1,
                                  "GAP_UNDER_MIN_GAP": 1, "NO_JAMB_AT_BOTH_ENDS": 1}
    assert s["silent_omissions"] == 0 and s["glazing_clusters"] == 5
    by = {w["cause"]: w for w in _held(res)}
    b = by["COLUMN_CUT_PIECE_UNDER_MIN_GAP"]["diagnosis"]
    assert b["spans"]["jamb_to_jamb_m"] == pytest.approx(0.50, abs=1e-4)
    assert b["spans"]["column_overlap_m"] == [pytest.approx(0.03, abs=1e-4)]
    assert b["spans"]["clear_pieces_m"] == [pytest.approx(0.47, abs=1e-4)]
    assert [p["printed_m"] for p in b["printed"]] == [pytest.approx(0.50, abs=1e-4)]      # DIM-X (0.60) refused
    c = by["CURVED_GLAZING_WITHOUT_CURVED_WALL_BAND"]["diagnosis"]
    assert c["spans"]["jamb_to_jamb_m"] == pytest.approx(3.00, abs=1e-4)
    arcs = c["curved"]["glazing_arcs"]
    assert [a["radius_m"] for a in arcs] == [pytest.approx(1.95, abs=1e-4), pytest.approx(2.00, abs=1e-4)]
    assert [a["length_m"] for a in arcs] == [pytest.approx(3.3074, abs=1e-4), pytest.approx(3.3922, abs=1e-4)]
    assert c["curved"]["concentric_wall_arcs"] == 0
    assert by["GAP_UNDER_MIN_GAP"]["diagnosis"]["spans"]["jamb_to_jamb_m"] == pytest.approx(0.45, abs=1e-4)
    for w in _held(res):                                                   # held: nothing released, never 0
        assert w["width_m"] is None and w["height_m"] is None and w["area_m2"] is None
    win = [w for w in res["windows"] if w["status"] == "MEASURED"]
    assert [(w["opening_id"], len(w["clusters"])) for w in win] == [("OP-001", 1)]
    # doors
    assert s["doors_drawn"] == 3 and s["doors_released"] == 1 and s["doors_held"] == 2
    d = {x["element_id"] or x["swings"][0]: x for x in res["doors"]}
    assert d["DOOR-1"]["status"] == "MEASURED" and d["DOOR-1"]["symbol"] == ["BLOCK"]
    assert d["DOOR-2"]["status"] == "HELD" and d["DOOR-2"]["symbol"] == ["LOOSE_ARC"]
    assert d["DOOR-2"]["engine_section"] == "PROVISIONAL_NOT_RELEASED"
    assert d["I3|A3@I3:0"]["reason"] == "SWING_NOT_IN_ENGINE" and d["I3|A3@I3:0"]["leaf_m"] == pytest.approx(0.8)


def test_units_missing_never_converts():
    res = G.guard(frame="nounits", unit_m=None, **frame(T()))
    assert res["summary"]["unit_status"] == "UNITS_MISSING"
    assert res["summary"]["windows_drawn"] == 5 and res["summary"]["silent_omissions"] == 0
    for w in res["windows"]:
        if w["status"] == "HELD":
            assert w["diagnosis"]["glazing_length_m"] is None
            assert w["diagnosis"]["printed"] == []


def test_bad_unit_refused():
    with pytest.raises(ValueError):
        G.guard([], {}, unit_m=0)


def test_empty_frame():
    res = G.guard([], {"segments": [], "arcs": []}, unit_m=0.001)
    assert res["summary"]["windows_drawn"] == 0 and res["summary"]["doors_drawn"] == 0


def test_window_with_no_wall_gap_at_all():
    """glazing alone in an unbroken wall (no jamb lines anywhere): held, not dropped."""
    t = T()
    walls = [t.seg("W0", (0, 0), (5, 0)), t.seg("W1", (0, 0.2), (5, 0.2))]
    gl = {"segments": [t.seg("G0", (2, 0.1), (3, 0.1))], "arcs": []}
    res = G.guard([], gl, walls=walls, unit_m=1.0)
    (w,) = res["windows"]
    assert w["status"] == "HELD" and w["cause"] == "NO_JAMB_AT_BOTH_ENDS"
    assert w["diagnosis"]["spans"]["glazing_extent_m"] == pytest.approx(1.0)


def test_glazing_in_a_door_gap_is_bound_to_that_opening():
    """a glazed door's glazing lies in a DOOR opening: bound there, not a held window, not a window count."""
    t = T()
    op = t.opening("OP-007", "DOOR", 1.0, 2.0, 1.0)
    gl = {"segments": [t.seg("G0", (1.0, 0.1), (2.0, 0.1))], "arcs": []}
    res = G.guard([op], gl, unit_m=1.0)
    assert res["summary"]["windows_drawn"] == 0 and res["summary"]["clusters_in_other_openings"] == 1


def test_curved_opening_of_a_curved_band_binds():
    """a V2.9 curved opening (COP) with its concentric glazing arc: MEASURED, nothing held."""
    c, r1, r2 = (0.0, 0.0), 3.0, 3.2
    th0, th1 = 0.2, 1.2
    op = {"opening_id": "COP-001", "kind": "WINDOW", "width_m": r2 * (th1 - th0),
          "curved": {"centre_du": [0.0, 0.0], "radii_du": [r1, r2], "angles_rad": [th0, th1, th0, th1]}}
    gl = {"segments": [], "arcs": [T().arc("G0", c, 3.1, th0, th1)]}
    wall_arcs = [T().arc("WA0", c, r1, th1, th0 + 2 * math.pi), T().arc("WA1", c, r2, th1, th0 + 2 * math.pi)]
    res = G.guard([op], gl, wall_arcs=wall_arcs, unit_m=1.0)
    assert res["summary"]["windows_engine"] == 1 and res["summary"]["windows_held"] == 0


def test_curved_glazing_with_concentric_wall_arcs_reports_refused_gap():
    c = (0.0, 0.0)
    gl = {"segments": [], "arcs": [T().arc("G0", c, 3.1, 0.2, 1.2)]}
    wall_arcs = [T().arc("WA0", c, 3.0, 1.2, 0.2 + 2 * math.pi)]
    rej = [{"reason": "NO_JAMB_LINE_AT_BOTH_ENDS", "r1_m": 3.0, "r2_m": 3.2}]
    res = G.guard([], gl, wall_arcs=wall_arcs, unit_m=1.0, curved_rejected=rej)
    (w,) = res["windows"]
    assert w["cause"] == "CURVED_GLAZING_CURVED_GAP_REFUSED" and w["diagnosis"]["curved_rejected"] == rej


def test_min_gap_is_the_band_opening_minimum():
    assert inspect.signature(LM.openings).parameters["min_gap_m"].default == G.MIN_GAP_M


def test_engine_drops_the_column_cut_piece_the_guard_holds():
    """cause check on the engine itself: lintel_measure.openings on case B's walls (mm) returns no opening for the
    0.50 m gap whose column leaves 0.47 m, and the 1.20 m window is found; the guard holds B."""
    t = T(scale=1000.0)
    fr = frame(t)
    segs = [dict(s, layer="WALL") for s in fr["walls"]]
    col = fr["columns"][0]
    box = (min(p[0] for p in col), min(p[1] for p in col), max(p[0] for p in col), max(p[1] for p in col))
    ops, _rej = LM.openings(segs, 0.001, ["WALL"], [box])
    widths = sorted(round(o["width_m"], 3) for o in ops)
    assert 1.2 in widths and 0.5 not in widths and 0.47 not in widths
    for o in ops:
        o["kind"] = "WINDOW" if abs(o["width_m"] - 1.2) < 1e-6 else "PASSAGE"
    res = G.guard(ops, fr["glazing"], walls=fr["walls"], columns=fr["columns"], dims=fr["dims"], unit_m=0.001)
    causes = {w["cause"] for w in res["windows"] if w["status"] == "HELD"}
    assert "COLUMN_CUT_PIECE_UNDER_MIN_GAP" in causes


def test_conservation_every_piece_and_swing_once():
    fr = frame(T(rot_deg=30.0))
    res = G.guard(unit_m=1.0, **fr)
    ids = [i for c in res["clusters"] for i in c["ids"]]
    assert sorted(ids) == sorted(str(x["id"]) for x in fr["glazing"]["segments"] + fr["glazing"]["arcs"])
    sw = [s for d in res["doors"] for s in d["swings"]]
    assert sorted(sw) == sorted(fr["swings"])
    rows = G.census_rows(res)
    assert len(rows) == res["summary"]["windows_drawn"] + res["summary"]["doors_drawn"]
