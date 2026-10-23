"""T-197 CURVED_GEOMETRY_CHECK_V1: hand fixtures, NOT the development villa (villa "T197-K", metres unless stated).

Hand truth (r x theta, sector / segment formulas, worked here, never taken from the module):
  K-WALL  curved wall band, centre (10, 5), outer r 3.20, inner r 3.00, quarter circle 0 -> 90 deg, radial ends:
          outer arc 3.2 pi / 2 = 5.026548; inner 3.0 pi / 2 = 4.712389; centreline 3.1 pi / 2 = 4.869469 (= mean);
          outer chord 3.2 sqrt 2 = 4.525483; true plan area pi / 4 (3.2^2 - 3.0^2) = 0.973894;
          chord polygon (3.2^2 - 3.0^2) / 2 = 0.620000.
  K-WIN   window in a curved wall, outer r 2.50, inner r 2.30, 60 deg: outer arc 2.5 pi / 3 = 2.617994 (supply,
          owner Q-39 C basis), inner arc 2.3 pi / 3 = 2.408554, inner chord 2 x 2.3 sin 30 = 2.300000 (the elevation's
          projected width), outer chord 2.500000.
  K-SLAB  slab 4 x 3 with the north edge bulged outward, bulge 0.5 on the span (4, 3) -> (0, 3): theta = 4 atan 0.5 =
          1.854590 rad, r = 4 / (2 sin(theta / 2)) = 2.5, sagitta 1.0; segment = 2.5^2 / 2 (theta - sin theta) =
          3.125 x (1.854590 - 0.96) = 2.795595; true area 12 + 2.795595 = 14.795595; arc 2.5 theta = 4.636476;
          perimeter 4 + 3 + 4.636476 + 3 = 14.636476; chord perimeter 14; straight parts alone 10.
  K-RING  full ring, outer r 1.2, inner r 1.0, each circle drawn as two half arcs: true area pi (1.44 - 1) =
          1.382301; north half band 0.691150; each half arc outer 1.2 pi = 3.769911, inner pi = 3.141593.
Adverse: a mirrored OCS (extrusion -1) and a mirrored INSERT through the K2 ezdxf route keep the bulge outward (area
14.795595, never 12 - 2.795595 = 9.204405); millimetres stated (same result) vs the same numbers as metres (refused); an
ARC of 359.9 deg (6.281439 m at r 1, not a full circle, not 0); a polyline bulge vs an ARC entity of the same quarter
circle (same length pi); a straight wall 0.05 m from an arc (never flagged); a shared boundary arc between a ring and the
slab outside it (not a double count); bad inputs refused."""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.source import curved_geometry_check_v1 as CG          # noqa: E402


def wall():
    return {"element_id": "K-WALL", "kind": "WALL", "units": "m", "ref": "villa K plan, wall W9",
            "pieces": [
                {"piece_id": "o", "role": "OUTER", "centre": (10, 5), "radius": 3.2, "start_angle": 0, "end_angle": 90},
                {"piece_id": "e1", "role": "OUTER", "line": [(10, 8.2), (10, 8.0)]},
                {"piece_id": "i", "role": "INNER", "centre": (10, 5), "radius": 3.0, "start_angle": 0, "end_angle": 90},
                {"piece_id": "e2", "role": "INNER", "line": [(13, 5), (13.2, 5)]}],
            "loops": [{"pieces": ["o", "e1", "i", "e2"]}]}


def _wall_no_ends():
    w = wall()
    w["pieces"] = [p for p in w["pieces"] if p["piece_id"] in ("o", "i")]
    w["loops"] = []
    return w


def _codes(res, lid):
    return next(r for r in res["lines"] if r["line_id"] == lid)["codes"]


