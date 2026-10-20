"""T-087: tiles to buy per room from a laid grid with the owner's joint widths (engine/source/tile_count.py).

Hand fixtures (metres, not a client drawing). Owner Q-42: joint 1 mm inside, 2 mm on roofs / outside; pitch = tile + joint.
A whole tile is placed while (room length - position) >= tile; the remainder is one cut piece (tile_layout, CORNER start).

H1  3.00 x 2.40 room, 600 x 600, INSIDE (1 mm, pitch 0.601):
      along 3.00: 0, 0.601, 1.202, 1.803 -> 4 whole, 3.00 - 2.404 = 0.596 cut  -> pieces [.6 .6 .6 .6 .596]
      along 2.40: 0, 0.601, 1.202        -> 3 whole, 2.40 - 1.803 = 0.597 cut  -> pieces [.6 .6 .6 .597]
      5 x 4 = 20 positions: 4 x 3 = 12 whole, 8 cut; no offcut reuse -> 20 tiles; every start corner the same.
H2  same room, ROOF (2 mm, pitch 0.602): 3.00 - 2.408 = 0.592, 2.40 - 1.806 = 0.594 -> 12 whole + 8 cut = 20 tiles;
      expansion joints HELD (spacing / BOQ line not answered).
H3  same room, printed joint 0 mm (replaces the owner default): 3.00 / 0.60 = 5, 2.40 / 0.60 = 4 -> 20 whole, 0 cut.
H4  3.005 x 2.40, 600 x 600: 1 mm: 3.005 - 2.404 = 0.601 >= 0.600 -> 5 whole, pos 3.005, nothing left -> 5 columns;
      rows 3 whole + 0.597 -> 5 x 4 = 20 positions, 15 whole + 5 cut = 20 tiles.
      printed 0 mm: 5 whole + a 0.005 sliver -> 6 columns x 4 rows = 24 positions, 20 whole + 4 cut = 24 tiles.
      (the joint changes the count by 4 tiles = 20 % here: why Q-42 matters for the count, not the m2.)
H5  3.00 x 2.40, 1200 x 600, INSIDE (1 mm):
      0 deg (1.20 along the 3.00 wall): 0, 1.201 -> 2 whole + 3.00 - 2.402 = 0.598 cut; across 3 whole + 0.597
          -> 3 x 4 = 12 positions: 6 whole + 6 cut = 12 tiles
      90 deg (0.60 along 3.00): 4 whole + 0.596; across 2.40: 1 whole + 2.40 - 1.201 = 1.199 cut
          -> 5 x 2 = 10 positions: 4 whole + 6 cut = 10 tiles
      fewest = 10 (90 deg), direction range 0 deg 12-12, 90 deg 10-10.
H6  L-shaped room (0,0) (3,0) (3,1.201) (1.201,1.201) (1.201,2.4) (0,2.4), 600 x 600, INSIDE; net 3.00 x 1.201 +
      1.201 x 1.199 = 5.042999 m2. Columns x [0-.6] [.601-1.201] [1.202-1.802] [1.803-2.403] [2.404-3.0];
      rows y [0-.6] [.601-1.201] [1.202-1.802] [1.803-2.4].
      from (min x, min y): rows 1-2: 4 whole + 1 cut each; row 3: 2 whole (leg x <= 1.201); row 4: 2 cut (0.597)
          -> 10 whole + 4 cut = 14 tiles
      from (max x, min y) (x mirrored, leg at x' 1.799-3.0): rows 1-2: 4 + 1 cut each; row 3: col 3 cut (1.799-1.802
          sliver), col 4 whole, col 5 cut; row 4: 3 cut -> 9 whole + 7 cut = 16
      from (min x, max y): row 1: 2 whole; row 2: 2 whole + 3 slivers (the 2 mm band 1.199-1.201); row 3: 4 + 1 cut;
          row 4: 5 cut -> 8 whole + 9 cut = 17
      from (max x, max y): row 1: 1 whole + 2 cut; row 2: 1 whole + 4 cut; row 3: 4 + 1; row 4: 5 cut
          -> 6 whole + 12 cut = 18
      fewest 14 (start at the corner where the two long walls meet), most 18: the start corner moves 4 tiles (29 %).
H7  3.30 x 2.40, 600 x 600, INSIDE: along 3.30 five whole (last at 2.404, pos 3.005) + 3.30 - 3.005 = 0.295 cut;
      rows 3 whole + 0.597 -> 15 whole + 9 cut (5 of 0.600 x 0.597, 3 of 0.295 x 0.600, 1 of 0.295 x 0.597).
      no reuse: 24 tiles. Reuse of offcuts >= 0.20 m inside the room: each 0.600 x 0.597 leaves a 0.003 strip (scrap)
      -> 5 tiles; the first 0.295 x 0.600 leaves 0.305 x 0.600 (kept), the second is cut from it (leaves 0.010:
      scrap), the third opens a tile (0.305 x 0.600 kept), the corner 0.295 x 0.597 comes from that offcut -> 2 tiles;
      15 + 5 + 2 = 22 tiles. Reuse not answered by the owner -> HELD, the 24 upper bound and every layout still shown.
Adversarial: rotation 30 deg, mirror, millimetre units, missing size / exposure / units / outline -> HELD, never 0;
the census reads printed sizes (Arabic and English, Arabic-Indic digits) and never takes a column or door size.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import tile_count as T  # noqa: E402

RECT = [(0, 0), (3.0, 0), (3.0, 2.4), (0, 2.4)]
L_ROOM = [(0, 0), (3.0, 0), (3.0, 1.201), (1.201, 1.201), (1.201, 2.4), (0, 2.4)]


def size(L, W, origin="OWNER", source="owner value (test)"):
    return {"length_m": L, "width_m": W, "origin": origin, "source": source, "concerns": []}


S60 = size(0.6, 0.6)
S120 = size(1.2, 0.6)


def counts(rec):
    return {x["layout"]: x["tiles_to_buy"] for x in rec["layouts"]}


def rot(poly, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return [(x * c - y * s + 7.3, x * s + y * c - 2.1) for x, y in poly]


# ---- H1 - H3: joint widths by exposure, printed joint wins ----------------------------------------------------------

def test_h1_inside_1mm_rectangle():
    r = T.count_room({"polygon": RECT, "room_id": "R1"}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["status"] == "RELEASED" and r["joint"]["joint_m"] == 0.001 and r["joint"]["origin"] == "OWNER_DEFAULT"
    first = r["layouts"][0]
    assert first["pieces_x_m"] == [0.6, 0.6, 0.6, 0.6, 0.596]
    assert first["pieces_y_m"] == [0.6, 0.6, 0.6, 0.597]
    assert (first["whole_tiles"], first["cut_pieces"], first["tiles_to_buy"]) == (12, 8, 20)
    assert set(counts(r).values()) == {20} and len(r["layouts"]) == 8
    assert r["tiles_to_buy"] == 20 and r["expansion_joints"] is None
    assert "SQUARE_TILE" in " ".join(r["concerns"])
    assert abs(r["net_m2"] - 7.2) < 1e-9


def test_h2_roof_2mm_and_expansion_joints_held():
    r = T.count_room({"polygon": RECT}, units="m", size=S60, exposure="ROOF", offcut_reuse=False)
    assert r["joint"]["joint_m"] == 0.002
    first = r["layouts"][0]
    assert first["pieces_x_m"][-1] == 0.592 and first["pieces_y_m"][-1] == 0.594
    assert r["tiles_to_buy"] == 20
    assert r["expansion_joints"]["status"] == "HELD" and r["expansion_joints"]["width_m"] == 0.003


def test_h3_printed_joint_replaces_owner_default():
    r = T.count_room({"polygon": RECT}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False,
                     printed_joint_m=0.0,
                     printed_joint_source="finish schedule note (test)")
    assert r["joint"]["origin"] == "PRINTED" and r["joint"]["joint_m"] == 0.0
    first = r["layouts"][0]
    assert (first["whole_tiles"], first["cut_pieces"], first["tiles_to_buy"]) == (20, 0, 20)


def test_h4_joint_changes_the_count():
    room = {"polygon": [(0, 0), (3.005, 0), (3.005, 2.4), (0, 2.4)]}
    a = T.count_room(room, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    b = T.count_room(room, units="m", size=S60, exposure="INSIDE", offcut_reuse=False, printed_joint_m=0.0)
    la, lb = a["layouts"][0], b["layouts"][0]
    assert (la["whole_tiles"], la["cut_pieces"], la["tiles_to_buy"]) == (15, 5, 20)
    assert (lb["whole_tiles"], lb["cut_pieces"], lb["tiles_to_buy"]) == (20, 4, 24)


# ---- H5: the direction is shown, not chosen silently ----------------------------------------------------------------

def test_h5_rectangular_tile_two_directions():
    r = T.count_room({"polygon": RECT}, units="m", size=S120, exposure="INSIDE", offcut_reuse=False)
    assert r["by_direction"] == {"0deg": {"fewest": 12, "most": 12}, "90deg": {"fewest": 10, "most": 10}}
    z = next(x for x in r["layouts"] if x["layout"] == "0deg from MIN_X_MIN_Y")
    n = next(x for x in r["layouts"] if x["layout"] == "90deg from MIN_X_MIN_Y")
    assert (z["whole_tiles"], z["cut_pieces"]) == (6, 6) and z["pieces_x_m"] == [1.2, 1.2, 0.598]
    assert (n["whole_tiles"], n["cut_pieces"]) == (4, 6) and n["pieces_y_m"] == [1.2, 1.199]
    assert r["tiles_to_buy"] == 10 and r["fewest"]["layout"] == "90deg from MIN_X_MIN_Y"
    assert "every layout is listed" in r["selection_basis"]


# ---- H6: L-shaped room, the start corner matters ---------------------------------------------------------------------

L_EXPECT = {"MIN_X_MIN_Y": (10, 4, 14), "MAX_X_MIN_Y": (9, 7, 16), "MIN_X_MAX_Y": (8, 9, 17), "MAX_X_MAX_Y": (6, 12, 18)}


def test_h6_l_room_every_start_corner():
    r = T.count_room({"polygon": L_ROOM, "room_id": "L"}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert abs(r["net_m2"] - 5.042999) < 1e-9
    for x in r["layouts"]:
        assert (x["whole_tiles"], x["cut_pieces"], x["tiles_to_buy"]) == L_EXPECT[x["start_corner"]], x["layout"]
    assert r["tiles_to_buy"] == 14 and r["fewest"]["layout"] == "0deg from MIN_X_MIN_Y"
    assert r["by_direction"]["0deg"] == {"fewest": 14, "most": 18}
    corner = {x["start_corner"]: x["start_corner_drawing_m"] for x in r["layouts"]}
    assert corner["MIN_X_MIN_Y"] == [0.0, 0.0] and corner["MAX_X_MAX_Y"] == [3.0, 2.4]


def test_h6_mirrored_l_room_same_counts_corner_swapped():
    mir = [(-x, y) for x, y in L_ROOM]
    r = T.count_room({"polygon": mir}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert sorted(counts(r).values()) == sorted([14, 16, 17, 18] * 2)
    assert r["tiles_to_buy"] == 14
    best = next(x for x in r["layouts"] if x["layout"] == r["fewest"]["layout"])
    assert best["start_corner_drawing_m"] == [0.0, 0.0]          # the same physical corner of the room


@pytest.mark.parametrize("deg", [30.0, -61.0])
def test_rotation_does_not_change_counts(deg):
    a = T.count_room({"polygon": RECT}, units="m", size=S120, exposure="INSIDE", offcut_reuse=False)
    b = T.count_room({"polygon": rot(RECT, deg)}, units="m", size=S120, exposure="INSIDE", offcut_reuse=False)
    assert sorted(counts(a).values()) == sorted(counts(b).values()) and b["tiles_to_buy"] == 10
    c = T.count_room({"polygon": rot(L_ROOM, deg)}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert sorted(counts(c).values()) == sorted([14, 16, 17, 18] * 2)
    assert abs(c["net_m2"] - 5.042999) < 1e-7


def test_millimetre_units():
    mm = [(x * 1000, y * 1000) for x, y in L_ROOM]
    r = T.count_room({"polygon": mm}, units="mm", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["tiles_to_buy"] == 14 and abs(r["net_m2"] - 5.042999) < 1e-7
    cm = [(x * 100, y * 100) for x, y in RECT]
    r = T.count_room({"polygon": cm}, units="cm", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["tiles_to_buy"] == 20


def test_hole_is_cut_around():
    room = {"polygon": [(0, 0), (6.0, 0), (6.0, 6.0), (0, 6.0)], "holes": [[(2.5, 2.5), (3.5, 2.5), (3.5, 3.5),
                                                                              (2.5, 3.5)]]}
    r = T.count_room(room, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["status"] == "RELEASED" and abs(r["net_m2"] - 35.0) < 1e-9
    assert r["tiles_to_buy"] >= math.ceil(35.0 / 0.36)


# ---- missing data: HELD, never 0 --------------------------------------------------------------------------------------

def test_missing_size_held_not_zero():
    r = T.count_room({"polygon": RECT, "room_id": "R9"}, units="m", size=None, exposure="INSIDE", offcut_reuse=False)
    assert r["status"] == "HELD" and r["tiles_to_buy"] is None and r["held_reason"].startswith("TILE_SIZE_NOT_GIVEN")
    assert r["location"]["room_id"] == "R9" and abs(r["net_m2"] - 7.2) < 1e-9


def test_missing_exposure_units_outline_held():
    assert T.count_room({"polygon": RECT}, units="m", size=S60)["held_reason"].startswith("JOINT_EXPOSURE_NOT_GIVEN")
    assert T.count_room({"polygon": RECT}, units="m", size=S60, exposure="attic")["held_reason"].startswith(
        "JOINT_EXPOSURE_UNKNOWN")
    r = T.count_room({"polygon": RECT}, units=None, size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["held_reason"].startswith("UNITS_NOT_GIVEN")
    r = T.count_room({"polygon": []}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert r["held_reason"].startswith("NO_ROOM_POLYGON")


def test_project_table_held_rooms_listed_never_zero():
    rel = T.count_room({"polygon": RECT}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    held = T.count_room({"polygon": RECT}, units="m", size=None, exposure="INSIDE", offcut_reuse=False)
    t = T.project_table([rel, held, held])
    assert t == {"rooms": 3, "released": 1, "held": 2, "held_by_reason": {"TILE_SIZE_NOT_GIVEN": 2},
                 "tiles_to_buy_released_rooms": 20, "complete": False}
    assert T.project_table([held])["tiles_to_buy_released_rooms"] is None


# ---- size sources and the printed-size census -------------------------------------------------------------------------

def test_resolve_size_order_and_holds():
    s, why = T.resolve_size(printed="بورسلان ١٢٠×٦٠ سم", project=size(0.6, 0.6, "PROJECT_DATA"))
    assert why is None and s["origin"] == "PRINTED" and (s["length_m"], s["width_m"]) == (1.2, 0.6)
    s, why = T.resolve_size(project={"length_m": 0.6, "width_m": 1.2, "source": "project data file row 4"})
    assert s["origin"] == "PROJECT_DATA" and (s["length_m"], s["width_m"]) == (1.2, 0.6)
    s, why = T.resolve_size()
    assert s is None and why.startswith("TILE_SIZE_NOT_GIVEN")
    s, why = T.resolve_size(printed="porcelain 60x60 and 120x60")
    assert s is None and why.startswith("TILE_SIZE_CONFLICT")
    s, why = T.resolve_size(printed="tile 45x45")
    assert s is None and why.startswith("TILE_SIZE_NOT_READ")
    with pytest.raises(ValueError):
        T.resolve_size(owner={"length_m": 0.6, "width_m": 0.6})            # an owner value needs its source


def test_parse_tile_size_units_and_digits():
    def one(t):
        r = T.parse_tile_size(t)
        assert len(r) == 1, t
        return r[0]
    a = one("PORCELAIN 60x60")
    assert (a["status"], a["length_m"], a["width_m"], a["unit"]) == ("RELEASED", 0.6, 0.6, "cm")
    assert a["concerns"] and a["concerns"][0].startswith("UNIT_NOT_PRINTED")
    b = one("600 X 600 mm")
    assert (b["length_m"], b["unit"], b["concerns"]) == (0.6, "mm", [])
    c = one("سيراميك ٣٠×٦٠ سم")
    assert (c["length_m"], c["width_m"], c["unit"]) == (0.6, 0.3, "cm")
    d = one("60x60 marble")                               # the 'm' of marble is not a metre unit
    assert d["unit"] == "cm" and d["length_m"] == 0.6
    assert one("tile 45x45")["status"] == "HELD"           # unitless and not an owner-approved size
    assert one("1600*800")["unit"] == "mm"
    assert T.parse_tile_size("+0.30") == [] and T.parse_tile_size("1:100") == []


def test_census_separates_tile_notes_from_other_sizes():
    texts = [{"text": "بلاط بورسلان 60x60", "sheet": "S1"}, {"text": "C1 60x60", "sheet": "S2"},
             {"text": "DOOR 90x210"}, {"text": "+0.15"}, {"text": "W.C"}]
    c = T.census(texts)
    assert c["texts_read"] == 5 and c["tile_size_notes"] == 1 and c["other_size_texts"] == 2
    kinds = [(r.get("sheet"), r["kind"]) for r in c["rows"]]
    assert kinds == [("S1", "TILE_SIZE_NOTE"), ("S2", "SIZE_WITHOUT_TILE_WORD"), (None, "SIZE_WITHOUT_TILE_WORD")]
    empty = T.census([{"text": "KITCHEN"}, {"text": "مطبخ"}])
    assert empty == {"texts_read": 2, "tile_size_notes": 0, "other_size_texts": 0, "rows": []}


def test_m2_line_is_not_touched():
    r = T.count_room({"polygon": RECT}, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    assert "stays m2" in r["m2_line_unchanged"] and "Q-42" in r["rule_refs"]


# ---- H7: offcut reuse is an owner input; not answered -> HELD with the upper bound ----------------------------------

H7 = {"polygon": [(0, 0), (3.3, 0), (3.3, 2.4), (0, 2.4)], "room_id": "H7"}


def test_h7_reuse_not_answered_is_held_with_upper_bound():
    r = T.count_room(H7, units="m", size=S60, exposure="INSIDE")
    assert r["status"] == "HELD" and r["tiles_to_buy"] is None
    assert r["held_reason"].startswith("OFFCUT_REUSE_NOT_ANSWERED") and r["offcut_reuse"] == "NOT_ANSWERED"
    assert r["upper_bound_no_reuse"] == 24 and len(r["layouts"]) == 8
    assert r["layouts"][0]["pieces_x_m"] == [0.6, 0.6, 0.6, 0.6, 0.6, 0.295]


def test_h7_no_reuse_and_reuse_from_20cm():
    a = T.count_room(H7, units="m", size=S60, exposure="INSIDE", offcut_reuse=False)
    b = T.count_room(H7, units="m", size=S60, exposure="INSIDE", offcut_reuse=0.20)
    la, lb = a["layouts"][0], b["layouts"][0]
    assert (la["whole_tiles"], la["cut_pieces"], la["tiles_to_buy"]) == (15, 9, 24)
    assert (lb["whole_tiles"], lb["cut_pieces"], lb["cut_from_offcuts"], lb["tiles_to_buy"]) == (15, 9, 2, 22)
    assert a["offcut_reuse"] == "NONE" and b["offcut_reuse"]["min_reusable_side_m"] == 0.2
    assert b["tiles_to_buy"] == 22 and b["upper_bound_no_reuse"] == 24
    with pytest.raises(ValueError):
        T.count_room(H7, units="m", size=S60, exposure="INSIDE", offcut_reuse=-0.1)
