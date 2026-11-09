"""T-634 / R-T634-1: dry wall plaster and paint, one face two quantities, and the re-measure of statement V11
T-552/plaster-internal (15 UNKNOWN rows) and T-561/paint-internal (16 UNKNOWN rows) (research rule, unwired).

Villa P634 (synthetic, not Alsenan), hand calculation (m):
  bed room 4.00 x 3.00, chain perimeter 14.00; one 3.00 wall is TILED (a wash niche): dry faces F = 11.00
  paint to the finished ceiling H = 3.00 (FINISHED_CEILING), plaster to the slab soffit H = 3.50 (SLAB_SOFFIT)
  door 0.90 head 2.20 -> 1.980 ; window 1.20 sill 1.00 head 2.40 -> 1.680 (inside both bands)
  paint   11.00 x 3.00 = 33.000 - 1.980 - 1.680 = 29.340
  plaster 11.00 x 3.50 = 38.500 - 1.980 - 1.680 = 34.840
  door return (wall 0.20): 0.20 x (2 x 2.20 + 0.90) = 1.060 ; the window reveal is its own item (Q-73), never in F
  his row: 11.50 x 3.10 = 35.650 vs an engine line 29.300 -> delta 6.350 = length 1.550 + height 1.100 + openings 3.660
           + line residual 0.040 (own 29.340 - line 29.300: ENGINE_WRONG, above the 0.010 tolerance)
Adverse: paint on a tiled face refused; plaster at the finished-ceiling height refused; paint at the slab height refused;
an opening with no head refused (HELD, never 0); a None quantity refused; outline read at 0 / 37 / 211 deg and mirrored.
"""
from __future__ import annotations

import json
import math
import os
import sys
from decimal import Decimal as D
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "agents_t634"))
sys.path.insert(0, str(ROOT / "research" / "agents_t606"))
import t634_rules as R  # noqa: E402
import t606_rules as R6  # noqa: E402

PAINT = {"H": "3.00", "basis": R.PAINT_BASIS}
PLASTER = {"H": "3.50", "basis": R.PLASTER_BASIS}


def ops():
    return [{"id": "D1", "w": "0.90", "sill": "0", "head": "2.20"},
            {"id": "W1", "w": "1.20", "sill": "1.00", "head": "2.40"}]


# ---------------------------------------------------------------- rule (normal)
def test_fixture_paint_and_plaster_two_numbers_on_one_face():
    p = R.face_net("11.00", PAINT, ops(), "paint")
    s = R.face_net("11.00", PLASTER, ops(), "plaster")
    assert p["net"] == D("29.340") and s["net"] == D("34.840")
    assert p["openings"] == s["openings"] == D("3.660")
    assert s["net"] - p["net"] == D("11.00") * D("0.50")


def test_fixture_door_return():
    assert R.return_face("0.20", "0.90", "2.20") == D("1.060")


def test_fixture_window_above_the_paint_band_cut_at_the_band():
    o = [{"id": "W2", "w": "2.00", "sill": "0", "head": "4.30"}]
    assert R.face_net("10", PAINT, o, "paint")["openings"] == D("6.00")
    assert R.face_net("10", PLASTER, o, "plaster")["openings"] == D("7.00")


def test_fixture_split_closes_and_classes_the_residual():
    sp = R.split_room("11.50", "3.10", "11.00", "3.00", "3.660", "29.300")
    assert sp["total"] == D("6.350")
    assert (sp["length"], sp["height"], sp["openings"], sp["line_residual"]) == (D("1.550"), D("1.100"), D("3.660"),
                                                                                  D("0.040"))
    assert sp["residual_class"] == "ENGINE_WRONG"
    sp2 = R.split_room("11.50", "3.10", "11.00", "3.00", "3.660", "29.335")
    assert sp2["residual_class"] == "TOLERANCE"


def test_opening_order_does_not_matter():
    a = R.face_net("11.00", PAINT, ops(), "paint")["net"]
    b = R.face_net("11.00", PAINT, list(reversed(ops())), "paint")["net"]
    assert a == b


def test_row_evidence_tolerance():
    assert R.row_evidence("1.005", "1.000")[0] == "DRAWING-CONFIRMED"
    assert R.row_evidence("1.010", "1.000")[0] == "DIFFERS"


# ---------------------------------------------------------------- rule (adverse)
def test_paint_on_a_tiled_face_refused():
    with pytest.raises(R.RuleError, match="tiled"):
        R.face_net("3.00", PAINT, [], "paint", face_class="WET")


def test_plaster_at_the_finished_ceiling_refused():
    with pytest.raises(R.RuleError, match="Q-72"):
        R.face_net("11.00", {"H": "3.00", "basis": R.PAINT_BASIS}, ops(), "plaster")


def test_paint_at_the_slab_height_refused():
    with pytest.raises(R.RuleError, match="Q-72"):
        R.face_net("11.00", {"H": "3.50", "basis": R.PLASTER_BASIS}, ops(), "paint")


