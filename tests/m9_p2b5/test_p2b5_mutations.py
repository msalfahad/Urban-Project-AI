"""Phase 2B-5 (ARCH_TAKEOFF_V2.6): mutations and edge cases of the installation layer (Part 8 of the program).

Metamorphic: a translated, mirrored or rotated room (90 degrees and an arbitrary angle) keeps every quantity and every
count of the installation inventory; a renamed room changes nothing but its name. Edge cases: a door 10 cm narrower
moves 0.10 m from the doorway piece to the upturn and keeps the proven subtotal; a door next to a column; a doorway
listed twice is flagged, never silently double counted; conflicting project rules block the layout (no plan is made
up); a degenerate ring is blocked; a tiny room (a wrong scale) is computed without failure; a missing drain is
NOT_SHOWN; the offcut classes have exact boundaries."""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "m9_p2b2"))

import install_cases as IC                                    # noqa: E402
import install_engine as IE                                   # noqa: E402
import p2b2_fixtures as F                                     # noqa: E402

from engine.source import knowledge as K                      # noqa: E402
from engine.source import waterproofing_system as WS          # noqa: E402
from engine.source import wp_install as WI                    # noqa: E402

QTY = ("consumed_m2", "installed_m2", "laps_total_m2", "true_waste_m2", "reusable_m2", "stock_m2", "rolls",
       "floor_seams", "band_joints", "seams", "corners_internal", "corners_external", "jamb_butt_joints",
       "terminations", "t_flange_over_seam_end", "t_doorway_lap_over_seam_end", "proven_subtotal_m2")


def _fig(room, rid="M"):
    return IE.figures(IE.area(room, room_id=rid))


def _map(room, f, *, flip=False):
    """the room with every point mapped by f (mm); flip: the mapping mirrors, so each ring is reversed and the door
    positions measured along the reversed edges."""
    r = copy.deepcopy(room)
    r["poly"] = [f(p) for p in room["poly"]]
    r["holes"] = [[f(p) for p in h] for h in room.get("holes", ())]
    for k in ("pipes", "drains"):
        r[k] = [dict(x, **dict(zip(("x", "y"), f((x["x"], x["y"]))))) for x in room.get(k, ())]
    if flip:
        n = len(r["poly"])
        r["poly"] = r["poly"][::-1]
        r["holes"] = [h[::-1] for h in r["holes"]]
        for key in ("doors", "breaks"):
            new = []
            for d in room.get(key, ()):
                e = d["edge"]
                a, b = room["poly"][e], room["poly"][(e + 1) % n]
                ln = round(math.hypot(b[0] - a[0], b[1] - a[1]))
                new.append(dict(d, edge=(n - 2 - e) % n, t0=ln - d["t1"], t1=ln - d["t0"]))
            r[key] = new
    return r


@pytest.mark.parametrize("ex", [IC.IX02, IC.IX03, IC.IX05, IC.IX06, IC.IX07], ids=lambda x: x["id"])
def test_translation_mirror_and_rotation_keep_every_quantity(ex):
    base = _fig(ex["room"])
    tr = _fig(_map(ex["room"], lambda p: (p[0] + 50000, p[1] - 20000)))
    mi = _fig(_map(ex["room"], lambda p: (-p[0], p[1]), flip=True))
    r90 = _fig(_map(ex["room"], lambda p: (-p[1], p[0])))
    for other in (tr, mi, r90):
        assert {k: other[k] for k in QTY} == {k: base[k] for k in QTY}
    assert tr == base                                          # a translation changes nothing at all


def test_an_arbitrary_rotation_keeps_the_quantities():
    th = math.radians(27.0)
    ex = IC.IX02
    rot = _map(ex["room"], lambda p: (p[0] * math.cos(th) - p[1] * math.sin(th),
                                      p[0] * math.sin(th) + p[1] * math.cos(th)))
    base, other = _fig(ex["room"]), _fig(rot)
    for k in QTY:
        assert abs(other[k] - base[k]) < 1e-3, k


