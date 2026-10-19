"""T-013: section / elevation level bands bound to plan floors (engine/source/section_binding.py), against hand truth.

Hand drawing (metres, not a client drawing). Three plan sheets, each one room with its level printed inside:
    GF box x 100..120, room (101,1)-(110,9), '+0.60';  1F box x 130..150, '+4.10';  2F box x 160..180, '+7.60'.
SECTION A-A (box x 0..20, y -2..16; datum 0.00 at y = 0, full size, y up). Level labels at x = 2, 0.15 above their
line: 'F.F.L. +0.60', 'F.F.L. +4.10', 'F.F.L. +7.60'. The floor names are drawn 0.50 BELOW their line (outside their
own band): 'GROUND FLOOR' (2, 0.10), 'FIRST FLOOR' (2, 3.60), 'SECOND FLOOR' (2, 7.10). Far side, x = 12:
'U/S SLAB +3.75', 'F.C.L. +3.40', 'T.O.S. +3.95'; 'C.H. 2.80' at (8, 2.0); '±0.00' at (16, 0.15).
Vertical dimension chain at x = 18: 0.00-0.60 (600), 0.60-4.10 (3500), 7.60-11.10 (3500). No 4.10-7.60 dimension.
Hand results:
    names: each name's nearest label is its own floor's (0.65 m); the next label is 3.50 m away -> 3 NAME bindings
    GF  floor-to-floor 3.50 PRINTED_DIMENSION (the 3500 joins +0.60 and +4.10)
        soffit 3.75 - 0.60 = 3.15; false ceiling 3.40 - 0.60 = 2.80; next slab top 3.95 - 0.60 = 3.35;
        slab 3.95 - 3.75 = 0.20 PRINTED_LEVELS (the drawing overrides the owner's 0.16); clear height 2.80 PRINTED
    1F  floor-to-floor 7.60 - 4.10 = 3.50 DERIVED_FROM_PRINTED_LEVELS; slab 0.16 OWNER_RULE (Q-14); soffit NOT_PRINTED
    2F  no floor above: floor-to-floor HELD; level above +11.10 (3.50) HELD, kind not printed
V2.8 (arch_v28.read_views) on the same view puts 'FIRST FLOOR' (y 3.60 -> level 3.45) inside the GF band and binds
the +0.60 band to 1F: the defect this module answers (shown, not changed).
Variants: millimetres, centimetres, mirrored, rotated 90 degrees (no calibration: name and value bindings only).
Adversarial: split-level storey with a wrong dominant plan level, bare level marks with the CAD '%%p' sign and a text
offset, a stale dimension, a name next to the wrong level, an ambiguous name, a value printed on two floors, two names
on one level, Arabic names, a floor with no printed level (held, never 0).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engine.source import arch_v28 as V28  # noqa: E402
from engine.source import section_binding as SB  # noqa: E402


def _ident(p):
    return p


def _mirror(p):
    return (-p[0], p[1])


def _rot90(p):
    return (-p[1], p[0])


class Drawing:
    """a metre spec turned into drawing records in unit_m, through a point transform."""

    def __init__(self, unit_m=1.0, tf=_ident):
        self.u, self.tf = unit_m, tf
        self.texts, self.dims, self.frames, self.plans = [], [], [], []
        self.n = 0

    def pt(self, p):
        q = self.tf(p)
        return (q[0] / self.u, q[1] / self.u)

    def box(self, x0, y0, x1, y1):
        cs = [self.pt(c) for c in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
        return [min(c[0] for c in cs), min(c[1] for c in cs), max(c[0] for c in cs), max(c[1] for c in cs)]

    def text(self, value, x, y):
        self.n += 1
        q = self.pt((x, y))
        self.texts.append({"id": f"T{self.n}", "value": value, "x": q[0], "y": q[1], "layer": "A"})

    def vdim(self, x, lo, hi, shown=None):
        self.n += 1
        a, b = self.pt((x, lo)), self.pt((x, hi))
        d = self.tf((0.0, 1.0))
        ang = math.degrees(math.atan2(d[1], d[0])) % 360.0
        geom = math.dist(a, b)
        self.dims.append({"handle": f"D{self.n}", "type": "LINEAR", "layer": "DIM", "p1": list(self.pt((x + 0.5, hi))),
                          "p2": list(a), "p3": list(b), "angle": ang, "dimstyle": "S", "style_dimlfac": None,
                          "override_dimlfac": None, "measurement": geom, "text": "",
                          "shown_text": shown if shown is not None else f"{geom:.4g}"})

    def frame(self, x0, y0, x1, y1):
        self.frames.append({"box": self.box(x0, y0, x1, y1)})

    def plan(self, floor, x0, rooms, dominant=None):
        """rooms: [(room_id, kind, (rx0, ry0, rx1, ry1), [level texts inside])] in the plan's local metres."""
        b = self.box(x0, 0, x0 + 20, 10)
        rr = []
        for rid, kind, (a0, b0, a1, b1), lvls in rooms:
            poly = [self.pt((x0 + a0, b0)), self.pt((x0 + a1, b0)), self.pt((x0 + a1, b1)), self.pt((x0 + a0, b1))]
            rr.append({"room_id": rid, "kind": kind, "polygon": [list(p) for p in poly]})
            for i, v in enumerate(lvls):
                self.text(v, x0 + (a0 + a1) / 2 + 0.3 * i, (b0 + b1) / 2)
        self.plans.append({"floor": floor, "box": b, "dominant_level_m": dominant, "rooms": rr})

    def bind(self):
        return SB.bind(self.texts, self.dims, None, self.frames, self.u, self.plans)


