"""T-727: union of void deduction pieces, one face one line, provenance of a deduction check (R-T727-1 .. -4).

Villa K727 is hand-made (not the development villa). 1F hall 10.00 x 6.00 = 60.00 m2 with a light well in its south-west
corner: well outline 6.00 x 4.00 = 24.00 m2 = void window 4.00 x 3.00 (12.00, y 1 .. 4) + a straight flight A seen
through it along the south wall (1.00 wide, 10 goings of 0.30 = 3.00 m2, x 0 .. 3) + a flight B 1.00 wide x 2.00 long
(2.00 m2, x 2.95 .. 4.95) whose first 0.05 m lies on A's last going (overlap 0.05 x 1.00 = 0.05 m2), and the rest of
the outline as residue cells. Hand: union A + B = 3.00 + 2.00 - 0.05 = 4.95; residue = 24.00 - 12.00 - 4.95 = 7.05;
floor = 60.00 - 24.00 = 36.00 (the opening is deducted once). Summing A + B (5.00) deducts 24.05: DEDUCTED_TWICE -0.05.
The last tests rebuild the development-villa closure from committed files."""
from __future__ import annotations

import json
import subprocess
import sys
from decimal import Decimal as X
from pathlib import Path

import pytest
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t727"))
import t727_rules as R  # noqa: E402

ROOM = box(0, 0, 10, 6)
WELL = box(0, 0, 6, 4)
VOID = box(0, 1, 4, 4)                       # 4.00 x 3.00
FLIGHT_A = box(0, 0, 3, 1)                   # 10 goings x 0.30 along the south wall, 1.00 wide
FLIGHT_B = box(2.95, 0, 4.95, 1)             # 2.00 x 1.00 east from x 2.95: 0.05 m on A's last going


def _tf(g, deg=0.0, mirror=False, scale=1.0):
    from shapely import affinity
    if mirror:
        g = affinity.scale(g, xfact=-1, yfact=1, origin=(0, 0))
    g = affinity.rotate(g, deg, origin=(0, 0))
    return affinity.scale(g, xfact=scale, yfact=scale, origin=(0, 0))


def _pieces(deg=0.0, mirror=False, scale=1.0):
    return [(n, _tf(g, deg, mirror, scale)) for n, g in
            (("void", VOID), ("A", FLIGHT_A), ("B", FLIGHT_B))]


def test_normal_hand_figures_union_once():
    inc, union, tot = R.union_increments(_pieces())
    assert dict(inc) == pytest.approx({"void": 12.0, "A": 3.0, "B": 1.95})
    assert union == pytest.approx(16.95) and tot == pytest.approx(17.0)
    residue = WELL.area - union
    assert residue == pytest.approx(7.05)
    res, r = R.deduction_check("24.00", [(n, round(a, 6)) for n, a in inc] + [("residue", round(residue, 6))])
    assert (res, r) == ("DEDUCTED_ONCE", X("0.000000"))
    assert ROOM.area - WELL.area == 36.0                      # floor carries 36.00, the opening deducted once


def test_adverse_two_overlapping_footprints_summed_deduct_twice():
    full = [(n, g.area) for n, g in _pieces()]
    residue = WELL.area - R.union_increments(_pieces())[1]
    res, r = R.deduction_check("24.00", full + [("residue", residue)])
    assert res == "DEDUCTED_TWICE" and r == X("-0.050000")
    ex, twice = R.overlap_named([3.0, 2.0], 4.95)
    assert ex == X("0.050000") and twice


def test_adverse_order_does_not_change_the_union():
    a = R.union_increments(_pieces())
    b = R.union_increments(list(reversed(_pieces())))
    assert a[1] == pytest.approx(b[1]) and sum(x for _, x in b[0]) == pytest.approx(16.95)
    assert dict(b[0])["A"] == pytest.approx(2.95)             # the overlap sits on whichever piece comes second


@pytest.mark.parametrize("deg,mirror,scale", [(90, False, 1.0), (37.5, False, 1.0), (0, True, 1.0),
                                              (213, True, 1.0), (0, False, 1000.0)])
def test_geometry_mirror_rotation_units(deg, mirror, scale):
    inc, union, _ = R.union_increments(_pieces(deg, mirror, scale))
    s2 = scale * scale
    assert union / s2 == pytest.approx(16.95, abs=1e-9)
    assert dict(inc)["B"] / s2 == pytest.approx(1.95, abs=1e-9)