def test_wall_bases_by_hand():
    res = CG.check([_wall_no_ends()], [])
    c = res["elements"][0]["length_candidates"]
    assert c["ARC:OUTER"] == pytest.approx(5.026548, abs=1e-6)
    assert c["ARC:INNER"] == pytest.approx(4.712389, abs=1e-6)
    assert c["ARC:CENTRELINE"] == pytest.approx(4.869469, abs=1e-6)
    assert c["CHORD:OUTER"] == pytest.approx(4.525483, abs=1e-6)
    res = CG.check([wall()], [])
    a = res["elements"][0]["area_candidates"]
    assert a["TRUE:AREA"] == pytest.approx(0.973894, abs=1e-6)
    assert a["CHORD:AREA"] == pytest.approx(0.620000, abs=1e-6)


def test_wall_lines_named_unnamed_straightened_mismatch():
    w = _wall_no_ends()
    lines = [
        {"line_id": "L1", "element_id": "K-WALL", "family": "BLOCK_FACE_OUT", "measure": "LENGTH", "value": 5.0265,
         "units": "m", "basis": "OUTER_ARC"},
        {"line_id": "L2", "element_id": "K-WALL", "family": "BLOCK_AXIS", "measure": "LENGTH", "value": 4.8695,
         "units": "m"},
        {"line_id": "L3", "element_id": "K-WALL", "family": "PLASTER_OUT", "measure": "LENGTH", "value": 4.5255,
         "units": "m", "basis": "CHORD", "chord_role": "OUTER"},
        {"line_id": "L6", "element_id": "K-WALL", "family": "PAINT_OUT", "measure": "LENGTH", "value": 4.7124,
         "units": "m", "basis": "OUTER_ARC"}]
    res = CG.check([w], lines)
    assert _codes(res, "L1") == []
    assert _codes(res, "L2") == ["BASIS_UNNAMED"]
    assert "ARC:CENTRELINE" in next(r for r in res["lines"] if r["line_id"] == "L2")["matches"]
    assert _codes(res, "L3") == ["STRAIGHTENED"]
    assert _codes(res, "L6") == ["BASIS_MISMATCH"]
    assert "ARC:INNER" in next(r for r in res["lines"] if r["line_id"] == "L6")["matches"]


def test_wall_area_true_vs_chord_and_double():
    lines = [
        {"line_id": "A1", "element_id": "K-WALL", "family": "CONC", "measure": "PLAN_AREA", "value": 0.9739,
         "units": "m", "basis": "TRUE_AREA"},
        {"line_id": "A5", "element_id": "K-WALL", "family": "SCREED", "measure": "PLAN_AREA", "value": 0.62,
         "units": "m", "basis": "CHORD_AREA"},
        {"line_id": "A7", "element_id": "K-WALL", "family": "CONC", "measure": "PLAN_AREA", "value": 0.9739,
         "units": "m", "basis": "TRUE_AREA"}]
    res = CG.check([wall()], lines)
    assert _codes(res, "A5") == ["STRAIGHTENED"]
    dbl = [i for i in res["issues"] if i["code"] == "DOUBLE_ARC"]
    assert len(dbl) == 1 and dbl[0]["line_ids"] == "A1;A7"
    assert "9.7389" in dbl[0]["detail"]                   # 5.026548 + 4.712389 of arc measured twice
    lines[2]["status"] = "SUPERSEDED"
    res = CG.check([wall()], lines)
    assert not [i for i in res["issues"] if i["code"] == "DOUBLE_ARC"]
    assert _codes(res, "A1") == []


def window():
    return {"element_id": "K-WIN", "kind": "OPENING", "units": "m", "ref": "villa K first floor, curved window",
            "pieces": [
                {"piece_id": "go", "role": "OUTER", "centre": (0, 0), "radius": 2.5, "start_angle": 60,
                 "end_angle": 120},
                {"piece_id": "gi", "role": "INNER", "centre": (0, 0), "radius": 2.3, "start_angle": 60,
                 "end_angle": 120}]}