def three_storeys(unit_m=1.0, tf=_ident):
    D = Drawing(unit_m, tf)
    D.plan("GF", 100, [("GF-R1", "DRY", (1, 1, 10, 9), ["+0.60"])], 0.60)
    D.plan("1F", 130, [("1F-R1", "DRY", (1, 1, 10, 9), ["+4.10"])], 4.10)
    D.plan("2F", 160, [("2F-R1", "DRY", (1, 1, 10, 9), ["+7.60"])], 7.60)
    D.frame(0, -2, 20, 16)
    D.text("SECTION A-A", 8, -1.5)
    for v in (0.60, 4.10, 7.60):
        D.text(f"F.F.L. +{v:.2f}", 2, v + 0.15)
    D.text("GROUND FLOOR", 2, 0.10)
    D.text("FIRST FLOOR", 2, 3.60)
    D.text("SECOND FLOOR", 2, 7.10)
    D.text("U/S SLAB +3.75", 12, 3.90)
    D.text("F.C.L. +3.40", 12, 3.55)
    D.text("T.O.S. +3.95", 12, 4.30)
    D.text("C.H. 2.80", 8, 2.0)
    D.text("%%p0.00", 16, 0.15)
    D.vdim(18, 0.0, 0.60)
    D.vdim(18, 0.60, 4.10)
    D.vdim(18, 7.60, 11.10)
    return D


def _zone(out, fl, i=0):
    return out["floors"][fl]["zones"][i]


