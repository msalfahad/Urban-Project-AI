"""T-658: columns / ground beams / straps / footing HELD lines (research/agents_t658, R-T658-1 .. 6). Hand villa "V658"
(not the training villa) with normal and adverse cases, then the development-villa ledger rebuilt from pinned files."""
from __future__ import annotations

import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t658"))
import t658_rules as R  # noqa: E402
import t658_alsenan as A  # noqa: E402
import t658_measure_bands as MB  # noqa: E402

D = Decimal
OUT = ROOT / "research" / "agents_t658" / "out" / "T658_LEDGER.json"
# V658 sheet S-12 prints ground-beam sections: '< 3 m' 25x30, '< 6 m' 25x45, '> 6 m' 25x60 (no precedence).
V658 = [("LT3", "<", "3", ("0.25", "0.30")), ("LT6", "<", "6", ("0.25", "0.45")), ("GT6", ">", "6", ("0.25", "0.60"))]


# ---- R-T658-1 / -2 -----------------------------------------------------------------------------------------------
def test_hand_short_span_both_titles_give_range():
    # 2.40 m: '< 3' and '< 6' both hold -> 0.25 x 0.30 x 2.40 = 0.180 .. 0.25 x 0.45 x 2.40 = 0.270
    lo, hi, fl = R.span_range(D("2.40"), V658, "V658 S-12")
    assert (lo, hi, fl) == (D("0.18"), D("0.27"), ["TITLES_OVERLAP"])


def test_hand_long_span_single_title_is_a_point():
    lo, hi, fl = R.span_range(D("7.00"), V658, "V658 S-12")   # only '> 6' holds: 0.25 x 0.60 x 7 = 1.05
    assert lo == hi == D("1.05") and fl == []


def test_adverse_on_limit_takes_both_adjacent_sections():
    lo, hi, fl = R.span_range(D("6.00"), V658, "V658 S-12")   # exactly 6.00: neither '< 6' nor '> 6' holds
    assert (lo, hi) == (D("0.675"), D("0.9")) and "ON_LIMIT" in fl


def test_adverse_units_and_missing_refused():
    with pytest.raises(R.Refused):
        R.span_range("2400mm", V658, "V658")
    with pytest.raises(R.Refused):
        R.span_range(D("2400"), V658, "V658")          # 2400 m: unit slip
    with pytest.raises(R.Refused):
        R.span_range(None, V658, "V658")
    with pytest.raises(R.Refused):
        R.m("2.4", "")                                 # no source


def test_mirror_and_rotation_do_not_change_a_span_bound():
    # a mirrored / rotated plan gives the same face-to-face span: the bound depends on the length only
    a = R.span_range(D("4.10"), V658, "V658 S-12 plan")
    b = R.span_range(D("4.10"), list(reversed(V658)), "V658 S-12 plan mirrored")
    assert a[:2] == b[:2]


# ---- R-T658-7 (r2): oblique band = drawn plan area x titles, never one edge ----------------------------------------
def _rd(span, area, edges, w="0.25", b="0.25"):
    return {"span": span, "area_m2": area, "width_m": w, "printed_b_m": b, "edges_m": edges}


def test_hand_oblique_band_uses_plan_area_not_short_edge():
    # V658 45-deg band, width 0.25, edges 1.20 / 1.70 m between two orthogonal faces: trapezoid area
    # 0.25 x (1.20 + 1.70) / 2 = 0.3625 m2; span 1.20 (< 3 and < 6 hold): 0.3625 x 0.30 = 0.10875 .. x 0.45 = 0.163125
    lo, hi, fl = R.area_bound([_rd("1.20", "0.3625", ["1.20", "1.70"])], V658, "V658 S-12")
    assert (lo, hi) == (D("0.10875"), D("0.163125")) and "TITLES_OVERLAP" in fl
    short_edge_hi = D("1.20") * D("0.25") * D("0.45")              # 0.135: what r1 carried
    assert hi > short_edge_hi                                       # the short-edge figure is NOT an upper bound


def test_adverse_unequal_edges_area_below_short_edge_rectangle_refused():
    # an 'area' equal to short edge x width on a band whose edges differ is accepted only as the rectangle floor;
    # below it the outline was not closed to the faces
    with pytest.raises(R.Refused):
        R.area_bound([_rd("1.20", "0.29", ["1.20", "1.70"])], V658, "V658")
    with pytest.raises(R.Refused):                                  # drawn width differs from the printed width
        R.area_bound([_rd("1.20", "0.3625", ["1.20", "1.70"], w="0.30")], V658, "V658")
    with pytest.raises(R.Refused):                                  # one edge only
        R.area_bound([_rd("1.20", "0.3625", ["1.20"])], V658, "V658")


