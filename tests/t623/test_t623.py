"""T-623: the UNKNOWN residual rows of the beam and column concrete lines re-measured from the drawing (R-T623-1 .. 3).
Hand villa "V623" (not the training villa: one beam over two columns, the second column narrower than the band), the
geometry primitives (oblique drawn end, mirror / rotation, ring in a bay), adverse cases, then the development villa
from the committed output (the private rebuild only when the private inputs are present)."""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from shapely.affinity import rotate, scale
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "agents_t623"))
import t623_rules as R  # noqa: E402

OUT = ROOT / "research" / "agents_t623" / "out" / "T623_UNKNOWN_ROWS.json"
STATEMENT = ROOT / "research" / "agents_t609" / "out" / "RECONCILED_STATEMENT_T609.json"
PRIV = ROOT.parent / "private"
PRIVATE = (PRIV / "ST7757.dxf", PRIV / "concrete_rebar.xlsx")
D = Decimal


# ---- villa "V623" (hand, metres) ---------------------------------------------------------------------------------
# beam BM 0.25 x 0.60, faces y = 0 and y = 0.25, both drawn x 0 .. 6.00
# column KA 0.40 x 0.35 (x 0 .. 0.40, y -0.05 .. 0.30): wider than the band, takes 0.40 x 0.25 = 0.10 m2 of it
# column KB 0.40 x 0.20 (x 5.60 .. 6.00, y 0.025 .. 0.225): NARROWER than the band; takes 0.08 m2, leaves two beside
#   strips 0.40 x 0.025 = 0.02 m2 that stay in the beam line (beam end at a narrow column, R-T614-1; counted once)
# own beam plan = 1.50 - 0.10 - 0.08 = 1.32 m2 -> 0.792 m3
# reference row b x D x L = 0.25 x 0.60 x 6.00 = 0.900 m3 (runs through both columns)
# row delta (reference - own) = 0.108 = KA 0.10 x 0.60 (0.060) + KB 0.08 x 0.60 (0.048): THROUGH_SUPPORT, the two
#   footprints the column lines own (J = KA 0.14 x 0.60 + KB 0.08 x 0.60 = 0.084 + 0.048 = 0.132)
FA = ((0.0, 0.0), (6.0, 0.0))
FB = ((0.0, 0.25), (6.0, 0.25))
KA = box(0.0, -0.05, 0.40, 0.30)
KB = box(5.60, 0.025, 6.00, 0.225)


def _own_plan(fa=FA, fb=FB, cols=(KA, KB)):
    q = R.quad_plan(fa, fb)
    for c in cols:
        q = q.difference(c)
    return q


def test_v623_beam_over_two_columns_one_narrower():
    q = _own_plan()
    assert round(q.area, 9) == 1.32
    assert R.beam_volume(q.area, "0.60") == D("0.792000")
    beside = q.intersection(box(5.60, -1, 6.00, 1)).area
    assert round(beside, 9) == 0.02                      # the narrow column leaves the beam its beside strips
    ref = R.d6(D("0.25") * D("0.60") * D("6.00"))
    delta = ref - R.beam_volume(q.area, "0.60")
    assert delta == D("0.108000")
    assert R.joint_head([(D("0.14"), D("0.60")), (D("0.08"), D("0.60"))]) == D("0.132000")
    status, drift = R.row_status(delta, "0.108")
    assert (status, drift) == ("RE-MEASURED", D("0"))
    causes = {"KA footprint (column line owns)": ("RULE_DIFFERENCE", "0.060"),
              "KB footprint (column line owns)": ("RULE_DIFFERENCE", "0.048")}
    assert R.split_line(delta, causes) == D("0.108000")


def test_v623_beside_strip_once():
    rows = [{"name": "BM through KB", "storey": "GF", "pieces": ["BM", "KB beside"]},
            {"name": "KB joint", "storey": "GF", "pieces": ["KB head"]}]
    assert R.pieces_once(rows) == 3
    rows.append({"name": "KB beside again", "storey": "GF", "pieces": ["KB beside"]})
    with pytest.raises(R.Refused):
        R.pieces_once(rows)


@pytest.mark.parametrize("angle", [0, 30, 90, 137.5])
@pytest.mark.parametrize("mirror", [False, True])
def test_v623_mirror_rotation_invariant(angle, mirror):
    def tf(seg):
        from shapely.geometry import LineString
        g = LineString(seg)
        if mirror:
            g = scale(g, -1, 1, origin=(0, 0))
        g = rotate(g, angle, origin=(0, 0))
        return tuple(g.coords)

    def tfp(p):
        if mirror:
            p = scale(p, -1, 1, origin=(0, 0))
        return rotate(p, angle, origin=(0, 0))
    q = _own_plan(tf(FA), tf(FB), (tfp(KA), tfp(KB)))
    assert abs(q.area - 1.32) < 1e-9