def _check_three(out, calibrated=True):
    (view,) = out["views"]
    assert [(b["floor"], b["ffl_m"], b["binding"]) for b in view["bands"]] == [
        ("GF", 0.6, "NAME_NEAREST_LEVEL_LABEL"), ("1F", 4.1, "NAME_NEAREST_LEVEL_LABEL"),
        ("2F", 7.6, "NAME_NEAREST_LEVEL_LABEL")]
    for b in view["bands"]:
        assert b["evidence"]["distance_m"] == pytest.approx(0.65, abs=1e-6)
        assert b["evidence"]["plan_check"] == "AGREES_WITH_A_ROOM_LEVEL"
    gf, f1, f2 = _zone(out, "GF"), _zone(out, "1F"), _zone(out, "2F")
    assert gf["ffl"]["value_m"] == 0.6 and gf["ffl"]["state"] == "PRINTED" and gf["ffl"]["rooms"] == ["GF-R1"]
    assert gf["soffit"]["value_m"] == pytest.approx(3.15) and gf["soffit"]["state"] == "PRINTED"
    assert gf["false_ceiling"]["value_m"] == pytest.approx(2.80)
    assert gf["next_slab_top"]["value_m"] == pytest.approx(3.35)
    assert gf["slab_thickness"]["value_m"] == pytest.approx(0.20) and gf["slab_thickness"]["state"] == "PRINTED_LEVELS"
    assert f1["floor_to_floor"]["state"] == "DERIVED_FROM_PRINTED_LEVELS"
    assert f1["floor_to_floor"]["value_m"] == pytest.approx(3.50)
    assert f1["slab_thickness"] == dict(f1["slab_thickness"], value_m=0.16, state="OWNER_RULE")
    assert f1["soffit"] == {"value_m": None, "state": "NOT_PRINTED"}
    assert f2["floor_to_floor"]["value_m"] is None and f2["floor_to_floor"]["why"] == "NO_FLOOR_ABOVE"
    for z in (gf, f1, f2):
        assert z["floor_to_floor"].get("never_wall_height", True)
    if calibrated:
        assert view["calibration"]["state"] == "CALIBRATED"
        assert view["calibration"]["values_on_dimension_ends"] == [0.0, 0.6, 4.1, 7.6]
        assert gf["floor_to_floor"]["state"] == "PRINTED_DIMENSION"
        assert gf["floor_to_floor"]["value_m"] == pytest.approx(3.50)
        assert gf["clear_height"]["value_m"] == pytest.approx(2.80) and gf["clear_height"]["state"] == "PRINTED"
        la = f2["level_above"]
        assert la["state"] == "HELD" and la["why"].startswith("LEVEL_ABOVE_KIND_NOT_PRINTED")
        assert [(c["level_m"], c["height_m"]) for c in la["candidates"]] == [(11.1, pytest.approx(3.5))]
    else:
        assert view["calibration"]["state"] == "VIEW_NOT_CALIBRATED"
        assert gf["floor_to_floor"]["state"] == "DERIVED_FROM_PRINTED_LEVELS"
        assert gf["floor_to_floor"]["value_m"] == pytest.approx(3.50)
        assert gf["clear_height"] == {"value_m": None, "state": "NOT_PRINTED"}
        assert f2["level_above"]["state"] == "NOT_PRINTED" and f2["level_above"]["candidates"] == []


@pytest.mark.parametrize("unit_m", [1.0, 0.01, 0.001])
def test_three_storeys_units(unit_m):
    _check_three(three_storeys(unit_m).bind())


@pytest.mark.parametrize("unit_m", [1.0, 0.001])
def test_three_storeys_mirrored(unit_m):
    _check_three(three_storeys(unit_m, _mirror).bind())


def test_three_storeys_rotated_view_binds_by_name_only():
    _check_three(three_storeys(0.001, _rot90).bind(), calibrated=False)
    out = three_storeys(0.001, _rot90).bind()
    assert any(f["code"] == "VIEW_NOT_CALIBRATED" for f in out["findings"])


def test_v28_binds_the_name_below_its_line_to_the_band_below():
    """the defect: V2.8's in-band rule puts 'FIRST FLOOR' (0.50 below +4.10) in the GF band."""
    D = three_storeys()
    rv = V28.read_views(D.texts, D.frames, 1.0, {"GF": 0.6, "1F": 4.1, "2F": 7.6}, ["GF", "1F", "2F"])
    bands = {b["ffl_m"]: (b["floor"], b["binding"]) for b in rv["views"][0]["bands"]}
    assert bands[0.6] == ("1F", "FLOOR_NAME_ON_THE_BAND")
    assert bands[4.1] == ("2F", "FLOOR_NAME_ON_THE_BAND")
    out = D.bind()
    assert {b["ffl_m"]: b["floor"] for b in out["views"][0]["bands"]} == {0.6: "GF", 4.1: "1F", 7.6: "2F"}


