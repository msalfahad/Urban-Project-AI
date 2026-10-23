"""T-204 LIFT_TANK_V1 on hand-calculated synthetic villa L (NOT Alsenan: a 1.60 x 2.00 pit, 0.25 walls, four 0.25 x 0.40
corner columns, one of them 0.35 deep standing 0.10 proud of the ring, a 3.10 x 3.40 x 0.60 base, printed pit height 1.35;
a drawn roof tank; other bars, other units).  Hand values are written out below with their arithmetic, not taken from
the module.  Regression guards (ENGINEERING_REASONING_STANDARD s.4 C), each with a normal and an adverse case:
  - pit height not printed -> every height-dependent row HELD with no value (never 0); plan rows still measured;
  - column sections in the ring counted again in the pit wall (double count with the neck / column line);
  - a closed '/m' loop (no column on the face) vs open runs between column faces (A .. B);
  - mirror, 90-degree turn and mm / m give the same results;
  - a tank with nothing drawn -> HELD placeholders with the designer item, never 0; a drawn tank measured;
  - input guards (overlapping columns, base smaller than the ring, height without its source, absence without search).
"""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("t204_lift_tank_v1_tests", ROOT / "research/agents_t204/lift_tank_v1.py")
LT = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LT)

KG12, KG10, KG16 = 144 / 162, 100 / 162, 256 / 162

VILLA_L = {
    "id": "LIFT-L", "unit": "m",
    "pit_inner": [0.25, 0.25, 1.85, 2.25], "pit_inner_ref": "villa L foundation plan, pit 1.60 x 2.00",
    "wall_t": 0.25, "wall_ref": "villa L pit section: RC walls 25 cm",
    "columns": [{"id": "SW", "rect": [0, 0, 0.25, 0.40], "ref": "L col 1"},
                {"id": "SE", "rect": [1.85, 0, 2.10, 0.40], "ref": "L col 2"},
                {"id": "NW", "rect": [0, 2.10, 0.25, 2.50], "ref": "L col 3"},
                {"id": "NE", "rect": [1.85, 2.10, 2.20, 2.50], "ref": "L col 4 (0.35 deep, 0.10 proud)"}],
    "base": {"id": "LB", "L": 3.10, "B": 3.40, "D": 0.60, "owner_line": "CONC.FOOTING LB", "ref": "L schedule LB"},
    "pit_height": 1.35, "pit_height_ref": "villa L section: pit 1.35 from the base top to the ring top",
    "detail": {"ref": "villa L lift pit detail", "state": "PROJECT",
               "vertical": {"n_per_m": 5, "d": 12, "faces": 2}, "horizontal": {"n_per_m": 5, "d": 10, "faces": 2},
               "membrane": True, "protection_board": True, "screed_t": 0.05},
    "tie_beams": {"rule_ref": "villa L note 7", "threshold": 4.30, "at": 3.00, "section": [0.20, 0.40],
                  "section_ref": "villa L tie beam 20 x 40",
                  "storeys": [{"storey": "GF", "height": 4.60, "ref": "L GF 4.60"},
                              {"storey": "1F", "height": 4.00, "ref": "L 1F 4.00"}]},
}


def rows(res):
    return {r["component"]: r for r in res["rows"]}


def val(res, comp):
    return rows(res)[comp]["value"]


# ---------------------------------------------------------------- normal case, hand values
def test_villa_l_plan_geometry():
    r = LT.lift_pit(VILLA_L)
    s = r["summary"]
    # gross ring 2.10 x 2.50 - 1.60 x 2.00 = 5.25 - 3.20 = 2.05 (= centreline 2 x (1.85 + 2.25) = 8.20 x 0.25)
    assert s["ring_gross_m2"] == pytest.approx(2.05)
    # columns in the band: SW / SE / NW 0.25 x 0.40 = 0.10 each; NE: only 1.85..2.10 of its 1.85..2.20 is in the band
    assert s["column_in_ring_m2"] == pytest.approx(0.40)
    assert val(r, "COLUMN_SECTION_IN_RING:NE") == pytest.approx(0.10)
    # net = 2.05 - 0.40 = 1.65; by wall segments 0.25 x (1.70 + 1.70 + 1.60 + 1.60) = 0.25 x 6.60
    assert s["ring_net_m2"] == pytest.approx(1.65)
    assert s["net_centreline_m"] == pytest.approx(6.60)
    # faces between column faces: W 1.70, E 1.70, S 1.60, N 1.60 on both faces
    assert s["face_run_inner_m"] == pytest.approx(6.60)
    assert s["face_run_outer_m"] == pytest.approx(6.60)
    # envelope = ring box 5.25 + NE proud part 0.10 x 0.40 = 5.29; outline 2 x (2.10 + 2.50) + 2 x 0.10 = 9.40
    assert s["envelope_m2"] == pytest.approx(5.29)
    assert s["envelope_outline_m"] == pytest.approx(9.40)


