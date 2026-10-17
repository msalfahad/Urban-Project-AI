"""Phase 2B-5 Stages D / F: the room-reader benchmark. The truth is hand-derived (bench_cases.py, literals) and checked
against the case coordinates here; every reader is scored against it. What is asserted:

    - independence: the case file imports nothing; no benchmark library module imports the engine (the native adapter
      runs the engine's command line in its own process)
    - the independent DXF reader and the vector-PDF prototype are exact on every case (an arc wall: to the 0.5 mm
      flattening); the engine with declared layer roles is exact on every straight-walled case
    - the CAD encodings (nested / mirrored / non-uniform blocks, metres, polylines, Arabic words with DIMENSIONs, a
      window block) change nothing for the DXF readers; an unresolved XREF is refused by all three, never read empty
    - the raster prototype at 10 mm / px finds every room within 1 % on area (2 % perimeter on the arc wall), with
      every opening of the straight unrotated cases; the 25 mm / px degraded scan finds every room within 5 % on area
    - found defects are asserted as found, so a change in their behaviour is seen: D-D1 (inferred roles miss a door,
      window or column layer drawn once), D-D2 (an arc-walled room's polygon is its chord: area and perimeter exact,
      IoU 0.92), the scan's unread room word joined to a wall (B09)
    - the hybrid rules never average, never take a BOQ quantity from vision, and keep a degraded scan at review
    - a wrong scale is caught by the scale check; a missing OCR is NOT_SUPPORTED, not a failure
"""

from __future__ import annotations

import ast
import json
import math
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bench_cases as BC                                      # noqa: E402
import bench_drawings as BD                                   # noqa: E402
import bench_run as BR                                        # noqa: E402
import hybrid as HY                                           # noqa: E402
import vision as VI                                           # noqa: E402