def test_hand_two_outline_readings_span_the_bound():
    # edge drawn open 0.10 m short of its face: as drawn 0.3500, extended 0.3625 m2 -> 0.3500 x 0.30 .. 0.3625 x 0.45
    lo, hi, fl = R.area_bound([_rd("1.20", "0.35", ["1.20", "1.60"]), _rd("1.20", "0.3625", ["1.20", "1.70"])],
                              V658, "V658")
    assert (lo, hi) == (D("0.105"), D("0.163125")) and "OUTLINE_READINGS" in fl


# ---- R-T658-8 (r2): a run carrying a landing beam is LOWER_ONLY -------------------------------------------------------
def test_hand_loaded_run_floor_least_title_least_reading():
    # loaded 2.40 m rectangle 0.25 wide (area 0.60): '< 3' and '< 6' hold -> floor 0.60 x 0.30 = 0.18; no high
    assert R.loaded_floor([_rd("2.40", "0.60", ["2.40", "2.40"])], V658, "V658") == D("0.18")
    # two span readings 5.95 / 6.05 (frame vs band end): 5.95 -> '< 6' 0.45; 6.05 -> '> 6' 0.60: floor on the least
    f = R.loaded_floor([_rd("5.95", "1.4875", ["5.95", "5.95"]), _rd("6.05", "1.5125", ["6.05", "6.05"])], V658, "V658")
    assert f == D("0.669375")
    # on the limit: the two adjacent titles, the least of them
    assert R.loaded_floor([_rd("6.00", "1.50", ["6.00", "6.00"])], V658, "V658") == D("0.675")


def test_adverse_loaded_row_carries_no_high():
    with pytest.raises(R.Refused):
        R.row("L-V658-GB2", "STR.CONC.GROUND_BEAM", "V658:GB2", "LOWER_ONLY", low="0.18", high="0.27", item="D-33")
    with pytest.raises(R.Refused):
        R.loaded_floor([], V658, "V658")


# ---- R-T658-7 measuring step on a synthetic drawing (no private file) --------------------------------------------------
def _synthetic(tmp_path, rotate_deg=0.0, mirror=False, scale=1.0):
    ezdxf = pytest.importorskip("ezdxf")
    import math
    doc = ezdxf.new()
    msp = doc.modelspace()

    def T(x, y):
        x, y = (-x if mirror else x) * scale, y * scale
        a = math.radians(rotate_deg)
        return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)

    def L(p, q):
        return msp.add_line(T(*p), T(*q)).dxf.handle
    s2 = 300 * math.sqrt(2)
    h = {"faceA": L((0, -5000), (0, 5000)),                      # vertical face x = 0
         "faceB": L((-5000, -2000), (5000, -2000)),              # horizontal face y = -2000
         "e1": L((0, 0), (2000, -2000)),                         # 45-deg edge, ends on faceB
         "e2": L((0, s2), (2000 + s2 - 100, -2000 + 100)),       # parallel edge, drawn open 100 mm (x) short of faceB
         }
    p = tmp_path / "v658.dxf"
    doc.saveas(p)
    runs = {"EXT": {"edges": ("e1", "e2"), "outline": [("X", "e1", "faceA"), ("X", "e1", "faceB"),
                                                       ("X", "e2", "faceB"), ("X", "e2", "faceA")]},
            "DRAWN": {"edges": ("e1", "e2"), "outline": [("X", "e1", "faceA"), ("E", "e1", 1), ("E", "e2", 1),
                                                         ("X", "e2", "faceA")]}}
    runs = {k: {"edges": tuple(h[e] for e in v["edges"]),
                "outline": [tuple(h.get(x, x) if isinstance(x, str) else x for x in r) for r in v["outline"]]}
            for k, v in runs.items()}
    return str(p), runs