def test_villa_l_quantities_with_printed_height():
    r = LT.lift_pit(VILLA_L)
    assert val(r, "PIT_WALL_CONCRETE") == pytest.approx(1.65 * 1.35)            # 2.2275 m3
    assert val(r, "PIT_WALL_FORMWORK") == pytest.approx((6.60 + 6.60) * 1.35)   # 17.82 m2
    assert val(r, "MEMBRANE_BASE_SOFFIT") == pytest.approx(3.10 * 3.40)        # 10.54
    assert val(r, "MEMBRANE_BASE_SIDES") == pytest.approx(2 * (3.10 + 3.40) * 0.65)  # 8.45
    assert val(r, "MEMBRANE_BASE_TOP_OUTSIDE_PIT") == pytest.approx(10.54 - 5.29)    # 5.25
    assert val(r, "MEMBRANE_PIT_OUTER_FACES") == pytest.approx(9.40 * 1.35)    # 12.69
    assert val(r, "PROTECTION_BOARD_BASE") == pytest.approx(8.45 + 5.25)
    assert val(r, "SCREED_UNDER_BASE") == pytest.approx(10.54 * 0.05)          # 0.527
    assert val(r, "PIT_BASE") == pytest.approx(3.10 * 3.40 * 0.60)            # listed only
    assert rows(r)["PIT_BASE"]["listed_only"] is True
    # tie beams: GF 4.60 > 4.30 -> 6.60 m x 0.20 x 0.40 = 0.528; 1F 4.00 -> not required, no value
    assert val(r, "TIE_BEAMS_LENGTH:GF") == pytest.approx(6.60)
    assert val(r, "TIE_BEAMS_CONCRETE:GF") == pytest.approx(0.528)
    assert rows(r)["TIE_BEAMS:1F"]["status"] == "NOT_REQUIRED" and rows(r)["TIE_BEAMS:1F"]["value"] is None


def test_villa_l_bar_counts_open_runs():
    r = LT.lift_pit(VILLA_L)
    v = rows(r)["BARS_VERTICAL"]
    # per face, runs 1.70, 1.70, 1.60, 1.60 at 5/m: C 5 x 6.60 = 33.0; A 9 + 9 + 8 + 8 = 34; B 10 + 10 + 9 + 9 = 38
    assert v["count_inner"]["C"] == pytest.approx(33.0)
    assert (v["count_inner"]["A"], v["count_inner"]["B"]) == (34, 38)
    assert v["count_inner"]["closed_loop"] is False
    assert v["kg_per_m_of_height"]["A"] == pytest.approx(68 * KG12)
    assert v["kg_per_m_of_height"]["B"] == pytest.approx(76 * KG12)
    assert v["status"] == "HELD" and v["value"] is None      # anchorage never printed here: never released
    h = rows(r)["BARS_HORIZONTAL"]
    assert h["kg_per_m_of_height"] == pytest.approx(5 * 13.20 * KG10)   # 40.7407 kg per metre of height


# ---------------------------------------------------------------- adverse cases
def test_missing_pit_height_is_held_never_zero():
    sp = copy.deepcopy(VILLA_L)
    sp["pit_height"] = None
    r = LT.lift_pit(sp)
    rr = rows(r)
    for comp in ("PIT_WALL_CONCRETE", "PIT_WALL_FORMWORK", "MEMBRANE_PIT_OUTER_FACES", "PROTECTION_BOARD_WALLS"):
        assert rr[comp]["status"] == "HELD", comp
        assert rr[comp]["value"] is None, comp
        assert "pit height" in rr[comp]["missing"]
    # plan facts and the base-only membrane stay measured
    assert rr["PIT_RING_PLAN_NET"]["value"] == pytest.approx(1.65)
    assert rr["MEMBRANE_BASE_SOFFIT"]["value"] == pytest.approx(10.54)
    assert all(x["value"] is None for x in r["rows"] if x["status"] == "HELD")