def test_a_renamed_room_changes_only_its_name():
    a, b = IE.area(IC.IX06["room"], room_id="KITCHEN-1"), IE.area(IC.IX06["room"], room_id="KITCHEN-RENAMED")
    assert IE.figures(a) == IE.figures(b)
    assert {p["id"] for p in a["v26"]["piece_plan"]["pieces"]} == {p["id"] for p in b["v26"]["piece_plan"]["pieces"]}


def test_a_door_ten_centimetres_narrower():
    r = copy.deepcopy(IC.IX02["room"])
    r["doors"][0]["t1"] -= 100
    a, b = _fig(IC.IX02["room"]), _fig(r)
    assert b["proven_subtotal_m2"] == a["proven_subtotal_m2"]      # +0.10 m upturn, -0.10 m doorway floor
    big, small = IE.area(IC.IX02["room"]), IE.area(r)
    assert round(small["boundary"]["eligible_lm"] - big["boundary"]["eligible_lm"], 6) == 0.1
    assert b["jamb_butt_joints"] == 2


def test_a_door_next_to_a_column():
    """a 0.40 x 0.40 column standing 0.05 m from the door's jamb: the column carries its own closed loop; the
    doorway's two jamb junctions are unchanged."""
    r = copy.deepcopy(IC.IX02["room"])
    r["holes"] = [[(2550, 50), (2950, 50), (2950, 450), (2550, 450)]]
    f = _fig(r)
    assert f["corners_external"] == 4 and f["jamb_butt_joints"] == 2
    a = IE.area(r)
    runs = a["v26"]["installation"]["runs"]
    assert [x["closed"] for x in runs] == [False, True]
    assert abs(a["v26"]["piece_plan"]["balance"]["consumed_m2"] - a["row"]["consumed_m2"]) < 1e-6


def test_a_doorway_listed_twice_is_flagged():
    r = copy.deepcopy(IC.IX02["room"])
    r["doors"] = r["doors"] + [dict(r["doors"][0])]
    a = IE.area(r)
    assert "DUPLICATE_DOORWAY_PIECE" in a["v26"]["flags"]
    assert a["v26"]["piece_plan"]["duplicate_doorways"] == ["D1"]


def _area_with(rules, ring=None, feats=None):
    U = IE.U
    ring = ring or [(0.0, 0.0), (4.0, 0.0), (4.0, 3.0), (0.0, 3.0)]
    rm = {"room_id": "R", "floor": "GF", "name_en": "R", "codes": ["BATHROOM"], "polygon_m": ring,
          "hole_polygons_m": [], "polygon": [(x / U, y / U) for x, y in ring], "hole_polygons": []}
    net = abs(sum(ring[i][0] * ring[(i + 1) % len(ring)][1] - ring[(i + 1) % len(ring)][0] * ring[i][1]
                  for i in range(len(ring)))) / 2
    with K.using("1.1.0"):
        a = WS.make_area(rm, F.walls(ring) if feats is None else feats, scope="WET", net_m2=net, ents={}, unit_m=U,
                         keep_segments=True)
        return WS.build_area(a, F.resolver(*rules), v26=True)


def test_conflicting_project_rules_block_the_layout():
    rules = [{"id": f"PR-{i}", "rule_id": "UP-WP-002", "parameter": "lap_m", "value": v, "scope": {"kind": "PROJECT"},
              "source": {"kind": "SPECIFICATION", "ref": f"sheet {i}"}} for i, v in ((1, 0.15), (2, 0.12))]
    a = _area_with(rules)
    assert a["layout"]["state"] == "BLOCKED" and a["v26"]["state"] == "BLOCKED"
    assert a["row"]["installation_state"] == "BLOCKED"


def test_a_degenerate_ring_is_blocked():
    a = _area_with([], ring=[(0.0, 0.0), (4.0, 0.0), (8.0, 0.0)], feats=[])
    assert a["v26"]["state"] == "BLOCKED" and a["v26"]["reason"].startswith("DEGENERATE_AREA")
    assert a["row"]["installation_state"] == "BLOCKED"


def test_a_tiny_room_from_a_wrong_scale_is_computed():
    r = {"poly": [(0, 0), (4, 0), (4, 3), (0, 3)], "doors": [], "breaks": [], "holes": [], "pipes": [], "drains": [],
         "codes": ["BATHROOM"], "scope": "WET"}
    a = IE.area(r)
    assert a["v26"]["state"] == "COMPUTED"
    assert a["v26"]["piece_plan"]["balance"]["closes"]