def test_measure_synthetic_oblique_band_and_invariance(tmp_path):
    # hand: band between y = -x and y = -x + 424.264 (width 300), from x = 0 to y = -2000: the extended outline is a
    # trapezoid with edges 2000*sqrt2 = 2.828427 and (2000 + 424.264)*sqrt2 = 3.428427 m -> area 0.3 x 3.128427 m2
    base = None
    for rot, mir, sc in ((0, False, 1.0), (33.0, False, 1.0), (0, True, 1.0), (117.0, True, 1.0)):
        path, runs = _synthetic(tmp_path, rot, mir, sc)
        out = MB.measure(path, runs)["runs"]
        ext = out["EXT"]
        assert ext["width_m"] == 0.3
        assert abs(ext["area_m2"] - 0.3 * (2.828427 + 3.428427) / 2) < 2e-6
        assert sorted(ext["band_edges_m"]) == [2.828427, 3.428427]
        assert out["DRAWN"]["area_m2"] < ext["area_m2"]           # the open-ended drawn reading is the smaller
        base = base or ext["area_m2"]
        assert ext["area_m2"] == base                             # rotation / mirror do not change the area


def test_measure_refuses_mm_slip_via_rules(tmp_path):
    # a drawing in metres read as mm would give a 0.0003 m width: the rules refuse a width that differs from the print
    path, runs = _synthetic(tmp_path, scale=0.001)
    ext = MB.measure(path, runs)["runs"]["EXT"]
    with pytest.raises(R.Refused):
        R.area_bound([{"span": "2.8", "area_m2": max(ext["area_m2"], 0.000001), "width_m": max(ext["width_m"], 0.000001),
                       "printed_b_m": "0.30", "edges_m": [max(x, 0.000001) for x in ext["band_edges_m"]]}],
                     V658, "V658")


# ---- R-T658-3 ----------------------------------------------------------------------------------------------------
def test_hand_literal_floor_lower_only():
    # runs 3.0 + 1.5 m, b 0.25, top +0.40 to N.G. 0.00: 4.5 x 0.25 x 0.40 = 0.450 floor; high open
    f = R.literal_floor(["3.0", "1.5"], "0.25", "0.40", "0.00", "V658 S-13")
    assert f == D("0.45")
    row = R.row("L-V658-GB1", "STR.CONC.GROUND_BEAM", "V658:GB1", "LOWER_ONLY", low=f, item="designer depth item")
    assert row["high"] is None and row["low"] == "0.450000"


def test_adverse_literal_top_below_underside_refused():
    with pytest.raises(R.Refused):
        R.literal_floor(["3.0"], "0.25", "0.00", "0.10", "V658")


# ---- R-T658-4 / -5 -----------------------------------------------------------------------------------------------
def test_hand_column_ceiling_from_finished_mark():
    # schedule 20x50 = 0.10 m2, base slab top +6.95, roof finished mark +10.40: h <= 3.45 -> ceiling 0.345 m3
    assert R.column_ceiling(D("0.10"), "6.95", "10.40") == D("0.345")


def test_adverse_ceiling_refused_with_upstand_or_unknown_second_reading():
    assert R.column_ceiling(D("0.10"), "6.95", "10.40", top_may_exceed_mark=True) is None
    assert R.column_ceiling(D("0.10"), "6.95", "10.40", second_reading_unknown=True) is None


def test_adverse_schedule_and_plan_disagree_hold_both():
    lo, hi = R.conflict_range(["0.125", "0.10"], D("4.20"))   # plan 25x50 vs schedule 20x50 x 4.20
    assert (lo, hi) == (D("0.42"), D("0.525"))
    with pytest.raises(R.Refused):
        R.conflict_range(["0.10", "0.10"], D("4.20"))        # one reading is not a range


# ---- R-T658-6 ----------------------------------------------------------------------------------------------------
def test_held_never_zero_and_blank_names_item():
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "BOUNDED", low=0, high="0.3")
    R.row("L-x", "STR.CONC.STRAP", "x", "BOUNDED", low=0, high="0.3", flags=["EXISTENCE_OPEN"])
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "HELD_BLANK")
    with pytest.raises(R.Refused):
        R.row("L-x", "STR.CONC.COLUMN", "x", "UPPER_ONLY", high="0.4")


# ---- development villa: rebuilt from pinned committed files --------------------------------------------------------
def test_ledger_reproduces_committed_output():
    doc = A.build()
    assert json.loads(json.dumps(doc, sort_keys=True)) == json.loads(OUT.read_text(encoding="utf-8"))