def test_curved_window_three_bases_each_in_its_family():
    lines = [
        {"line_id": "SUP", "element_id": "K-WIN", "family": "OPENING_SUPPLY", "measure": "LENGTH", "value": 2.618,
         "units": "m", "basis": "OUTER_ARC"},
        {"line_id": "ELEV", "element_id": "K-WIN", "family": "ELEVATION_ID", "measure": "LENGTH", "value": 2.30,
         "units": "m", "basis": "PROJECTED_CHORD", "chord_role": "INNER", "purpose": "IDENTITY"},
        {"line_id": "FAC", "element_id": "K-WIN", "family": "FACADE_DEDUCTION", "measure": "LENGTH", "value": 2.4086,
         "units": "m"},
        {"line_id": "SUP2", "element_id": "K-WIN", "family": "SILL", "measure": "LENGTH", "value": 2.50, "units": "m"}]
    res = CG.check([window()], lines)
    assert _codes(res, "SUP") == []
    assert _codes(res, "ELEV") == []                     # an identity chord is not a quantity
    assert _codes(res, "FAC") == ["BASIS_UNNAMED"]
    # 2.4086 is the inner arc; the derived centreline chord (2.50 + 2.30) / 2 = 2.40 is also within 1 cm: both are
    # listed (the check never picks one), and the line stays BASIS_UNNAMED until its ledger names it
    assert next(r for r in res["lines"] if r["line_id"] == "FAC")["matches"] == ["ARC:INNER", "CHORD:CENTRELINE"]
    assert _codes(res, "SUP2") == ["BASIS_UNNAMED", "STRAIGHTENED"]
    # same window measured at half its arc, covering one of two drawn pieces: PARTIAL
    w = window()
    w["pieces"] = [{"piece_id": "a", "role": "OUTER", "centre": (0, 0), "radius": 2.5, "start_angle": 60,
                    "end_angle": 90},
                   {"piece_id": "b", "role": "OUTER", "centre": (0, 0), "radius": 2.5, "start_angle": 90,
                    "end_angle": 120}]
    res = CG.check([w], [{"line_id": "H", "element_id": "K-WIN", "family": "OPENING_SUPPLY", "measure": "LENGTH",
                          "value": 1.309, "units": "m", "basis": "OUTER_ARC", "covers": ["a"]}])
    assert _codes(res, "H") == ["PARTIAL"]
    assert "not covered b (1.3090 m of arc)" in next(i for i in res["issues"])["detail"]


def slab(z=1.0, units="m", k=1.0):
    pts = [(0, 0, 0), (4, 0, 0), (4, 3, 0.5), (0, 3, 0)]
    pts = [(x * k, y * k, b) for x, y, b in pts]
    pcs = CG.pieces_from_polyline("s", "FACE", pts, closed=True, extrusion_z=z)
    return {"element_id": "K-SLAB", "kind": "SLAB_EDGE", "units": units, "ref": "villa K roof slab, curved north edge",
            "pieces": pcs, "loops": [{"pieces": [p["piece_id"] for p in pcs]}]}


def test_slab_curved_edge_by_hand():
    res = CG.check([slab()], [])
    e = res["elements"][0]
    assert e["area_candidates"]["TRUE:AREA"] == pytest.approx(14.795595, abs=1e-6)
    assert e["area_candidates"]["CHORD:AREA"] == pytest.approx(12.0, abs=1e-9)
    assert e["length_candidates"]["ARC:FACE"] == pytest.approx(14.636476, abs=1e-6)
    assert e["arcs"][0]["r"] == pytest.approx(2.5, abs=1e-9)
    assert e["arcs"][0]["side"] == "IN"                 # material inside the arc's circle: an outward bulge