def test_a_wet_room_without_a_drawn_drain_is_not_shown():
    f = _fig(IC.IX02["room"])
    assert "DRAIN_NOT_SHOWN" in f["flags"] and f["lay_order"] is None
    a = IE.area(IC.IX02["room"])
    assert a["v26"]["installation"]["penetrations"]["drains"] == {"state": "NOT_SHOWN", "count": None}


@pytest.mark.parametrize("w,l,cls", [(0.3, 2.0, "REUSABLE_SUBJECT_TO_N7"), (0.2999, 2.0, "TRUE_WASTE"),
                                     (0.3, 0.1, "TRUE_WASTE"), (0.3, 0.1001, "REUSABLE_SUBJECT_TO_N7"),
                                     (None, None, "TRUE_WASTE")])
def test_offcut_class_boundaries(w, l, cls):
    assert WI.offcut_class(w, l, 0.3, 0.1, None) == cls


def test_offcut_classes_with_a_minimum_reusable_size():
    assert WI.offcut_class(0.3, 2.0, 0.3, 0.1, 0.5) == "WASTE_BY_N7"
    assert WI.offcut_class(0.8, 1.0, 0.3, 0.1, 0.5) == "RETAINED_BY_N7"


def test_an_internal_corner_count_follows_the_ring():
    f = _fig(IC.IX04["room"])
    assert (f["corners_internal"], f["corners_external"]) == (5, 1)


def _trims(room):
    a = IE.area(room)
    offs = a["v26"]["piece_plan"]["offcuts"]
    return a, [o for o in offs if o["id"].endswith(".o~")]


def test_a_wall_drawn_a_hair_off_square_is_not_a_shaped_trim():
    """one corner of a 3 x 4 bathroom 0.02 mm off square: the strip beside it falls short of its rectangle by
    0.5 x 4 x 0.00002 = 0.00004 m2 (below 1 cm2). That is drawing tolerance, never a cut: no shaped-trim flag, and the
    sliver stays in the balance (the plan still closes)."""
    r = {"poly": [(0, 0), (3000, 0), (3000.02, 4000), (0, 4000)], "doors": [], "breaks": [], "holes": [],
         "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"}
    a, trims = _trims(r)
    assert "SHAPED_TRIM_NOT_DECOMPOSED" not in a["v26"]["flags"]
    assert a["v26"]["piece_plan"]["shaped_trims"] == 0
    assert all(o["why"] == "drawing tolerance at the wall line" and o["class"] == "TRUE_WASTE" for o in trims)
    assert a["v26"]["piece_plan"]["balance"]["closes"]


def test_a_splayed_corner_is_a_shaped_trim():
    """a 3 x 4 bathroom with one corner cut at 45 degrees from (3.0, 3.5) to (2.5, 4.0): outside the room is
    x + y > 6.5. The strips run along x (3.0 m) across y, 1.0 m wide at 0.90 m pitch: strip 4 spans y 2.70-3.70 over
    x 0-3.00 and is trimmed over y 3.50-3.70 by a width y - 3.50 (integral 0.02 m2); strip 5 (0.40 m, y 3.60-4.00)
    reaches x 6.5 - 3.6 = 2.90 and is trimmed by a width y - 3.60 (integral 0.08 m2). The plan does not decompose a
    triangle into rectangles: both trims are flagged, never hidden."""
    r = {"poly": [(0, 0), (3000, 0), (3000, 3500), (2500, 4000), (0, 4000)], "doors": [], "breaks": [], "holes": [],
         "pipes": [], "drains": [], "codes": ["BATHROOM"], "scope": "WET"}
    a, trims = _trims(r)
    assert "SHAPED_TRIM_NOT_DECOMPOSED" in a["v26"]["flags"]
    assert {o["id"]: o["area_m2"] for o in trims} == {"S4.o~": 0.02, "S5.o~": 0.08}
    assert all(o["why"] == "trim at a splayed wall (shaped)" for o in trims)
    assert a["v26"]["piece_plan"]["balance"]["closes"]