def test_column_sections_are_not_counted_twice():
    r = LT.lift_pit(VILLA_L)
    # adverse: the same pit with its columns forgotten would bill the column sections again in the wall
    sp = copy.deepcopy(VILLA_L)
    sp["columns"] = []
    r0 = LT.lift_pit(sp)
    assert r0["summary"]["ring_net_m2"] == pytest.approx(2.05)
    assert r0["summary"]["ring_net_m2"] - r["summary"]["ring_net_m2"] == pytest.approx(0.40)   # the double count
    assert val(r0, "PIT_WALL_CONCRETE") - val(r, "PIT_WALL_CONCRETE") == pytest.approx(0.40 * 1.35)


def test_ring_without_columns_is_a_closed_loop():
    sp = copy.deepcopy(VILLA_L)
    sp["columns"] = []
    v = rows(LT.lift_pit(sp))["BARS_VERTICAL"]
    # inner perimeter 2 x (1.60 + 2.00) = 7.20 at 5/m = 36.0 exactly: A = B = 36 (no end bar on a loop)
    assert v["count_inner"]["closed_loop"] is True
    assert v["count_inner"]["C"] == pytest.approx(36.0)
    assert v["count_inner"]["A"] == v["count_inner"]["B"] == 36
    # outer 2 x (2.10 + 2.50) = 9.20 -> 46.0 -> 46
    assert v["count_outer"]["A"] == v["count_outer"]["B"] == 46


def _mirror_x(sp):
    m = copy.deepcopy(sp)
    f = lambda r: [-r[2], r[1], -r[0], r[3]]  # noqa: E731
    m["pit_inner"] = f(m["pit_inner"])
    for c in m["columns"]:
        c["rect"] = f(c["rect"])
    return m


def _turn_90(sp):
    m = copy.deepcopy(sp)
    f = lambda r: [-r[3], r[0], -r[1], r[2]]  # noqa: E731  (x, y) -> (-y, x)
    m["pit_inner"] = f(m["pit_inner"])
    for c in m["columns"]:
        c["rect"] = f(c["rect"])
    return m


def _to_mm(sp):
    m = copy.deepcopy(sp)
    m["unit"] = "mm"
    s = lambda r: [round(v * 1000, 6) for v in r]  # noqa: E731
    m["pit_inner"] = s(m["pit_inner"])
    m["wall_t"] = 250
    for c in m["columns"]:
        c["rect"] = s(c["rect"])
    m["base"].update(L=3100, B=3400, D=600)
    m["pit_height"] = 1350
    m["detail"]["screed_t"] = 50
    m["tie_beams"].update(threshold=4300, at=3000, section=[200, 400])
    for st in m["tie_beams"]["storeys"]:
        st["height"] = round(st["height"] * 1000)
    return m


@pytest.mark.parametrize("tf", [_mirror_x, _turn_90, _to_mm], ids=["mirror", "turn90", "mm"])
def test_transforms_and_units_leave_results_unchanged(tf):
    a = LT.lift_pit(VILLA_L)
    b = LT.lift_pit(tf(VILLA_L))
    for k in ("ring_gross_m2", "ring_net_m2", "column_in_ring_m2", "face_run_inner_m", "face_run_outer_m",
              "envelope_m2", "envelope_outline_m"):
        assert b["summary"][k] == pytest.approx(a["summary"][k]), k
    ra, rb = rows(a), rows(b)
    for comp in ("PIT_WALL_CONCRETE", "PIT_WALL_FORMWORK", "MEMBRANE_BASE_TOP_OUTSIDE_PIT", "TIE_BEAMS_CONCRETE:GF"):
        assert rb[comp]["value"] == pytest.approx(ra[comp]["value"]), comp
    assert rb["BARS_VERTICAL"]["count_inner"]["A"] == ra["BARS_VERTICAL"]["count_inner"]["A"]