def test_slab_lines():
    lines = [
        {"line_id": "S1", "element_id": "K-SLAB", "family": "CONC.SLAB", "measure": "PLAN_AREA", "value": 14.7956,
         "units": "m", "basis": "TRUE_AREA"},
        {"line_id": "S2", "element_id": "K-SLAB", "family": "SCREED", "measure": "PLAN_AREA", "value": 12.0,
         "units": "m"},
        {"line_id": "S3", "element_id": "K-SLAB", "family": "EDGE_FORM", "measure": "LENGTH", "value": 14.6365,
         "units": "m", "basis": "FACE_ARC"},
        {"line_id": "S4", "element_id": "K-SLAB", "family": "EDGE_PAINT", "measure": "LENGTH", "value": 14.0,
         "units": "m", "basis": "CHORD", "chord_role": "FACE"},
        {"line_id": "S5", "element_id": "K-SLAB", "family": "EDGE_TRIM", "measure": "LENGTH", "value": 10.0,
         "units": "m", "basis": "FACE_ARC"},
        {"line_id": "S6", "element_id": "K-SLAB", "family": "EDGE_SEAL", "measure": "LENGTH", "value": 14.8365,
         "units": "m", "basis": "FACE_ARC"}]
    res = CG.check([slab()], lines)
    assert _codes(res, "S1") == []
    assert _codes(res, "S2") == ["BASIS_UNNAMED", "STRAIGHTENED"]
    assert _codes(res, "S3") == []
    assert _codes(res, "S4") == ["STRAIGHTENED"]
    assert _codes(res, "S5") == ["PARTIAL"]              # the straight parts alone: 4.6365 m of arc not measured
    assert "4.6365" in next(i["detail"] for i in res["issues"] if i["line_ids"] == "S5")
    assert _codes(res, "S6") == ["OVER_OUTLINE"]         # +0.20 m past the drawn face (a region-tool leak)
    # a deduction the line states moves it back onto its basis
    lines[3:] = [dict(lines[4], value=8.0, deductions=2.0)]
    res = CG.check([slab()], lines)
    assert _codes(res, "S5") == ["PARTIAL"]


def test_mirrored_ocs_keeps_the_bulge_outward():
    res = CG.check([slab(z=-1.0)], [])
    e = res["elements"][0]
    assert e["area_candidates"]["TRUE:AREA"] == pytest.approx(14.795595, abs=1e-6)   # not 9.204405
    assert e["arcs"][0]["side"] == "IN"
    # the arc's mid point is mirrored too: x -> -x, y unchanged
    m = CG.arc_from_bulge((4, 3), (0, 3), 0.5, -1.0)
    assert m.mid == pytest.approx((-2.0, 4.0), abs=1e-9)
    assert CG.arc_from_bulge((4, 3), (0, 3), 0.5, 1.0).mid == pytest.approx((2.0, 4.0), abs=1e-9)


def test_mirrored_insert_through_the_k2_route():
    ezdxf = pytest.importorskip("ezdxf")
    from engine.source.cad import kernel_ezdxf as K2
    doc = ezdxf.new()
    blk = doc.blocks.new("K197")
    blk.add_arc((0, 0), 2.0, 0, 90)
    blk.add_lwpolyline([(0, 0, 0, 0, 0), (4, 0, 0, 0, 0), (4, 3, 0, 0, 0.5), (0, 3, 0, 0, 0)],
                       format="xyseb", close=True)
    doc.modelspace().add_blockref("K197", (10, 0), dxfattribs={"xscale": -1.0})
    geo = K2.realise(doc)
    arcs = sorted(geo.arcs, key=lambda a: a.radius)
    a = arcs[0]                                          # the ARC r 2: (2, 0) -> (0, 2) mirrored about x = 10
    pc = {"piece_id": "m", "role": "FACE", "centre": a.center, "radius": a.radius, "start": a.start, "end": a.end,
          "mid": a.mid}
    p = CG._piece(pc, 1.0, "mirror")
    assert p.arc.length == pytest.approx(math.pi, abs=1e-9)
    assert p.arc.mid == pytest.approx((10 - math.sqrt(2), math.sqrt(2)), abs=1e-9)
    b = arcs[1]                                          # the bulge span, r 2.5
    segs = [s for s in geo.segments]
    pieces = [{"piece_id": f"l{i}", "role": "FACE", "line": [s.a, s.b]} for i, s in enumerate(segs)]
    pieces.append({"piece_id": "arc", "role": "FACE", "centre": b.center, "radius": b.radius, "start": b.start,
                   "end": b.end, "mid": b.mid})
    el = {"element_id": "K-SLAB-M", "kind": "SLAB_EDGE", "units": "m", "ref": "mirrored insert", "pieces": pieces,
          "loops": [{"pieces": [x["piece_id"] for x in pieces]}]}
    res = CG.check([el], [])
    assert res["elements"][0]["area_candidates"]["TRUE:AREA"] == pytest.approx(14.795595, abs=1e-6)
    assert b.mid[1] == pytest.approx(4.0, abs=1e-9)      # the bulge stays on the outside (north) after the mirror