def test_opening_without_head_is_held_never_zero():
    with pytest.raises(R.RuleError, match="never 0"):
        R.face_net("11.00", PAINT, [{"id": "A1", "w": "1.0", "sill": "0", "head": None}], "paint")
    with pytest.raises(R.RuleError, match="HELD"):
        R.return_face("0.15", "1.0", None)


def test_missing_quantity_never_zero():
    with pytest.raises(R.RuleError):
        R.d(None)


def test_openings_larger_than_face_refused():
    with pytest.raises(R.RuleError):
        R.face_net("1.00", PAINT, [{"id": "W", "w": "2.0", "sill": "0", "head": "3.0"}], "paint")


# ---------------------------------------------------------------- outline geometry (R-T606-1, read only)
def _room(theta_deg, mirror):
    pts = [(0, 0), (4000, 0), (4000, 3000), (0, 3000)]
    if mirror:
        pts = [(-x, y) for x, y in pts][::-1]
    t = math.radians(theta_deg)
    pts = [(x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)) for x, y in pts]
    geom = {f"E{i}": ("LINE", (pts[i], pts[(i + 1) % 4])) for i in range(4)}
    return geom, [(f"E{i}", "WALL") for i in range(4)]


@pytest.mark.parametrize("theta", [0, 37, 211])
@pytest.mark.parametrize("mirror", [False, True])
def test_outline_rotation_mirror(theta, mirror):
    g, ch = _room(theta, mirror)
    assert R6.outline(g, ch)["perimeter"] == D("14.000000")


# ---------------------------------------------------------------- development villa (pins)
OUT = ROOT / "research" / "agents_t634" / "out" / "T634_PLASTER_PAINT_REMEASURE.json"
DRAWN = ROOT / "research" / "agents_t634" / "T634_DRAWN.json"


def _out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_builder_rebuild_identical():
    import t634_alsenan as B
    assert json.dumps(B.build(), indent=1, sort_keys=True) + "\n" == OUT.read_text(encoding="utf-8")


def test_31_rows_own_value_and_counts():
    d = _out()
    rows = d["rows"]
    assert len(rows) == 31
    assert sum(r["section"] == "T-552/plaster-internal" for r in rows) == 15
    assert sum(r["section"] == "T-561/paint-internal" for r in rows) == 16
    assert all(r["own"] is not None for r in rows)
    c = d["evidence_count"]
    assert c["T-552/plaster-internal"] == {"DRAWING-CONFIRMED": 14, "DIFFERS": 1, "HELD_untouched": 24}
    assert c["T-561/paint-internal"] == {"DRAWING-CONFIRMED": 15, "DIFFERS": 1, "HELD_untouched": 25}


def test_split_exact_per_section():
    for sid, v in _out()["split"].items():
        assert v["exact"] is True
        assert D(v["own_rows_plus_residuals"]) == D(v["stated_unknown_sum"]) == D(v["scorecard_unknown_signed"])


def test_the_one_differing_row_is_w03_width():
    d = _out()
    dif = [r for r in d["rows"] if r["evidence"] == "DIFFERS"]
    assert len(dif) == 2 and all("GF-15 opening deductions" in r["name"] for r in dif)
    assert all(D(r["own_minus_stated"]) == D("-0.015161") for r in dif)


def test_drawn_faces_and_returns():
    d = _out()
    assert {k: v["face_lm_own"] for k, v in d["rooms"].items()} == {
        "GF-15": "21.534454", "1F-01": "17.700000", "1F-04": "17.400000", "2F-03": "18.900000"}
    assert d["gf02_wet"]["face_lm_own"] == "7.200000" and d["gf02_wet"]["paint_refused"] is True
    assert len(d["returns"]["rows"]) == 26
    assert d["returns"]["own_total"] == "23.069556"
    assert d["returns"]["paint_return_bound"] == ["19.170000", "23.069556"]
    for v in d["rooms"].values():
        assert v["paint_G1"]["class"] == "TOLERANCE"


def test_no_coordinates_or_text_in_the_drawn_json():
    txt = DRAWN.read_text(encoding="utf-8")
    d = json.loads(txt)

    def walk(o):
        if isinstance(o, list):
            assert not (len(o) == 2 and all(isinstance(x, float) for x in o)), "coordinate pair"
            for x in o:
                walk(x)
        elif isinstance(o, dict):
            for x in o.values():
                walk(x)
        elif isinstance(o, float):
            raise AssertionError("raw float in the drawn json")
    walk(d)


DXF = Path(os.environ.get("T634_DXF", ROOT.parents[1] / ".work" / "private" / "P7757_DXF_COMPRESSED" / "P7757.dxf"))


@pytest.mark.skipif(not DXF.exists(), reason="private drawing absent")
def test_private_drawing_reread_is_identical():
    pytest.importorskip("ezdxf")
    import t634_extract as X
    assert json.dumps(X.read(str(DXF)), indent=1, sort_keys=True) + "\n" == DRAWN.read_text(encoding="utf-8")