def split_level(unit_m=0.001, tf=_ident):
    """GF: main rooms at +1.00, a street-side annex at +0.30; plot corner marks make the dominant plan level 0.00."""
    D = Drawing(unit_m, tf)
    D.plan("GF", 100, [("GF-MAIN", "DRY", (1, 1, 8, 9), ["+1.00", "+1.00"]), ("GF-ANNEX", "DRY", (10, 1, 15, 9),
                                                                          ["+0.30"]),
                       ("GF-YARD", "EXTERIOR", (16, 1, 19, 9), ["+0.15"])], 0.0)
    D.plan("1F", 130, [("1F-R1", "WET", (1, 1, 8, 9), ["+4.80"])], 4.80)
    D.frame(0, -3, 20, 12)
    D.text("SOUTH ELEVATION", 8, -2.5)
    for v, x in ((0.0, 1), (0.30, 4), (1.00, 7), (4.80, 7)):
        D.text("%%p0.00" if v == 0 else f"+{v:.2f}", x, v + 0.80)
    D.vdim(17, 0.0, 0.30)
    D.vdim(17, 0.30, 3.30)
    D.vdim(19, 0.0, 1.00)
    D.vdim(19, 1.00, 4.80)
    D.vdim(15, 0.0, 2.00, shown="9999")              # stale: shown value differs from the defpoints -> not read
    return D


@pytest.mark.parametrize("unit_m,tf", [(0.001, _ident), (1.0, _mirror), (0.01, _ident)])
def test_split_level_storey(unit_m, tf):
    out = split_level(unit_m, tf).bind()
    fl = out["floor_levels"]["GF"]
    assert fl["how"] == "SPLIT_LEVEL" and [z["level_m"] for z in fl["zones"]] == [0.3, 1.0]
    assert {"code": "PLAN_DOMINANT_LEVEL_IS_NOT_A_ROOM_LEVEL", "floor": "GF", "dominant_level_m": 0.0,
            "room_levels_m": [0.3, 1.0]} in out["findings"]
    (view,) = out["views"]
    assert view["calibration"]["values_on_dimension_ends"] == [0.0, 0.3, 1.0, 4.8]
    assert all(abs(l["value_m"] - 2.0) > 1e-6 for l in view["levels"])           # the stale dimension gives nothing
    assert [(b["floor"], b["ffl_m"]) for b in view["bands"]] == [("GF", 0.3), ("GF", 1.0), ("1F", 4.8)]
    annex, main = _zone(out, "GF", 0), _zone(out, "GF", 1)
    assert annex["ffl"]["rooms"] == ["GF-ANNEX"] and main["ffl"]["rooms"] == ["GF-MAIN"]
    assert main["floor_to_floor"]["state"] == "PRINTED_DIMENSION"
    assert main["floor_to_floor"]["value_m"] == pytest.approx(3.80)
    assert annex["floor_to_floor"]["value_m"] is None
    assert annex["floor_to_floor"]["why"].startswith("SPLIT_LEVEL_ZONE")
    assert [(c["level_m"], c["height_m"]) for c in annex["level_above"]["candidates"]] == [
        (3.3, pytest.approx(3.0))]
    assert main["soffit"]["state"] == "HELD"                                      # two GF zones in one view
    top = _zone(out, "1F")
    assert top["level_above"] == dict(top["level_above"], state="NOT_PRINTED", candidates=[])


def test_name_next_to_the_wrong_level_is_a_conflict():
    D = three_storeys()
    D.texts = [t for t in D.texts if t["value"] != "FIRST FLOOR"]
    D.text("FIRST FLOOR", 2, 0.10 + 0.30)            # beside +0.60, which is the GF room level
    out = D.bind()
    assert any(f["code"] == "NAME_LEVEL_CONFLICT" and f["floor"] == "1F" and f["label_value_m"] == 0.6
               for f in out["findings"])
    bands = {b["ffl_m"]: (b["floor"], b["binding"]) for b in out["views"][0]["bands"]}
    assert bands[0.6] == ("GF", "NAME_NEAREST_LEVEL_LABEL")
    assert bands[4.1] == ("1F", "LEVEL_EQUALS_A_ROOM_LEVEL")                     # the value still binds it


def test_ambiguous_name_binds_nothing():
    D = three_storeys()
    D.texts = [t for t in D.texts if t["value"] != "FIRST FLOOR"]
    D.text("FIRST FLOOR", 1.0, (0.75 + 4.25) / 2)      # halfway between the +0.60 and +4.10 labels: 2.016 m each
    out = D.bind()
    assert any(f["code"] == "NAME_AMBIGUOUS" and f["values_m"] == [0.6, 4.1] for f in out["findings"])
    bands = {b["ffl_m"]: b["binding"] for b in out["views"][0]["bands"]}
    assert bands[4.1] == "LEVEL_EQUALS_A_ROOM_LEVEL"