def test_tolerance_edge_grid_noise_is_not_twice():
    # a 0.1 mm snap grid on the pieces (0.0004 m2) stays DEDUCTED_ONCE; 0.006 m2 is not noise
    assert R.deduction_check("24.00", [("all", "23.9996")])[0] == "DEDUCTED_ONCE"
    assert R.deduction_check("24.00", [("all", "24.006")])[0] == "DEDUCTED_TWICE"
    assert R.deduction_check("24.00", [("all", "23.994")])[0] == "NOT_DEDUCTED"


def test_provenance_record_of_net_vs_stale_base_list():
    # the net was set from the union record: 60 - (12 + 3 + 1.95 + 7.05) = 36
    rec = [("void", "12"), ("A", "3"), ("B inc", "1.95"), ("residue", "7.05")]
    assert R.net_provenance("60", rec, [], "36") == ("RECORD_OF_NET", X("0.000000"))
    stale = [("void", "12"), ("A", "3"), ("B full", "2.00"), ("residue", "7.05")]
    res, r = R.net_provenance("60", stale, [], "36")
    assert res == "NOT_THE_NET_RECORD" and r == X("-0.050000")
    # a later named deduction (threshold 0.30) is part of the re-add
    assert R.net_provenance("60", rec, [("threshold", "0.30")], "35.70")[0] == "RECORD_OF_NET"


def test_ceiling_one_face_one_line_normal():
    o = R.face_owner("well top", [{"line_id": "L-DECOR", "face_contains": True, "value": 51.0},
                                  {"line_id": "L-OVERVOID", "face_contains": False, "value": None}])
    assert o["owner"] == "L-DECOR" and o["result"] == "ONCE"
    assert o["excluded"] == [("L-OVERVOID", "DUPLICATE_FACE of L-DECOR")]


def test_ceiling_adverse_face_never_in_two_lines():
    two = R.face_owner("well top", [{"line_id": "L-DECOR", "face_contains": True, "value": 51.0},
                                    {"line_id": "L-OVERVOID", "face_contains": False, "value": 12.0}])
    assert two["result"] == "DEDUCTED_TWICE"
    both = R.face_owner("well top", [{"line_id": "L1", "face_contains": True, "value": 1.0},
                                     {"line_id": "L2", "face_contains": True, "value": None}])
    assert both["owner"] is None and both["result"] == "OWNER_UNRESOLVED"
    none = R.face_owner("well top", [{"line_id": "L2", "face_contains": False, "value": None}])
    assert none["owner"] is None and none["result"] == "NOT_CARRIED"


def test_missing_outline_stays_held_never_zero():
    h = R.held_void("V-X", "circle drawn 'above', no opening line")
    assert h["status"] == "HELD" and h["m2"] is None and h["deducted_from"] == []
    assert R.deduction_check(None, [("void", "0")]) == ("VOID_EXTENT_UNRESOLVED", None)
    assert R.union_increments([]) == ([], 0.0, 0.0)


# ---- development villa (committed inputs only) ------------------------------------------------------------------------
OUT = ROOT / "research" / "agents_t727" / "out" / "T727_VOIDS_CLOSED.json"


def test_alsenan_rebuild_identical():
    p = subprocess.run([sys.executable, "-I", str(ROOT / "research" / "agents_t727" / "t727_alsenan.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def test_alsenan_floor_overlap_deducted_once_net_unchanged():
    o = json.loads(OUT.read_text(encoding="utf-8"))
    f, ov = o["floor_1F"], o["overlap"]
    assert ov["strip_by_handles_m2"] == "0.057500" and ov["handles"] == {"F1_last_line": "B4E", "F4_first_riser": "B43"}
    assert abs(X(ov["handle_vs_engine_m2"])) < X("0.0001")
    assert f["net_record"]["result"] == "RECORD_OF_NET"
    assert f["net_record_in_well"]["result"] == "DEDUCTED_ONCE"
    assert f["own_geometry_in_well"]["result"] == "DEDUCTED_ONCE"
    assert f["t719_base_list_check"]["result"] == "DEDUCTED_TWICE"           # the stale list, not the net
    assert f["corrected_m2"] == 33.411036 and f["verdict"].startswith("ENGINE_RIGHT")
    assert o["moved"] == []


def test_alsenan_ceiling_owner_and_v07_held():
    o = json.loads(OUT.read_text(encoding="utf-8"))
    c = o["ceiling_top"]
    assert c["ownership"]["owner"] == "L-43bf1f869e1588f1d3bd" and c["ownership"]["result"] == "ONCE"
    assert c["roof_over_well_2F"]["opening_outline_found"] is False
    assert c["decor_line"]["equals_ledger"] and c["st01_zone_in_well_m2"] == 0.0
    assert o["V-07"]["status"] == "HELD" and o["V-07"]["m2"] is None
