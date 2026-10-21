"""T-004a: the label census (tools/label_census.py) against hand truth on synthetic plans (no private drawing).

Hand truth: a 4.40 x 3.40 m shell (0.20 m walls) split by a 0.20 m partition into two closed rooms, west BEDROOM
(1.90 x 3.00 = 5.70 m2) and east KITCHEN (1.90 x 3.00 = 5.70 m2). Planted: a COURT label drawn 1.6 m outside the
shell (in no room: the silent omission the census must find), one Arabic SHX text in an unmapped font inside the
plan (counted UNREAD_SHX, never guessed), one BEDROOM text outside the sheet frame (out of scope: not counted).
Variants: millimetres, metres, the plan rotated 37 degrees, mirrored. The unit tests feed the pure census hand-built
records for the cases a real run does not give cheaply (held, excluded, code mismatch, no coverage record, holes)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tools import label_census as LC                         # noqa: E402

W, TXT = "A-WALL", "A-TEXT"
ROLES = {"A-WALL": "WALL"}
C = (2200.0, 1700.0)


def _xf(p, deg, mirror):
    x, y = p
    if mirror:
        x = 2 * C[0] - x
    a = math.radians(deg)
    dx, dy = x - C[0], y - C[1]
    return (C[0] + dx * math.cos(a) - dy * math.sin(a), C[1] + dx * math.sin(a) + dy * math.cos(a))


def plan(path, *, scale=1.0, deg=0.0, mirror=False):
    import ezdxf
    doc = ezdxf.new("R2018")
    doc.header["$INSUNITS"] = 4 if scale == 1.0 else 6
    doc.styles.add("ARSHX", font="x-arab.shx")
    for n in (W, TXT, "A-FRAME", "A-TITLE"):
        doc.layers.add(n)
    msp = doc.modelspace()
    s = lambda p: tuple(v * scale for v in _xf(p, deg, mirror))     # noqa: E731
    box = [(-8000, -9000), (14000, -9000), (14000, 12000), (-8000, 12000)]
    msp.add_lwpolyline([(x * scale, y * scale) for x, y in box], close=True, dxfattribs={"layer": "A-FRAME"})
    msp.add_text("GROUND FLOOR PLAN", dxfattribs={"layer": "A-TITLE", "height": 500 * scale}).set_placement(
        (-6000 * scale, -8000 * scale))
    segs = [((0, 0), (4400, 0)), ((4400, 0), (4400, 3400)), ((4400, 3400), (0, 3400)), ((0, 3400), (0, 0)),
            ((200, 200), (2100, 200)), ((2100, 200), (2100, 3200)), ((2100, 3200), (200, 3200)),
            ((200, 3200), (200, 200)),
            ((2300, 200), (4200, 200)), ((4200, 200), (4200, 3200)), ((4200, 3200), (2300, 3200)),
            ((2300, 3200), (2300, 200))]
    for a, b in segs:
        msp.add_line(s(a), s(b), dxfattribs={"layer": W})
    for txt, p in (("BEDROOM", (1150, 1700)), ("KITCHEN", (3250, 1700)), ("COURT", (6000, 1700))):
        msp.add_text(txt, dxfattribs={"layer": TXT, "height": 150 * scale}).set_placement(s(p))
    msp.add_text("lk", dxfattribs={"layer": TXT, "height": 150 * scale, "style": "ARSHX"}).set_placement(
        s((1150, 1000)))
    msp.add_text("BEDROOM", dxfattribs={"layer": TXT, "height": 150 * scale}).set_placement(
        (30000 * scale, 30000 * scale))                         # outside the frame: out of scope
    doc.saveas(str(path))
    return path


def _run(path):
    from tools import urban_boq_m9 as M
    return LC.census_of_run(M.arch_compute(str(path), method="ARCH_TAKEOFF_V2.9", layer_roles=ROLES))


VARIANTS = {"mm": {}, "metres": {"scale": 0.001}, "rot37": {"deg": 37.0}, "mirror": {"mirror": True},
            "rot37_mirror_m": {"deg": 37.0, "mirror": True, "scale": 0.001}}


@pytest.mark.parametrize("name", sorted(VARIANTS))
def test_synthetic_plan_finds_the_planted_omission(tmp_path, name):
    out = _run(plan(tmp_path / f"{name}.dxf", **VARIANTS[name]))
    by = {r["text"]: r for r in out["labels"]}
    assert sorted(by) == ["BEDROOM", "COURT", "KITCHEN"]           # the out-of-frame BEDROOM is not counted
    assert len(out["labels"]) == 3
    assert by["COURT"]["status"] == "SILENT_OMISSION" and by["COURT"]["cause"] == "NO_ROOM"
    for k in ("BEDROOM", "KITCHEN"):
        assert by[k]["status"] in ("MEASURED", "HELD"), by[k]   # in a room the ledger accounts for: never silent
        assert by[k]["room_id"] and by[k]["face_id"]
    assert by["BEDROOM"]["room_id"] != by["KITCHEN"]["room_id"]
    assert out["summary"]["unread_shx"] == 1 and out["unread"][0]["status"] == "UNREAD_SHX"
    assert out["summary"]["by_status"]["SILENT_OMISSION"] == 1
    assert out["summary"]["silent_by_cause"] == {"NO_ROOM": 1}


# ------------------------------------------------------------------ pure census on hand-built records

REG = [{"region_id": "SH1:GF", "floor": "GF", "box": [0, 0, 100, 100]}]
SQ = [(10, 10), (40, 10), (40, 40), (10, 40)]


def _t(i, v, x, y, enc="UNICODE"):
    return {"id": i, "value": v, "x": x, "y": y, "encoding": enc}


def _room(rid, fid, codes, poly, holes=(), area=9.0, floor="GF"):
    return {"room_id": rid, "face_id": fid, "codes": codes, "polygon": poly, "hole_polygons": list(holes),
            "area_m2": area, "floor": floor}


def _cov(*faces):
    return [{"floor": "GF", "physical_regions": {"faces": [{"face_id": f, "state": s, "category": c}
                                                            for f, s, c in faces]}}]


def test_each_ledger_state_maps_to_one_status():
    rooms = [_room("R1", "F1", ["BEDROOM"], SQ), _room("R2", "F2", ["GARDEN"], [(50, 10), (90, 10), (90, 40), (50, 40)]),
             _room("R3", "F3", ["VOID"], [(10, 50), (40, 50), (40, 90), (10, 90)])]
    cov = _cov(("F1", "LINE", "ROOM_FLOOR"), ("F2", "RFI", "EXTERNAL"), ("F3", "EXCLUDED", "VOID"))
    out = LC.census([_t("T1", "BEDROOM", 20, 20), _t("T2", "GARDEN", 60, 20), _t("T3", "VOID", 20, 60)], REG, rooms, cov)
    st = {r["text_id"]: (r["status"], r["cause"]) for r in out["labels"]}
    assert st == {"T1": ("MEASURED", "LEDGER_LINE:ROOM_FLOOR"), "T2": ("HELD", "LEDGER_RFI:EXTERNAL"),
                  "T3": ("UNSUPPORTED", "LEDGER_EXCLUDED:VOID")}


def test_a_face_with_several_ledger_entries():
    rooms = [_room("R1", "F1", ["LIVING"], SQ) | {"codes_with_void": ["LIVING", "VOID"]}]
    cov = _cov(("F1", "EXCLUDED", "VOID"), ("F1", "LINE", "ROOM_FLOOR"), ("F1", "EXCLUDED", "STAIR_BELOW_SEEN"))
    out = LC.census([_t("T1", "LIVING", 20, 20), _t("T2", "VOID", 30, 30)], REG, rooms, cov)
    st = {r["text_id"]: (r["status"], r["cause"]) for r in out["labels"]}
    assert st == {"T1": ("MEASURED", "LEDGER_LINE:ROOM_FLOOR"), "T2": ("UNSUPPORTED", "LEDGER_EXCLUDED:VOID")}
    rfi = LC.census([_t("T1", "LIVING", 20, 20)], REG, rooms, _cov(("F1", "EXCLUDED", "VOID"), ("F1", "RFI", "X")))
    assert rfi["labels"][0]["status"] == "HELD"


def test_missing_is_never_measured():
    rooms = [_room("R1", "F1", ["KITCHEN"], SQ), _room("R2", "F2", ["BEDROOM"], [(50, 10), (90, 10), (90, 40), (50, 40)])]
    cov = _cov(("F1", "LINE", "ROOM_FLOOR"))                       # F2 has no coverage record
    out = LC.census([_t("T1", "BEDROOM", 20, 20), _t("T2", "BEDROOM", 60, 20), _t("T3", "KITCHEN", 95, 95)],
                    REG, rooms, cov)
    st = {r["text_id"]: (r["status"], r["cause"]) for r in out["labels"]}
    assert st == {"T1": ("SILENT_OMISSION", "CODE_NOT_ON_ROOM"), "T2": ("SILENT_OMISSION", "NO_COVERAGE_RECORD"),
                  "T3": ("SILENT_OMISSION", "NO_ROOM")}
    assert out["summary"]["by_status"] == {"MEASURED": 0, "HELD": 0, "UNSUPPORTED": 0, "SILENT_OMISSION": 3}


def test_a_label_named_in_an_unresolved_record_is_held_not_silent():
    out = LC.census([_t("AT7", "BEDROOM", 95, 95)], REG, [], [], [{"item": "label", "source_ref": {"text_id": "AT7"}}])
    assert [(r["status"], r["cause"]) for r in out["labels"]] == [("HELD", "NAMED_IN_UNRESOLVED")]
    out = LC.census([_t("AT7", "BEDROOM", 95, 95)], REG, [], [], [{"source_ref": {"text_id": "AT77"}}])
    assert out["labels"][0]["status"] == "SILENT_OMISSION"       # AT77 does not name AT7


def test_a_label_in_a_hole_is_not_in_the_room_and_nested_takes_the_inner_room():
    outer = _room("RO", "FO", ["LIVING"], [(0, 0), (60, 0), (60, 60), (0, 60)], holes=[SQ], area=36.0)
    inner = _room("RI", "FI", ["BEDROOM"], [(70, 70), (90, 70), (90, 90), (70, 90)], area=4.0)
    big = _room("RB", "FB", ["LIVING", "BEDROOM"], [(65, 65), (99, 65), (99, 99), (65, 99)], area=11.0)
    cov = _cov(("FO", "LINE", None), ("FI", "LINE", None), ("FB", "LINE", None))
    out = LC.census([_t("T1", "LIVING", 20, 20), _t("T2", "BEDROOM", 80, 80)], REG, [outer, inner, big], cov)
    st = {r["text_id"]: (r["status"], r["room_id"]) for r in out["labels"]}
    assert st == {"T1": ("SILENT_OMISSION", None), "T2": ("MEASURED", "RI")}


def test_other_floor_rooms_shx_and_out_of_region_texts():
    rooms = [_room("R1F", "F9", ["BEDROOM"], SQ, floor="1F")]
    out = LC.census([_t("T1", "BEDROOM", 20, 20), _t("T2", "xyz", 20, 20, enc="SHX_UNMAPPED"),
                     _t("T3", "BEDROOM", 500, 500), _t("T4", "NOTE: ALL DIMENSIONS IN CM", 20, 20)],
                    REG, rooms, _cov(("F9", "LINE", None)))
    assert [(r["text_id"], r["status"], r["cause"]) for r in out["labels"]] == [("T1", "SILENT_OMISSION", "NO_ROOM")]
    assert [u["text_id"] for u in out["unread"]] == ["T2"] and out["summary"]["unread_shx"] == 1
    assert out["summary"]["by_floor"] == {"GF": {"SILENT_OMISSION": 1, "UNREAD_SHX": 1}}


def test_empty_inputs_give_an_empty_census():
    out = LC.census([], [], [], [])
    assert out["labels"] == [] and out["unread"] == [] and out["summary"]["labels"] == 0
    assert LC.census([_t("T1", "BEDROOM", 5, 5)], [], [], [])["labels"] == []    # no plan region: out of scope