def test_millimetres_stated_and_refused_as_metres():
    res = CG.check([slab(units="mm", k=1000.0)],
                   [{"line_id": "S1", "element_id": "K-SLAB", "family": "CONC.SLAB", "measure": "PLAN_AREA",
                     "value": 14795595.0, "units": "mm", "basis": "TRUE_AREA"}])
    assert res["elements"][0]["area_candidates"]["TRUE:AREA"] == pytest.approx(14.795595, abs=1e-6)
    assert _codes(res, "S1") == []
    with pytest.raises(ValueError, match="millimetres given as metres"):
        CG.check([slab(units="m", k=1000.0)], [])
    with pytest.raises(ValueError, match="units must be"):
        CG.check([dict(slab(), units=None)], [])


def test_arc_of_359_9_degrees():
    a = CG.arc_from_dxf_arc((0, 0), 1.0, 0.0, 359.9)
    assert a.length == pytest.approx(6.281439, abs=1e-6)
    assert a.chord == pytest.approx(2 * math.sin(math.radians(0.05)), abs=1e-9)
    full = CG.arc_from_dxf_arc((0, 0), 1.0, 30.0, 30.0)
    assert full.length == pytest.approx(2 * math.pi, abs=1e-12)
    with pytest.raises(ValueError, match="full circle or nothing"):
        CG.arc_from_points((0, 0), 1.0, (1, 0), (1, 0))
    # realised form: ends 0.1 deg apart, mid opposite -> the long way round, not the 0.1 deg way
    e = (math.cos(math.radians(359.9)), math.sin(math.radians(359.9)))
    r = CG.arc_from_points((0, 0), 1.0, (1, 0), e, (-1, 0))
    assert r.length == pytest.approx(6.281439, abs=1e-6)


def test_bulge_and_arc_entity_of_the_same_geometry_agree():
    b = CG.arc_from_bulge((2, 0), (0, 2), math.tan(math.radians(22.5)))
    a = CG.arc_from_dxf_arc((0, 0), 2.0, 0, 90)
    assert b.length == pytest.approx(a.length, abs=1e-12) == pytest.approx(math.pi, abs=1e-12)
    assert b.centre == pytest.approx((0, 0), abs=1e-12)
    assert b.mid == pytest.approx(a.mid, abs=1e-12)
    els = [{"element_id": "E1", "kind": "WALL_FACE", "units": "m", "ref": "x",
            "pieces": [{"piece_id": "p", "role": "FACE", "a": (2, 0), "b": (0, 2), "bulge": math.tan(math.pi / 8)}]},
           {"element_id": "E2", "kind": "WALL_FACE", "units": "m", "ref": "x",
            "pieces": [{"piece_id": "q", "role": "FACE", "centre": (0, 0), "radius": 2, "start_angle": 0,
                        "end_angle": 90}]}]
    lines = [{"line_id": f"P{i}", "element_id": e, "family": "PLASTER", "measure": "LENGTH", "value": math.pi,
              "units": "m", "basis": "FACE_ARC"} for i, e in enumerate(("E1", "E2"))]
    res = CG.check(els, lines)
    assert [i["code"] for i in res["issues"]] == ["DOUBLE_ARC"]   # one arc drawn twice, measured twice


