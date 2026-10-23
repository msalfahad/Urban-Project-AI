"""T-223 method tests on a NON-Alsenan hand fixture (villa K223) with adverse cases.

Fixture K223: a 5.00 x 4.00 m room whose east wall is a concave curved bay: wall face an arc of R 2.00 m about a
centre 1.50 m east of the east line, at mid depth. By hand:
  half-angle acos(1.50 / 2.00) = 0.722734 rad -> sweep 1.445468 rad; chord 2 x 2.00 x sin(0.722734) = 2.645751 m;
  segment (R^2 / 2)(sweep - sin sweep) = 2 x (1.445468 - 0.992157) = 0.906624 m2;
  floor = 5.00 x 4.00 - 0.906624 = 19.093376 m2; perimeter 18.00 - 2.645751 + 2 x 1.445468 = 18.245186 m.
  The same bay bulging OUTWARD (centre 1.50 m inside the room): 20.906624 m2.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t223"))
sys.path.insert(0, str(ROOT / "research" / "agents_t218"))

import floor_typing as F                                               # noqa: E402
import wet_class_strips as WS                                          # noqa: E402

H = math.sqrt(2.0 ** 2 - 1.5 ** 2)                                     # 1.322876: half chord
HAND_AREA, HAND_PER, HAND_OUT = 19.093376, 18.245186, 20.906624


def ring(side=-1, k=1.0, radius=2.0, role="WALL", **extra):
    arc = {"p": (5 * k, (2 - H) * k), "kind": "ARC", "radius": radius, "side": side, "role": role, **extra}
    return [{"p": (0, 0)}, {"p": (5 * k, 0)}, arc, {"p": (5 * k, (2 + H) * k)}, {"p": (5 * k, 4 * k)},
            {"p": (0, 4 * k)}]


def test_arc_face_by_hand():
    v = F.face_area(ring())
    assert v["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)
    assert v["perimeter_m"] == pytest.approx(HAND_PER, abs=1e-6)
    a = v["arcs"][0]
    assert a["sense"] == "inward" and a["segment_m2"] == pytest.approx(0.9066, abs=1e-4)
    assert a["chord_m"] == pytest.approx(2.6458, abs=1e-4)


def test_outward_bay_adds_the_segment():
    assert F.face_area(ring(side=+1))["area_m2"] == pytest.approx(HAND_OUT, abs=1e-6)


def test_bulge_convention_equals_radius_convention():
    b = -math.tan(math.acos(0.75) / 2.0)          # DXF bulge = tan(sweep / 4), clockwise = negative
    r = ring()
    r[2] = {"p": r[2]["p"], "kind": "ARC", "bulge": b, "role": "WALL"}
    assert F.face_area(r)["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)


def test_mirror_rotation_and_reverse_ring():
    mir = [dict(e, p=(-e["p"][0], e["p"][1]), **({"side": -e["side"]} if "side" in e else {})) for e in ring()]
    assert F.face_area(mir)["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)
    rot = [dict(e, p=(-e["p"][1], e["p"][0])) for e in ring()]
    assert F.face_area(rot)["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)
    # the same ring walked the other way: the arc edge now runs from its far end, its sense reverses
    pts = [e["p"] for e in ring()]
    rev_pts = pts[::-1]                       # edges: (0,4)->(5,4)->(5,2+h)-ARC->(5,2-h)->(5,0)->(0,0)
    rev = [{"p": p} for p in rev_pts]
    rev[2] = {"p": rev_pts[2], "kind": "ARC", "radius": 2.0, "side": +1, "role": "WALL"}
    assert F.face_area(rev)["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)


def test_millimetres():
    mm = ring(k=1000.0, radius=2000.0)
    assert F.face_area(mm, unit="mm")["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)


def test_radius_in_the_wrong_unit_is_refused():
    with pytest.raises(F.Refused):
        F.face_area(ring(k=1000.0, radius=2.0), unit="mm")
    with pytest.raises(F.Refused):
        F.face_area(ring(), unit="ft")


def test_chord_instead_of_arc_is_refused():
    r = ring()
    r[2] = {"p": r[2]["p"], "kind": "ARC", "role": "WALL"}          # end points only
    with pytest.raises(F.Refused):
        F.face_area(r)
    c = F.chord_reading_refused(ring())
    assert c["status"] == "REFUSED" and c["area_m2"] == pytest.approx(20.0)   # never the quantity


def test_glazing_line_as_wall_face_needs_a_wall_on_the_same_curve():
    with pytest.raises(F.Refused):
        F.face_area(ring(role="GLAZING"))
    ok = F.face_area(ring(role="GLAZING", wall_on_same_curve=True))
    assert ok["area_m2"] == pytest.approx(HAND_AREA, abs=1e-6)


def test_missing_vertices_refused():
    with pytest.raises(F.Refused):
        F.face_area([{"p": (0, 0)}, {"p": (1, 0)}])


# ------------------------------------------------------------------------------------------------ space typing
def dressing(**kw):
    s = {"id": "K223-D", "label": None, "decision": None, "enclosed": True, "open_end_to_outside": False,
         "reached_from": ["DRY", "WET"], "fixtures": [], "drainage_checked": True, "stack_above_or_below": False,
         "floor_drawn_inside": True, "area_m2": 1.60 * 2.20,
         "boxes": [{"layer_role": "ANNOTATION", "has_wall_line": False, "counterpart_above_or_below": False}]}
    s.update(kw)
    return s


def test_enclosed_dressing_enters_the_internal_floor_line_dry_material_held():
    t = F.type_space(dressing())
    assert t["class"] == "INTERIOR" and t["floor_line"] == "FLOOR.INTERNAL" and t["wet_dry"] == "DRY"
    assert t["material_status"] == F.HELD and t["area_m2"] == 3.52 and t["area_status"] == F.DC
    assert len(t["joinery"]) == 1                                       # the box is joinery, floor continues


def test_wet_by_fixture_and_basin_alone_not_wet():
    assert F.type_space(dressing(fixtures=["WC"]))["wet_dry"] == "WET"
    t = F.type_space(dressing(fixtures=["BASIN"]))
    assert t["wet_dry"] is None and t["floor_line"].endswith("(class HELD)")
    t = F.type_space(dressing(drainage_checked=False))
    assert t["wet_dry"] is None                                         # no drain read: class HELD, never DRY


def test_shaft_with_a_stack_stays_out():
    t = F.type_space(dressing(stack_above_or_below=True, floor_drawn_inside=False))
    assert t["class"] == "SHAFT" and t["floor_line"] is None


def test_box_with_a_wall_line_or_a_counterpart_is_not_joinery():
    t = F.type_space(dressing(boxes=[{"layer_role": "ANNOTATION", "has_wall_line": False,
                                      "counterpart_above_or_below": True}]))
    assert t["class"] == F.UNKNOWN and t["floor_line"] is None and t["area_status"] == F.HELD
    t = F.type_space(dressing(boxes=[{"layer_role": "WALL", "has_wall_line": True,
                                      "counterpart_above_or_below": False}]))
    assert t["class"] == F.UNKNOWN


def test_open_end_without_decision_is_held_never_internal():
    t = F.type_space(dressing(enclosed=False, open_end_to_outside=True))
    assert t["class"] == "POSSIBLY_EXTERIOR" and t["floor_line"] is None and t["area_status"] == F.HELD


def test_bound_exterior_goes_to_the_outdoor_key():
    t = F.type_space(dressing(enclosed=False, open_end_to_outside=True,
                              decision={"class": "EXTERIOR", "source": "project decision X"}))
    assert t["class"] == "EXTERIOR" and t["floor_line"] == "FLOOR.OUTDOOR"


def test_not_enclosed_or_reached_from_outside_is_unknown():
    assert F.type_space(dressing(enclosed=None))["class"] == F.UNKNOWN
    assert F.type_space(dressing(reached_from=["EXTERIOR"]))["class"] == F.UNKNOWN


def test_missing_area_is_held_never_zero():
    t = F.type_space(dressing(area_m2=None))
    assert t["area_m2"] is None and t["area_status"] == F.HELD
    with pytest.raises(F.Refused):
        F.type_space(dressing(area_m2=-1.0))


# ------------------------------------------------------------------------------------------------- strips, pairing
def test_one_strip_in_floor_and_threshold_is_refused():
    lines = [{"line_id": "a", "opening_id": "K-OP-1", "item_code": "FIN.FLOOR.PORCELAIN", "covers_m2": 0.28},
             {"line_id": "b", "opening_id": "K-OP-1", "item_code": "ARCH.THRESHOLD", "covers_m2": 0.28}]
    with pytest.raises(WS.Refused):
        WS.assert_one_strip_one_line(lines)


def test_pairing_needs_both_keys_and_a_physical_reading():
    rd = [{"id": "area only", "m2": 19.0934, "lm": 17.0, "physical": True},
          {"id": "both", "m2": 19.0934, "lm": 18.245, "physical": True},
          {"id": "both but not drawn", "m2": 19.0934, "lm": 18.245, "physical": False},
          {"id": "missing", "m2": None, "lm": None, "physical": True}]
    p = F.pair_row(rd, 19.0934, 18.245)
    v = {r["id"]: r["verdict"] for r in p["readings"]}
    assert v == {"area only": "ONE KEY ONLY", "both": "PAIRED", "both but not drawn": "NOT A PAIRING",
                 "missing": "NOT A PAIRING"}
    assert p["paired"] == ["both"]