def test_column_into_pit_is_flagged():
    sp = copy.deepcopy(VILLA_L)
    sp["columns"][0]["rect"] = [0, 0, 0.35, 0.40]   # 0.10 into the pit clear space
    r = LT.lift_pit(sp)
    assert any(f["code"] == "COLUMN_INTO_PIT" and f["column"] == "SW" for f in r["findings"])


def test_no_base_is_held_not_zero():
    sp = copy.deepcopy(VILLA_L)
    sp["base"] = None
    sp["detail"]["membrane"] = sp["detail"]["protection_board"] = False
    sp["detail"]["screed_t"] = None
    r = LT.lift_pit(sp)
    assert rows(r)["PIT_BASE"]["status"] == "HELD" and rows(r)["PIT_BASE"]["value"] is None
    assert any(f["code"] == "PIT_BASE_NOT_DRAWN" for f in r["findings"])


def test_tie_beam_section_not_printed_is_held():
    sp = copy.deepcopy(VILLA_L)
    sp["tie_beams"]["section"] = None
    r = LT.lift_pit(sp)
    assert rows(r)["TIE_BEAMS_LENGTH:GF"]["value"] == pytest.approx(6.60)
    t = rows(r)["TIE_BEAMS_CONCRETE:GF"]
    assert t["status"] == "HELD" and t["value"] is None and "section" in t["missing"]


@pytest.mark.parametrize("mut, msg", [
    (lambda s: s["columns"].append({"id": "X", "rect": [0, 0, 0.10, 0.10], "ref": "x"}), "overlap"),
    (lambda s: s["base"].update(L=1.0), "smaller than the pit ring"),
    (lambda s: s.update(pit_height_ref=None), "pit_height_ref"),
    (lambda s: s.update(unit="ft"), "unit"),
    (lambda s: s.update(wall_t=None), "wall_t"),
    (lambda s: s.update(pit_inner=[1, 1, 0, 0]), "x1 > x0"),
    (lambda s: s["columns"][1].update(ref=""), "ref required"),
    (lambda s: s.update(pit_height=0), "pit_height"),
])
def test_input_guards(mut, msg):
    sp = copy.deepcopy(VILLA_L)
    mut(sp)
    with pytest.raises(ValueError, match=msg):
        LT.lift_pit(sp)


def test_unit_mass_rule():
    assert LT.kg_per_m(16) == pytest.approx(KG16)
    assert LT.kg_per_m(12) == pytest.approx(KG12)


# ---------------------------------------------------------------- tank
TANK_L = {"id": "TANK-L", "unit": "m", "place_ref": "villa L roof plan tank", "searched": "villa L all sheets",
          "supporting_slab_lines": ["SLAB R-03"],
          "walls": {"inner": [0, 0, 2.00, 1.50], "t": 0.20, "height": 1.50, "ref": "villa L tank section"},
          "base": "ROOF_SLAB",
          "cover": {"area": 2.40 * 1.90, "t": 0.15, "openings": [0.36], "ref": "villa L tank cover"}}


def test_drawn_tank_measured():
    r = LT.tank(TANK_L)
    rr = rows(r)
    # ring 2.40 x 1.90 - 2.00 x 1.50 = 4.56 - 3.00 = 1.56 x 1.50 = 2.34
    assert rr["TANK_WALLS"]["value"] == pytest.approx(2.34)
    # cover (4.56 - 0.36) x 0.15 = 0.63
    assert rr["TANK_COVER"]["value"] == pytest.approx(0.63)
    assert rr["TANK_BASE"]["status"] == "LISTED" and rr["TANK_BASE"]["value"] is None
    assert r["missing"] == [] and r["designer_item"] is None


def test_undrawn_tank_is_held_with_designer_item():
    sp = dict(TANK_L, walls=None, base=None, cover=None, designer_item="tank type, size and supports")
    r = LT.tank(sp)
    assert r["missing"] == ["walls", "base", "cover"]
    held = [x for x in r["rows"] if x["status"] == "HELD"]
    assert len(held) == 3 and all(x["value"] is None for x in held)
    assert r["designer_item"] == "tank type, size and supports"
    # adverse: missing parts without a designer item, or an absence without the sheets searched, are refused
    with pytest.raises(ValueError, match="designer_item"):
        LT.tank(dict(TANK_L, walls=None))
    with pytest.raises(ValueError, match="searched"):
        LT.tank(dict(TANK_L, searched=""))