def test_two_names_on_one_level():
    """a second name at +7.60 for a storey with no plan (ROOF): no plan check can decide -> conflict, no binding.
    (A second name of a planned floor at the wrong level is a NAME_LEVEL_CONFLICT first.)"""
    D = three_storeys()
    D.text("ROOF", 2.6, 7.10)
    D.text("FIRST FLOOR", 2.4, 0.10)
    out = D.bind()
    assert any(f["code"] == "TWO_NAMES_ON_ONE_LEVEL" and f["floors"] == ["2F", "ROOF"] for f in out["findings"])
    assert any(f["code"] == "NAME_LEVEL_CONFLICT" and f["floor"] == "1F" for f in out["findings"])
    bands = {b["ffl_m"]: (b["floor"], b["binding"]) for b in out["views"][0]["bands"]}
    assert bands[7.6] == (None, "CONFLICT")
    assert bands[0.6] == ("GF", "NAME_NEAREST_LEVEL_LABEL")
    assert _zone(out, "2F")["ffl"]["confirmed_by_views"] == []


def test_value_printed_on_two_floors_binds_nothing():
    D = Drawing(1.0)
    D.plan("GF", 100, [("GF-R1", "DRY", (1, 1, 8, 9), ["+3.00"])])
    D.plan("1F", 130, [("1F-R1", "DRY", (1, 1, 8, 9), ["+3.00"])])
    D.frame(0, -2, 20, 10)
    D.text("SECTION B-B", 8, -1.5)
    D.text("+3.00", 2, 3.15)
    out = D.bind()
    assert out["views"][0]["bands"] == []
    assert any(f["code"] == "VALUE_ON_TWO_FLOORS" and f["floors"] == ["1F", "GF"] for f in out["findings"])
    assert any(f["code"] == "SECTION_BAND_NOT_BOUND" for f in out["findings"])


def test_arabic_floor_names():
    D = three_storeys()
    names = {"GROUND FLOOR": "الدور الأرضي", "FIRST FLOOR": "الدور الاول", "SECOND FLOOR": "الطابق الثاني"}
    for t in D.texts:
        t["value"] = names.get(t["value"], t["value"])
    _check_three(D.bind())
    assert SB.floor_name("الدور الثاني عشر") is None                           # the twelfth, not the second
    assert SB.floor_name("FIRST FLOOR PLAN 1:100") is None                      # a title, not a band name


def test_missing_floor_level_is_held_never_zero():
    D = Drawing(1.0)
    D.plan("GF", 100, [("GF-R1", "DRY", (1, 1, 8, 9), [])], None)
    D.plan("1F", 130, [("1F-R1", "DRY", (1, 1, 8, 9), ["+4.00"])], 4.0)
    D.frame(0, -2, 20, 10)
    D.text("SECTION C-C", 8, -1.5)
    D.text("+4.00", 2, 4.15)
    out = D.bind()
    assert out["floors"]["GF"]["state"] == "HELD" and out["floors"]["GF"]["zones"] == []
    assert {"code": "FLOOR_LEVEL_NOT_PRINTED", "floor": "GF"} in out["findings"]
    assert _zone(out, "1F")["floor_to_floor"]["value_m"] is None


def test_unlabelled_room_and_dominant_fallback():
    D = Drawing(1.0)
    D.plan("GF", 100, [("GF-U", None, (1, 1, 8, 9), ["+0.45"])], 0.45)   # unidentified space: its level does not count
    out = D.bind()
    assert out["floor_levels"]["GF"]["how"] == "PLAN_DOMINANT_LEVEL"
    assert _zone(out, "GF")["ffl"]["state"] == "PLAN_DOMINANT_LEVEL"
    assert {"code": "NO_LEVEL_IN_A_ROOM", "floor": "GF", "dominant_level_m": 0.45} in out["findings"]


def test_policy_record_never_list():
    p = SB.policy_record()
    assert p["owner_slab_m"] == 0.16
    assert "a floor-to-floor height taken as a wall height" in p["never"]