def test_straight_wall_next_to_an_arc_is_not_flagged():
    els = [{"element_id": "K-STRAIGHT", "kind": "WALL", "units": "m", "ref": "villa K wall W2",
            "pieces": [{"piece_id": "f", "role": "FACE", "line": [(0, 2.05), (3, 2.05)]}]},
           {"element_id": "K-ARC", "kind": "WALL_FACE", "units": "m", "ref": "villa K curved wall W3",
            "pieces": [{"piece_id": "q", "role": "FACE", "centre": (0, 0), "radius": 2, "start_angle": 0,
                        "end_angle": 90}]}]
    lines = [{"line_id": "W2", "element_id": "K-STRAIGHT", "family": "PLASTER", "measure": "LENGTH", "value": 3.0,
              "units": "m"},
             {"line_id": "W3", "element_id": "K-ARC", "family": "PLASTER", "measure": "LENGTH", "value": math.pi,
              "units": "m", "basis": "FACE_ARC"}]
    res = CG.check(els, lines)
    assert res["issues"] == []


def ring():
    pcs = [{"piece_id": "o1", "role": "OUTER", "centre": (0, 0), "radius": 1.2, "start_angle": 0, "end_angle": 180},
           {"piece_id": "o2", "role": "OUTER", "centre": (0, 0), "radius": 1.2, "start_angle": 180, "end_angle": 360},
           {"piece_id": "i1", "role": "INNER", "centre": (0, 0), "radius": 1.0, "start_angle": 0, "end_angle": 180},
           {"piece_id": "i2", "role": "INNER", "centre": (0, 0), "radius": 1.0, "start_angle": 180, "end_angle": 360}]
    return {"element_id": "K-RING", "kind": "RING", "units": "m", "ref": "villa K roof, ring beam R1", "pieces": pcs,
            "loops": [{"pieces": ["o1", "o2"]}, {"pieces": ["i1", "i2"], "hole": True}],
            "expected_families": ["CONC.BEAM"]}


def half_band():
    pcs = [{"piece_id": "o", "role": "OUTER", "centre": (0, 0), "radius": 1.2, "start_angle": 0, "end_angle": 180},
           {"piece_id": "w", "role": "OUTER", "line": [(-1.2, 0), (-1.0, 0)]},
           {"piece_id": "i", "role": "INNER", "centre": (0, 0), "radius": 1.0, "start_angle": 0, "end_angle": 180},
           {"piece_id": "e", "role": "OUTER", "line": [(1.0, 0), (1.2, 0)]}]
    return {"element_id": "K-RING-N", "kind": "RING", "units": "m", "ref": "route band over R1 north",
            "pieces": pcs, "loops": [{"pieces": ["o", "w", "i", "e"]}]}


def slab_outside_ring():
    pcs = [{"piece_id": "o", "role": "OUTER", "centre": (0, 0), "radius": 1.5, "start_angle": 0, "end_angle": 180},
           {"piece_id": "w", "role": "FACE", "line": [(-1.5, 0), (-1.2, 0)]},
           {"piece_id": "i", "role": "INNER", "centre": (0, 0), "radius": 1.2, "start_angle": 0, "end_angle": 180},
           {"piece_id": "e", "role": "FACE", "line": [(1.2, 0), (1.5, 0)]}]
    return {"element_id": "K-SLAB-N", "kind": "SLAB_EDGE", "units": "m", "ref": "slab around R1 north",
            "pieces": pcs, "loops": [{"pieces": ["o", "w", "i", "e"]}]}


def test_ring_split_into_two_arcs():
    res = CG.check([ring(), half_band()], [])
    a = {e["element_id"]: e["area_candidates"]["TRUE:AREA"] for e in res["elements"]}
    assert a["K-RING"] == pytest.approx(1.382301, abs=1e-6)
    assert a["K-RING-N"] == pytest.approx(0.691150, abs=1e-6)


