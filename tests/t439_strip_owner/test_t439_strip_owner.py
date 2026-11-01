"""T-439 STRIP_OWNER_V1 (R-T439-1) on hand villa K439 (not Alsenan).

Villa K439, one storey, hand figures (metres, room-local, origin = inner SW corner of each room):
  K1 kitchenette, WET, printed box 4.00 x 2.50 = 10.00 m2, tiled full height (wall-tile line WT-K1), open on its east
     side (x 4.00) to the living room. An L counter along the south wall: the engine cut out the piece under it
     P1 = (2.80, 0) (4.00, 0) (4.00, 1.00) (3.40, 1.00) (3.40, 0.60) (2.80, 0.60) = 1.20 x 0.60 + 0.60 x 0.40 = 0.96 m2,
     edges: south wall 1.20 (WALL_FACE), east open edge 1.00, an undrawn zone line 0.60, counter outline 0.40 + 0.60 + 0.60.
     Beam BK1 (D 0.80, CALCULATED) crosses P1 with a 0.90 m face to slab: owner face 0.90 x (0.80 - 0.60) = 0.18 m2.
     Beam BK2 (D 0.50) along the zone line: hidden above the decor ceiling (no face).
     An unregistered piece beside BK1: 0.30 m of edge HELD (never 0).
  K2 living, DRY, a strip P2 2.00 x 0.20 = 0.40 m2 inside its box along a wall: skirting 2.00 lm on that wall.
  S1 doorway strip 0.90 x 0.20 = 0.18 m2 between two jambs: ceiling = opening soffit, skirting DOORWAY.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

import pytest
from shapely import affinity
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t439"))
import strip_owner_v1 as S  # noqa: E402

K1 = {"id": "K1", "class": "WET", "full_height_tile": True, "wall_tile_line": "WT-K1", "skirting_line": None}
K2 = {"id": "K2", "class": "DRY", "full_height_tile": False, "wall_tile_line": None, "skirting_line": "SK-K2"}

P1_POLY = Polygon([(2.8, 0), (4.0, 0), (4.0, 1.0), (3.4, 1.0), (3.4, 0.6), (2.8, 0.6)])
DRAWN = [("W-south", "WALL_FACE", LineString([(0, 0), (4.0, 0)])),
         ("E-open", "ROOM_EDGE_OPEN", LineString([(4.0, 0), (4.0, 2.5)])),
         ("C1", "FIXTURE_OUTLINE", LineString([(3.4, 1.0), (3.4, 0.6)])),
         ("C2", "FIXTURE_OUTLINE", LineString([(3.4, 0.6), (2.8, 0.6)])),
         ("C3", "FIXTURE_OUTLINE", LineString([(2.8, 0.6), (2.8, 0.0)]))]


def edges_p1():
    return [{"length_m": 1.2, "role": "WALL_FACE"}, {"length_m": 1.0, "role": "ROOM_EDGE_OPEN"},
            {"length_m": 0.6, "role": "ZONE_LINE_UNDRAWN"}, {"length_m": 0.4, "role": "FIXTURE_OUTLINE"},
            {"length_m": 0.6, "role": "FIXTURE_OUTLINE"}, {"length_m": 0.6, "role": "FIXTURE_OUTLINE"}]


def p1(**kw):
    d = {"id": "P1", "floor_m2": 0.96, "in_room_box_m2": 0.96, "edges": edges_p1()}
    d.update(kw)
    return d


def segs():
    return [{"beam": "BK1", "m": 0.90, "beam_depth_m": 0.80, "beam_status": "CALCULATED", "neighbour": "SLAB"},
            {"beam": "BK2", "m": 0.60, "beam_depth_m": 0.50, "beam_status": "CALCULATED", "neighbour": "SLAB"},
            {"beam": "BK1", "m": 0.30, "beam_depth_m": 0.80, "beam_status": "CALCULATED",
             "neighbour": "UNREGISTERED"}]


# ------------------------------------------------------------------------------------------------- normal cases
def test_p1_area_by_hand():
    assert math.isclose(P1_POLY.area, 1.2 * 0.6 + 0.6 * 0.4, abs_tol=1e-9)


def test_counter_piece_is_room_piece_with_ceiling_proposal():
    d = S.decide(p1(), K1, segs())
    assert d["kind"] == "ROOM_PIECE"
    c = d["ceiling"]
    assert c["code"] == "CEILING_CONTINUES_FROM_ROOM" and c["room_class"] == "WET"
    assert c["decor_m2"] == 0.96 and c["decor_status"] == S.ST_DC
    assert c["bulkhead_m2"] == pytest.approx(0.18) and c["bulkhead_status"] == S.ST_OA
    assert c["paintable_owner_m2"] == pytest.approx(1.14)
    assert c["held_edge_m"] == pytest.approx(0.30)          # unregistered neighbour: HELD, never 0
    assert [x["beam"] for x in c["no_face"]] == ["BK2"]      # D 0.50 under the 0.60 allowance
    assert c["board_type"] == S.ST_H                        # wet room board type not specified


def test_counter_piece_skirting_tile_owns_the_wall_base():
    k = S.decide(p1(), K1, segs())["skirting"]
    assert k["tile_owned_lm"] == pytest.approx(1.2) and k["skirting_lm"] is None
    assert k["status"] == S.ST_NA
    assert sum(r["m"] for r in k["rows"] if r["owner"] == "NO_BASE") == pytest.approx(3.2)
    assert all(r["line"] == "WT-K1" for r in k["rows"] if r["owner"] == "TILE_OWNS")


def test_dry_strip_takes_skirting_lm():
    st = {"id": "P2", "floor_m2": 0.40, "in_room_box_m2": 0.40,
          "edges": [{"length_m": 2.0, "role": "WALL_FACE"}, {"length_m": 0.2, "role": "ZONE_LINE_UNDRAWN"},
                    {"length_m": 2.0, "role": "ZONE_LINE_UNDRAWN"}, {"length_m": 0.2, "role": "ZONE_LINE_UNDRAWN"}]}
    d = S.decide(st, K2)
    assert d["skirting"]["skirting_lm"] == 2.0 and d["skirting"]["status"] == S.ST_DC
    assert d["ceiling"]["board_type"].startswith("gypsum")


def test_doorway_strip_gets_soffit_reason_and_no_skirting():
    st = {"id": "S1", "floor_m2": 0.18, "in_room_box_m2": None,
          "edges": [{"length_m": 0.2, "role": "OPENING_JAMB"}, {"length_m": 0.9, "role": "ZONE_LINE_UNDRAWN"},
                    {"length_m": 0.2, "role": "OPENING_JAMB"}, {"length_m": 0.9, "role": "ZONE_LINE_UNDRAWN"}]}
    d = S.decide(st, K2)
    assert d["kind"] == "DOORWAY" and d["ceiling"]["code"] == "OPENING_SOFFIT_IN_WALL"
    assert d["skirting"]["skirting_lm"] is None


def test_step_face_against_a_deep_neighbour_beam():
    sg = [{"beam": "B9", "m": 1.0, "beam_depth_m": 0.90, "beam_status": "CALCULATED", "neighbour": "BEAM",
           "neighbour_depth_m": 0.70, "neighbour_status": "CALCULATED"}]
    c = S.decide(p1(), K1, sg)["ceiling"]
    assert c["bulkhead_m2"] == pytest.approx(0.20)          # 0.90 - max(0.60, 0.70)


def test_carried_segment_is_not_counted_again():
    sg = segs()
    sg[0]["carried_by"] = "L-existing"
    c = S.decide(p1(), K1, sg)["ceiling"]
    assert c["bulkhead_m2"] == 0.0 and c["bulkhead_status"] is None


@pytest.mark.parametrize("deg", [0, 37, 90, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_edge_roles_survive_rotation_and_mirror(deg, mirror):
    def tf(g):
        g = affinity.scale(g, -1 if mirror else 1, 1, origin=(0, 0))
        g = affinity.rotate(g, deg, origin=(0, 0))
        return affinity.translate(g, 123.4, -56.7)
    e = S.classify_edges(tf(P1_POLY), [(r, ro, tf(s)) for r, ro, s in DRAWN])
    got = sorted((round(x["length_m"], 4), x["role"]) for x in e)
    want = sorted((round(x["length_m"], 4), x["role"]) for x in edges_p1())
    assert got == want


def test_room_closure_by_hand():
    assert S.room_closure(10.0, {"rest": 9.04, "P1": 0.96}) == 0.0
    assert S.room_closure(10.0, {"rest": 9.00, "P1": 0.96}) == pytest.approx(0.04)   # named, not forced to 0


# ------------------------------------------------------------------------------------------------ adverse cases
def test_door_strip_given_a_room_ceiling_with_no_drawn_soffit_is_refused():
    st = {"id": "S1", "floor_m2": 0.18, "in_room_box_m2": 0.18,
          "edges": [{"length_m": 0.2, "role": "OPENING_JAMB"}, {"length_m": 0.2, "role": "OPENING_JAMB"}]}
    with pytest.raises(S.StripError):
        S.decide(st, K2, proposal={"kind": "ROOM_CEILING"})
    ok = S.decide(st, K2, proposal={"kind": "ROOM_CEILING", "soffit_ref": "section A-A head"})
    assert ok["ceiling"]["code"] == "OPENING_SOFFIT_IN_WALL"


def test_strip_outside_every_box_is_held_with_area_kept():
    d = S.decide(p1(in_room_box_m2=0.50), K1, segs())
    assert d["kind"] == "HELD"
    assert d["ceiling"]["m2"] is None and d["ceiling"]["area_kept_m2"] == 0.96
    assert d["skirting"]["tile_owned_lm"] == pytest.approx(1.2)   # the tiled room still owns its own wall base


def test_held_strip_in_a_dry_room_keeps_wall_lm_held():
    st = {"id": "P3", "floor_m2": 0.4, "in_room_box_m2": 0.1, "edges": [{"length_m": 2.0, "role": "WALL_FACE"}]}
    k = S.decide(st, K2)["skirting"]
    assert k["held_lm"] == 2.0 and k["skirting_lm"] is None and k["status"] == S.ST_H


def test_wall_behind_a_fixture_in_a_dry_room_is_held_not_zero():
    st = {"id": "P4", "floor_m2": 0.4, "in_room_box_m2": 0.4,
          "edges": [{"length_m": 2.0, "role": "WALL_FACE", "fixture_covers": True}]}
    k = S.decide(st, K2)["skirting"]
    assert k["held_lm"] == 2.0 and k["status"] == S.ST_H


def test_tiled_room_without_its_tile_line_is_refused():
    with pytest.raises(S.StripError):
        S.decide(p1(), dict(K1, wall_tile_line=None), segs())


def test_unknown_edge_role_is_refused():
    with pytest.raises(S.StripError):
        S.decide(p1(edges=[{"length_m": 1.0, "role": "CONFLICT"}]), K1)


@pytest.mark.parametrize("where", ["strip", "edge", "segment"])
def test_units_other_than_metres_are_refused(where):
    st = p1()
    sg = segs()
    if where == "strip":
        st["unit"] = "mm2"
    elif where == "edge":
        st["edges"][0]["unit"] = "mm"
    else:
        sg[0]["unit"] = "mm"
    with pytest.raises(S.StripError):
        S.decide(st, K1, sg)


def test_beam_not_calculated_gives_held_edge_not_zero():
    sg = [{"beam": "BX", "m": 0.8, "beam_depth_m": 0.9, "beam_status": "CONFLICT", "neighbour": "SLAB"}]
    c = S.decide(p1(), K1, sg)["ceiling"]
    assert c["bulkhead_m2"] == 0.0 and c["held_edge_m"] == pytest.approx(0.8)


def test_missing_depth_is_held():
    sg = [{"beam": "BY", "m": 0.5, "beam_depth_m": None, "beam_status": "CALCULATED", "neighbour": "SLAB"}]
    assert S.decide(p1(), K1, sg)["ceiling"]["held_edge_m"] == pytest.approx(0.5)


def test_closure_with_a_piece_without_figure_is_refused():
    with pytest.raises(S.StripError):
        S.room_closure(10.0, {"rest": 9.04, "P1": None})


def test_engine_zone_line_is_not_a_drawn_line():
    e = S.classify_edges(P1_POLY, [d for d in DRAWN if d[0] != "E-open"])
    roles = [x["role"] for x in e if math.isclose(x["length_m"], 1.0)]
    assert roles == ["ZONE_LINE_UNDRAWN"]


# ------------------------------------------------------------------------------------- committed Alsenan output
def test_committed_alsenan_table_reproduces():
    r = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t439" / "t439_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_committed_alsenan_figures_pinned():
    s = json.loads((ROOT / "research" / "agents_t439" / "summary.json").read_text())
    t = s["totals"]
    assert t["ceiling_decor_new_m2"] == pytest.approx(1.70)
    assert t["ceiling_bulkhead_new_m2"] == pytest.approx(0.842 * 0.25 + 1.4 * 0.15 + 0.2485 * 0.25)
    assert t["skirting_lm"] is None and t["skirting_tile_owned_lm"] == pytest.approx(1.6)
    assert s["box"]["ceiling_m2_carried_plus_strips"] == pytest.approx(13.455)
    assert abs(s["box"]["closure_m2"]) < 1e-5
    for b in s["beam_reconciliation"].values():
        assert abs(b["residual_m"]) < 1e-3
    assert all(st["kind"] == "ROOM_PIECE" for st in s["strips"])