def test_ledger_every_line_once_and_counts():
    doc = A.build()
    rows = doc["rows"]
    assert len(rows) == 61 and len({r["line_id"] for r in rows}) == 61
    t = doc["totals"]
    assert {k: t[k]["lines"] for k in t} == {"STR.CONC.COLUMN": 29, "STR.CONC.GROUND_BEAM": 29,
                                              "STR.CONC.STRAP": 2, "STR.CONC.FOOTING": 1}
    gb = t["STR.CONC.GROUND_BEAM"]
    assert (gb["before_low"], gb["before_high"]) == ("2.808073", "6.621731")
    # r2: 9 bounded (4 orthogonal short spans, 2 oblique on their drawn area, BAND0007 / BAND0025.1, boundary 0 ..)
    assert (gb["bounded"], gb["bounded_low"], gb["bounded_high"]) == (9, "1.173410", "5.096771")
    # 16 LOWER_ONLY: 8 annex D-35 floors 2.227973 + 8 D-33 loaded-run floors 2.841866; 4 blank (3 court, 1 sliver)
    assert (gb["lower_only"], gb["lower_only_floor"], gb["blank"]) == (16, "5.069839", 4)
    col = t["STR.CONC.COLUMN"]
    assert (col["bounded_low"], col["bounded_high"]) == ("8.034000", "10.119000")   # conflict range unchanged
    assert (col["upper_only"], col["upper_only_ceiling"], col["blank"]) == (6, "2.801250", 8)


def test_ledger_no_figure_invented_and_ranges_not_narrowed():
    for r in A.build()["rows"]:
        moved = "AREA_NOT_RECTANGLE" in r["flags"] or "R-T658-8" in r["flags"]
        if r["before_low"] is not None and r["low"] is not None and r["high"] is not None and not moved:
            assert D(r["low"]) <= D(r["before_low"]) and D(r["high"]) >= D(r["before_high"]), r["line_id"]
        if r["high"] is not None and r["before_high"] is not None:
            assert D(r["high"]) >= D(r["before_high"]), r["line_id"]     # no high ever drops below the old one
        if r["status"] == "HELD_BLANK":
            assert r["low"] is None and r["high"] is None and r["item"]
        assert "freelancer" not in json.dumps(r).lower()


# ---- r2 Checker points ---------------------------------------------------------------------------------------------
def _gb(doc, key):
    return [r for r in doc["rows"] if r["element_id"].endswith(key)][0]


def test_r2_oblique_runs_bound_the_drawn_member():
    doc = A.build()
    b38, b39 = _gb(doc, "BAND0038"), _gb(doc, "BAND0039")
    # Checker r1 own outlines: BAND0038 0.309944 m2 -> 30x40 0.123978; BAND0039 0.631972 m2 -> 0.252789 m3
    assert D(b38["high"]) >= D("0.123978") and D(b39["high"]) >= D("0.252789")
    assert (b38["low"], b38["high"]) == ("0.093040", "0.130678")     # 0.310134 x 0.30 .. 0.326694 x 0.40
    assert (b39["low"], b39["high"]) == ("0.196120", "0.261493")     # 0.653733 x 0.30 .. x 0.40
    for k in ("BAND0037.1", "BAND0008.2"):
        assert "AREA_NOT_RECTANGLE" in _gb(doc, k)["flags"]


def test_r2_every_d33_run_lower_only_no_high():
    doc = A.build()
    want = {"BAND0010.3": "0.600000", "BAND0008.1": "0.596400", "BAND0008.2": "0.147657", "BAND0040": "0.189000",
            "BAND0023:7DC+7DD#1": "0.423000", "BAND0032:7E7+7E8#2": "0.423000", "BAND0037.1": "0.242309",
            "BAND0019": "0.220500"}
    for k, lo in want.items():
        r = _gb(doc, k)
        assert (r["status"], r["low"], r["high"]) == ("LOWER_ONLY", lo, None), k
        assert "D-33" in r["item"]
    assert not [r for r in doc["rows"] if "D-33_LOADED_SPAN" in r["flags"] and r["high"] is not None]


def test_r2_band_areas_pinned_to_the_checker_dxf_and_carry_no_coordinates():
    txt = A.AREAS.read_text(encoding="utf-8")
    doc = json.loads(txt)
    assert doc["dxf_sha256_16"] == A.DXF_SHA16
    import re
    assert not re.search(r"(?<![A-Za-z\d])\d{4,}\.\d", txt)                      # no drawing coordinate (mm) is tracked
    for k, v in doc["runs"].items():
        if not k.startswith(("BAND0038", "BAND0039", "BAND0037.1", "BAND0008.2")):
            e = v["band_edges_m"]
            assert e[0] == e[1] and abs(v["area_m2"] - e[0] * v["width_m"]) < 1e-6, k   # orthogonal controls