def test_ring_double_partial_and_shared_boundary():
    lines = [{"line_id": "RING", "element_id": "K-RING", "family": "CONC.BEAM", "measure": "PLAN_AREA",
              "value": 1.3823, "units": "m", "basis": "TRUE_AREA"},
             {"line_id": "BAND", "element_id": "K-RING-N", "family": "CONC.BEAM", "measure": "PLAN_AREA",
              "value": 0.6912, "units": "m", "basis": "TRUE_AREA"},
             {"line_id": "SLAB", "element_id": "K-SLAB-N", "family": "CONC.BEAM", "measure": "PLAN_AREA",
              "value": 1.4137, "units": "m", "basis": "TRUE_AREA"}]
    res = CG.check([ring(), half_band(), slab_outside_ring()], lines)
    dbl = [i for i in res["issues"] if i["code"] == "DOUBLE_ARC"]
    assert len(dbl) == 1 and dbl[0]["line_ids"] == "RING;BAND"           # the slab only shares the r 1.2 boundary
    assert "6.9115" in dbl[0]["detail"]                                 # 1.2 pi + 1.0 pi
    # the ring line superseded: the band alone leaves the south half uncovered
    lines[0]["status"] = "SUPERSEDED"
    res = CG.check([ring(), half_band(), slab_outside_ring()], lines)
    part = [i for i in res["issues"] if i["code"] == "PARTIAL"]
    assert len(part) == 1 and part[0]["element_id"] == "K-RING" and "6.9115" in part[0]["detail"]
    assert not [i for i in res["issues"] if i["code"] == "DOUBLE_ARC"]
    # no CONC.BEAM line at all: NOT_MEASURED (information), never a zero
    res = CG.check([ring()], [])
    assert [i["code"] for i in res["issues"]] == ["NOT_MEASURED"]


@pytest.mark.parametrize("bad, msg", [
    ({"role": "SIDE"}, "role"),
    ({"start": (1, 0), "end": (0, 1.01), "centre": (0, 0), "radius": 1.0, "mid": None}, "off its circle"),
])
def test_bad_pieces_refused(bad, msg):
    pc = {"piece_id": "p", "role": "FACE", "centre": (0, 0), "radius": 1.0, "start_angle": 0, "end_angle": 90}
    if "start" in bad:
        pc = {"piece_id": "p", "role": "FACE", **bad}
    else:
        pc.update(bad)
    with pytest.raises(ValueError, match=msg):
        CG.check([{"element_id": "X", "kind": "WALL", "units": "m", "ref": "x", "pieces": [pc]}], [])


def test_bad_lines_refused():
    w = _wall_no_ends()
    base = {"line_id": "L", "element_id": "K-WALL", "family": "F", "measure": "LENGTH", "value": 1.0, "units": "m"}
    for change, msg in (({"basis": "CHORD"}, "chord_role"), ({"element_id": "NOPE"}, "unknown element"),
                        ({"covers": ["zz"]}, "unknown pieces"), ({"measure": "PLAN_AREA"}, "no loops"),
                        ({"basis": "TRUE_AREA"}, "not a LENGTH basis"), ({"units": None}, "units must be"),
                        ({"value": 5026.5}, "millimetres given as metres"), ({"status": "DRAFT"}, "status")):
        with pytest.raises(ValueError, match=msg):
            CG.check([w], [dict(base, **change)])
    with pytest.raises(ValueError, match="does not close"):
        bad = wall()
        bad["loops"] = [{"pieces": ["o", "i", "e2"]}]
        CG.check([bad], [])
    with pytest.raises(ValueError, match="the mid point says"):
        CG.arc_from_points((0, 0), 1.0, (1, 0), (0, 1), (math.sqrt(.5), math.sqrt(.5)), "CW")