def _imports(path):
    out = set()
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out |= {a.name for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            out.add(n.module or "")
    return out


def test_independence():
    assert _imports(HERE / "bench_cases.py") == set()
    for p in HERE.glob("*.py"):
        assert not any(m.startswith("engine") for m in _imports(p)), p.name
    assert not any(m.startswith("engine") for m in _imports(HERE.parents[1] / "tools" / "arch_synth.py"))


def _shoelace(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2e6


def _arc_room(a):
    """an arc-walled room by hand: the straight edges + the circular segment on their chord."""
    st = a["straight"]
    th = math.radians(a["a1_deg"] - a["a0_deg"])
    seg = a["r"] ** 2 * (th - math.sin(th)) / 2
    straight = sum(math.dist(st[i], st[i + 1]) for i in range(len(st) - 1))
    return (_shoelace(st) + seg / 1e6), (straight + a["r"] * th) / 1000


@pytest.mark.parametrize("case", BC.CASES, ids=lambda c: c["id"])
def test_the_hand_truth_matches_the_coordinates(case):
    for name, t in case["truth"]["rooms"].items():
        if name in (case.get("arc_room") or {}):
            area, per = _arc_room(case["arc_room"][name])
            assert abs(area - t["area_m2"]) < 1e-9 and abs(per - t["perimeter_m"]) < 1e-9
            continue
        poly = case["rooms"][name]
        holes = sum(0.16 for x, y in case["columns"])
        assert abs(_shoelace(poly) - holes - t["area_m2"]) < 1e-6
        per = sum(math.dist(poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly))) / 1000
        assert abs(per - t["perimeter_m"]) < 1e-6
        assert abs(t.get("boundary_m", t["perimeter_m"]) - per - 1.6 * len(case["columns"])) < 1e-6
    widths = sorted((s1 - s0) / 1000 for kind, *_, s0, s1, _d in case["openings"])
    t = case["truth"]
    assert widths == sorted(t["doors_m"] + t["windows_m"] + t["passages_m"])


@pytest.mark.parametrize("case", BC.ENCODED, ids=lambda c: c["id"])
def test_an_encoding_case_keeps_its_base_truth(case):
    base = BC.BY_ID[case["base"]]
    if case["truth"].get("expect_state"):
        assert case["truth"]["rooms"] == {}                     # the truth is a refusal: nothing to measure
    else:
        assert case["truth"] == base["truth"] and case["rooms"] == base["rooms"]
    assert set(case["encoding"]) <= {"nested_walls", "metres", "polylines", "dimensions", "window_block", "xref_walls"}


def test_the_mirrored_plan_mirrors_every_point():
    """B09 is B05 mirrored: the turned truth polygons are B05's reflected about the plan centre x = 2800."""
    a, _, _ = BD.truth_polygons(BC.BY_ID["B05"])
    b, _, _ = BD.truth_polygons(BC.BY_ID["B09"])
    for k in a:
        assert sorted((round(5600 - x, 6), round(y, 6)) for x, y in a[k]) == sorted((round(x, 6), round(y, 6))
                                                                                  for x, y in b[k])


@pytest.fixture(scope="module")
def bench(tmp_path_factory):
    return BR.run(tmp_path_factory.mktemp("bench"))


def _res(bench, method, refusals=False):
    return {r["case"]: r for r in bench["results"] if r["method"] == method and ("expected_state" in r) == refusals}


def _rooms_ok(r, area_pct, per_pct):
    labelled = [x for x in r["rooms"] if not x["unlabelled"]]
    return r["recall"] == 1.0 and all(abs(x["area_err_pct"]) <= area_pct and abs(x["perimeter_err_pct"]) <= per_pct
                                      for x in labelled)


@pytest.mark.parametrize("method", ["REF_DXF", "PDF_VECTOR", "NATIVE_DECLARED"])
def test_the_exact_readers(bench, method):
    res = _res(bench, method)
    assert set(res) >= {c["id"] for c in BC.CASES}
    for cid, r in res.items():
        if method == "NATIVE_DECLARED" and cid == "B10":
            continue                                                # D-D2 below
        assert _rooms_ok(r, 0.01, 0.01), (method, cid)
        assert r["false_rooms"] == 0
        assert all(x["iou"] >= 0.9999 for x in r["rooms"] if x["found"]), (method, cid)


def test_an_arc_walled_room_in_the_engine(bench):
    """D-D2: the engine's area of the arc-walled room is exact (13.0219 m2 against 13.021882), but the polygon it
    keeps is the chord polygon - IoU 0.92, the arc's 0.50 m rise missing at the boundary. The polygon-based layouts
    and the wall run inherit it (tests/m9_p2b5/test_p2b5_curved_wall.py)."""
    for m in ("NATIVE_AUTO", "NATIVE_DECLARED"):
        x = _res(bench, m)["B10"]["rooms"][0]
        assert abs(x["area_err_pct"]) < 0.001
        assert 0.90 < x["iou"] < 0.93 and abs(x["boundary_err_mm"] - 500.0) < 1.0


def test_the_cad_encodings(bench):
    for m in ("NATIVE_DECLARED", "REF_DXF"):
        for cid in ("C01", "C02", "C03", "C04", "C05"):
            r = _res(bench, m)[cid]
            assert _rooms_ok(r, 0.01, 0.01) and r["false_rooms"] == 0, (m, cid)
            assert all(x["iou"] >= 0.9999 and x["label_ok"] for x in r["rooms"] if not x["unlabelled"]), (m, cid)
            o = r["openings"]
            assert (o["correct"], o["wrong_kind"], o["spurious"]) == (o["expected"], 0, 0), (m, cid)
    for m in ("NATIVE_AUTO", "NATIVE_DECLARED", "REF_DXF"):
        r = _res(bench, m, refusals=True)["C06"]
        assert r["refused_ok"] and "XREF" in r["status"], m
    assert _res(bench, "NATIVE_DECLARED", refusals=True)["C06"]["status"] == "BLOCKED: XREF_NOT_SUPPLIED"


def test_openings_of_the_exact_dxf_readers(bench):
    for cid, r in _res(bench, "NATIVE_DECLARED").items():
        o = r["openings"]
        assert (o["correct"], o["wrong_kind"], o["spurious"]) == (o["expected"], 0, 0), cid
    for cid, r in _res(bench, "REF_DXF").items():
        o = r["openings"]
        # the reference reader reads labelled rooms only: B08's lobby door lies on the unlabelled lobby
        assert o["correct"] == o["expected"] - (1 if cid == "B08" else 0) and o["spurious"] == 0, cid


def test_the_raster_prototype(bench):
    res = _res(bench, "RASTER_10MM")
    assert set(res) == {c["id"] for c in BC.CASES}
    for cid, r in res.items():
        assert _rooms_ok(r, 1.0, 2.0 if cid == "B10" else 1.0), cid    # B10: the arc drawn in pixels, 1.6 %
        assert r["false_rooms"] == 0 and abs(r["scale_check_err_mm"]) <= 30.0
    for cid in ("B01", "B02", "B03", "B04", "B05", "B07", "B08", "B09"):
        o = res[cid]["openings"]
        assert (o["correct"], o["wrong_kind"], o["spurious"]) == (o["expected"], 0, 0), cid


def test_the_degraded_scan(bench):
    res = _res(bench, "SCAN_25MM")
    for cid, r in res.items():
        assert _rooms_ok(r, 5.0, 3.0 if cid != "B09" else 100.0), cid
    # B09 (mirrored): the room word, unread by OCR on the scan, runs into the east wall and is taken as a wall spur -
    # a 1.45 m slit: area within 5 %, perimeter +23 % (asserted as found)
    b = [x for x in res["B09"]["rooms"] if x["truth"] == "BEDROOM"][0]
    assert -5.0 < b["area_err_pct"] < 0 and b["perimeter_err_pct"] > 20.0


def test_the_engine_with_inferred_layer_roles(bench):
    """D-D1: a layer whose role rests on a count (doors: two anchored swings; columns: three filled squares) is not
    recognised when a drawing holds one door / one column; the doors and windows become passages and the column is
    not deducted. Geometry is otherwise exact."""
    res = _res(bench, "NATIVE_AUTO")
    for cid, r in res.items():
        assert r["recall"] == 1.0
    for cid in ("B04", "C03"):
        b04 = [x for x in res[cid]["rooms"] if x["truth"] == "BEDROOM"][0]
        assert abs(b04["area_err_pct"] - 100 * 0.16 / 7.34) < 0.01     # the column's 0.16 m2 not deducted
    for cid in ("B01", "B02", "B03", "B04", "B06", "B07", "B10", "C01", "C02", "C03", "C05"):
        o = res[cid]["openings"]
        assert o["correct"] == 0 and o["wrong_kind"] == o["expected"], cid
    for cid in ("B05", "B09", "C04"):                                     # two doors: the door layer is recognised
        assert res[cid]["openings"]["correct"] == 2, cid


def test_the_hybrid_rules_on_the_benchmark(bench):
    by = {}
    for h in bench["hybrid"]:
        for r in h["records"]:
            by.setdefault(h["vision"], []).append(r)
            assert r["boq_basis"] in ("CAD", None)
            if r["status"] != "VISUAL_OMISSION":
                assert r["boq_area_m2"] == r["cad"]["area_m2"]          # never averaged
            else:
                assert r["boq_area_m2"] is None and r["release"] == "NO_BOQ_CANDIDATE_ONLY"
    assert {r["status"] for r in by["PDF_VECTOR"]} == {"AGREE"}
    assert {r["status"] for r in by["RASTER_10MM"]} <= {"AGREE", "VISUAL_OMISSION"}
    assert "AGREE" not in {r["status"] for r in by["SCAN_25MM"]}


def _sq(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def test_hybrid_status_boundaries():
    src = {"kind": "T", "reader": "t", "version": "1", "method": "t"}
    cad = [{"label": "BATH", "polygon_mm": _sq(0, 0, 4000, 3000), "area_m2": 12.0}]
    same = HY.reconcile(cad, [{"label": "BATH", "polygon_mm": _sq(0, 0, 4000, 3000), "area_m2": 12.0}], src, src)
    assert [r["status"] for r in same] == ["AGREE"]
    shifted = HY.reconcile(cad, [{"label": None, "polygon_mm": _sq(0, 0, 4000, 2850), "area_m2": 11.4}], src, src)
    assert [r["status"] for r in shifted] == ["REVIEW_CANDIDATE"] and shifted[0]["boq_area_m2"] == 12.0
    other = HY.reconcile(cad, [{"label": "KITCHEN", "polygon_mm": _sq(0, 0, 4000, 3000), "area_m2": 12.0}], src, src)
    assert other[0]["status"] == "DISAGREEMENT" and other[0]["label_conflict"]
    away = HY.reconcile(cad, [{"label": "X", "polygon_mm": _sq(9000, 0, 10000, 1000), "area_m2": 1.0}], src, src)
    assert sorted(r["status"] for r in away) == ["CAD_ONLY", "VISUAL_OMISSION"]


def test_a_wrong_scale_is_caught(tmp_path):
    c = BC.BY_ID["B05"]
    meta = BD.raster(c, tmp_path / "b05.png", 10.0)
    wrong = dict(meta, mm_per_px=20.0)                                  # the scale stated twice too large
    r = VI.raster_rooms(tmp_path / "b05.png", wrong)
    assert r["scale_check"].startswith("SCALE_SUSPECT")
    ok = VI.raster_rooms(tmp_path / "b05.png", meta)
    assert ok["scale_check"] == "OK" and abs(ok["wall_thickness_mm"] - 200.0) <= 30.0


def test_no_ocr_is_not_supported(tmp_path, monkeypatch):
    c = BC.BY_ID["B01"]
    meta = BD.raster(c, tmp_path / "b01.png", 10.0)
    monkeypatch.setattr(VI.shutil, "which", lambda name: None)
    r = VI.raster_rooms(tmp_path / "b01.png", meta)
    assert r["ocr"].startswith("NOT_SUPPORTED") and len(r["rooms"]) == 1 and r["rooms"][0]["label"] is None


def test_the_prototypes_are_deterministic(tmp_path):
    c = BC.BY_ID["B05"]
    meta = BD.raster(c, tmp_path / "b05.png", 10.0)
    one = VI.raster_rooms(tmp_path / "b05.png", meta)
    two = VI.raster_rooms(tmp_path / "b05.png", meta)
    strip = lambda r: json.dumps({k: v for k, v in r.items() if k != "runtime_s"}, sort_keys=True, default=str)  # noqa
    assert strip(one) == strip(two)
    m = BD.vector_pdf(c, tmp_path / "b05.pdf")
    assert strip(VI.vector_pdf_rooms(tmp_path / "b05.pdf", m)) == strip(VI.vector_pdf_rooms(tmp_path / "b05.pdf", m))