def test_oblique_end_kept_long_face_clipped():
    # face B runs on 0.15 past face A at one end (< one band width 0.20): the drawn oblique end is kept
    q = R.quad_plan(((0, 0), (5.0, 0)), ((0, 0.2), (5.15, 0.2)))
    assert abs(q.area - (5.0 * 0.2 + 0.5 * 0.15 * 0.2)) < 1e-9
    # face B runs on 3.0 (a slab edge / shared face): the band ends with its partner
    q = R.quad_plan(((0, 0), (5.0, 0)), ((0, 0.2), (8.0, 0.2)))
    assert abs(q.area - 1.0) < 1e-9
    # reversed face direction is the same band
    q2 = R.quad_plan(((0, 0), (5.0, 0)), ((5.0, 0.2), (0, 0.2)))
    assert abs(q2.area - 1.0) < 1e-9


def test_ring_in_bay():
    full = R.annulus_in_box((0, 0), 2.0, 2.2, (-10, -10, 10, 10))
    assert abs(full - math.pi * (2.2 ** 2 - 2.0 ** 2)) < 1e-4
    half = R.annulus_in_box((0, 0), 2.0, 2.2, (0, -10, 10, 10))
    assert abs(half - full / 2) < 1e-4
    clipped = R.annulus_in_box((0, 0), 2.0, 2.2, (-2.05, -2.05, 2.05, 2.05))
    assert 0 < clipped < full


def test_count_and_global_depth_hand():
    assert R.count_delta(6, 4, "0.375") == D("0.750000")          # two rows beyond the drawn members
    assert R.count_delta(3, 4, "0.345") == D("-0.345000")         # one drawn member he has no row for
    # three members A 0.10 / 0.125 / 0.275, D_ctrl 0.40 / 0.50 / 0.85 vs his uniform 0.75
    gd = R.global_depth_delta([(D("0.10"), D("0.40")), (D("0.125"), D("0.50")), (D("0.275"), D("0.85"))], "0.75")
    assert gd == D("-0.035000") + D("-0.031250") + D("0.027500")


# ---- adverse -------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("cls", ["BALANCE", "SHORT", "REMAINDER", "PLUG", None, "WHATEVER"])
def test_balancing_or_unknown_class_refused(cls):
    with pytest.raises(R.Refused):
        R.check_class(cls)


def test_balancing_term_as_cause_refused():
    with pytest.raises(R.Refused):
        R.split_line("0.108", {"KA footprint": ("RULE_DIFFERENCE", "0.060"), "BALANCE": ("UNRESOLVED", "0.048")})
    with pytest.raises(R.Refused):
        R.split_line("0.108", {"KA footprint": ("RULE_DIFFERENCE", "0.060"), "SHORT B4": ("UNRESOLVED", "0.048")})


def test_open_sum_refused():
    with pytest.raises(R.Refused):
        R.split_line("0.108", {"KA footprint": ("RULE_DIFFERENCE", "0.060")})


def test_held_as_zero_refused():
    with pytest.raises(R.Refused):
        R.split_line("0", {"designer item": ("HELD", "0")})


def test_unit_and_missing_refused():
    with pytest.raises(R.Refused):
        R.row_status("0.108", "0.108", unit="mm")
    with pytest.raises(R.Refused):
        R.split_line("0.108", {"KA": ("RULE_DIFFERENCE", "0.108")}, unit="m2")
    with pytest.raises(R.Refused):
        R.d6(None)
    with pytest.raises(R.Refused):
        R.beam_volume(1.32, None)
    with pytest.raises(R.Refused):
        R.count_delta(2, 1.5, "0.375")
    with pytest.raises(R.Refused):
        R.global_depth_delta([(D("0.10"), None)], "0.75")


def test_drift_needs_a_named_physical_cause():
    with pytest.raises(R.Refused):
        R.row_status("0.1875", "0.160962")
    with pytest.raises(R.Refused):
        R.row_status("0.1875", "0.160962", drift_cause="BALANCE")
    st, dr = R.row_status("0.1875", "0.160962", drift_cause="EXTENT_VS_ALLOWANCE")
    assert st == "RE-MEASURED" and dr == D("0.026538")
    assert R.row_status("0.1875", "0.1870")[0] == "RE-MEASURED"          # within 0.001 m3
    assert R.row_status("0", "0", held_by="D-16")[0] == "HELD"


def test_faces_not_a_band_refused():
    with pytest.raises(R.Refused):
        R.quad_plan(((0, 0), (5, 0)), ((6, 0.2), (9, 0.2)))           # no overlap along the axis
    with pytest.raises(R.Refused):
        R.quad_plan(((0, 0), (5, 0)), ((0, 0.2), (5, 0.9)))           # not parallel


# ---- development villa (committed output) --------------------------------------------------------------------------
def _out():
    return json.loads(OUT.read_text(encoding="utf-8"))


def test_dev_eighteen_rows_each_with_class_and_status():
    d = _out()
    n = {sid: len(ln["rows"]) for sid, ln in d["lines"].items()}
    assert n == {"T-545/beams@V10": 12, "T-551/columns@V10": 6}
    for ln in d["lines"].values():
        for r in ln["rows"]:
            assert r["class"] in R.CLASSES and r["status"] in R.STATUSES
            assert r["pieces"]
        R.pieces_once(ln["rows"])


def test_dev_line_split_closes_exactly_with_named_drifts():
    d = _out()
    st = json.loads(STATEMENT.read_text(encoding="utf-8"))
    for si, sid in ((2, "T-545/beams@V10"), (3, "T-551/columns@V10")):
        ln = d["lines"][sid]
        stmt = {i: r for i, r in enumerate(st["sections_v10"][si]["rows"])}
        tot = sum((D(stmt[r["row"]]["delta"]) for r in ln["rows"]), D(0))
        assert R.d6(tot) == D(ln["statement_unknown_delta_m3"])
        own = sum((D(r["own_delta"]) for r in ln["rows"]), D(0))
        assert R.d6(own) == D(ln["own_unknown_delta_m3"])
        assert R.d6(own - tot) == D(ln["drift_m3"])
        for r in ln["rows"]:
            assert R.d6(D(r["own_delta"]) - D(r["statement_delta"])) == D(r["drift"])
            if abs(D(r["drift"])) > R.TOL_M3:
                assert r["drift_cause"] and r["drift_cause"].split(":")[0] not in R.BALANCING


def test_dev_key_measures():
    d = _out()
    rows = {r["name"].split(" residual")[0]: r for ln in d["lines"].values() for r in ln["rows"]}
    # columns: every compared member re-read (A and D_ctrl) and J reproduced member by member
    gd = rows["columns GF: GLOBAL_DEPTH"]["evidence"]
    assert gd["members_agreeing"] == "20 / 20" and gd["joint_head_own_m3"] == "2.281250"
    assert rows["columns 1F: GLOBAL_DEPTH"]["evidence"]["joint_head_own_m3"] == "0.385000"
    for k in ("columns GF: COUNT C1", "columns GF: COUNT C2"):
        ev = rows[k]["evidence"]
        assert ev["tags_equal_members"] is True and ev["his_neck_rows_equal_drawn_count"] is True
    # ring and upstands from the raw arcs / section outlines
    assert rows["1F: DOME_RING"]["evidence"]["detail"][0]["ring_plan_m2"] == "1.510481"
    for k in ("GF: UPSTAND", "1F: UPSTAND"):
        up = rows[k]["evidence"]["detail"][0]
        assert (up["upstand_area_m2"], up["span_m"]) == ("0.040000", "3.000000")
    cb = rows["1F: UNTRACED -> 1F CB12 BEYOND_EXTENT"]
    assert cb["evidence"]["outer_face_extent_m"] == "12.000000" and cb["own_delta"] == "0.187500"
    # the THROUGH_SUPPORT residuals stay UNRESOLVED (closure terms, never relabelled)
    for k in ("GF: THROUGH_SUPPORT", "1F: THROUGH_SUPPORT"):
        assert rows[k]["class"] == "UNRESOLVED"


def test_dev_no_coordinate_or_his_row_tracked():
    txt = OUT.read_text(encoding="utf-8")
    for bad in ("ref_m3", "neck_count", "polygon", "\"x\"", "origin", "coords"):
        assert bad not in txt


@pytest.mark.skipif(not all(p.exists() for p in PRIVATE), reason="private drawing / workbook not present")
def test_private_rebuild_equals_committed():
    import t623_alsenan as A
    d = A.build(str(PRIVATE[0]), str(PRIVATE[1]))
    assert json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n" == OUT.read_text(encoding="utf-8")
