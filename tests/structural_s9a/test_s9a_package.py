"""S9A package: the completeness correction layer over the frozen S9 (owners and lanes only; nothing released).

Checks are re-derived here with code independent of the builder where the source allows it: the dense-hatch bands are
re-detected from ST7757.dxf, the beam readings are recomputed from B, H, L and t, the ground-beam length classes from
the lengths, the S9A inventory view from S9's inventory plus the S9A delta register, and the band polygons in the SVG
figures are mapped back to drawing mm. Passing tests prove arithmetic and reading, not engineering approval."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "research"
PKG = R / "alsenan_structural_s9a"
S9 = R / "alsenan_structural_s9"
S1 = R / "alsenan_structural_census_s1"
MANIFEST = PKG / "18_S9A_CORRECTION_MANIFEST.json"
ST_DXF = ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
FIREWALL = re.compile(r"registers_v3b|R9_1|alsenan_arch_truth_05|post_freeze|pre_s8_structural_completeness")
RELEASED = {"RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA"}
LABELS = {"SOURCE-DERIVED", "SCHEMATIC", "CONDITIONAL"}
SVG = "{http://www.w3.org/2000/svg}"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, pkg=PKG):
    with open(pkg / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return None if v in (None, "", "None") else float(v)


@pytest.fixture(scope="module")
def s():
    return J(PKG / "16_S9A_SUMMARY.json")


@pytest.fixture(scope="module")
def bands():
    return rows("03_BAND_CORRECTION_REGISTER.csv")


@pytest.fixture(scope="module")
def beams():
    return rows("05_BEAM_CONVENTION_COMPARISON.csv")


@pytest.fixture(scope="module")
def s9conc():
    return rows("02_CONCRETE_BOQ_RECONCILIATION.csv", S9)


@pytest.fixture(scope="module")
def deltas():
    return rows("10_S9A_DELTA_REGISTER.csv")


# ------------------------------------------------------------------ correction layer and firewall
def test_dated_correction_layer_over_unchanged_s9(s):
    m = J(MANIFEST)
    assert m["state"] == "DATED_CORRECTION_LAYER" and m["references_read"] == [] == s["references_read"]
    assert m["release_delta"] == {"concrete_m3": 0.0, "kg": 0.0} == s["release_delta"]
    DR.verify_frozen(MANIFEST, ROOT)
    s9m = S9 / "16_S9_FREEZE_MANIFEST.json"
    assert m["s9_manifest_sha256"] == hashlib.sha256(s9m.read_bytes()).hexdigest()
    DR.verify_frozen(s9m, ROOT)
    assert len(m["frozen_baselines"]) == 30 and "S9" in m["frozen_baselines"]
    assert not [p for p in m["inputs"] if FIREWALL.search(p)]
    assert {"engine/source/structural_completeness.py", "research/alsenan_structural_s9a/build_s9a.py",
            "research/alsenan_structural_s9a/visual_s9a.py"} <= set(m["code"])
    outs = set(m["outputs"])
    assert "visual/S9A_VISUAL_QA.html" in outs and not [o for o in outs if o.endswith(".pdf")]
    assert m["drawing_sha256"]["ST7757.dxf"] == ST_DXF.name.split(".")[0]


def test_registry_declares_the_engine_the_builder_and_the_comparison():
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "engine/source/structural_completeness.py" in RP.ACCURATE_MODULES
    assert {"research/alsenan_structural_s9a/build_s9a.py",
            "research/alsenan_structural_s9a/visual_s9a.py"} <= set(RP.ACCURATE_BUILDERS)
    assert "research/alsenan_structural_s9a/post_freeze/post_freeze_comparison.py" in RP.COMPARISON_MODULES


def test_gate_stays_incomplete_and_nothing_is_released(s):
    assert "INCOMPLETE" in s["gate_note"]
    s9 = J(S9 / "14_RELEASE_SUMMARY.json")
    assert s["released_unchanged"] == {"concrete_m3": s9["released_concrete_m3_total"],
                                       "reinforcement_kg": s9["released_reinforcement_kg_total"]}


# ------------------------------------------------------------------ A. S9 verified
def test_s9_totals_recomputed_independently(s):
    v = rows("01_S9_TOTALS_VERIFICATION.csv")
    agree = [r for r in v if r["RESULT"] == "AGREES"]
    assert len(agree) == 21 == s["verification"]["families_agree"]
    assert all(abs(float(r["PUBLISHED_MINUS_INDEPENDENT"])) < 1e-6 for r in agree)
    tot = {r["TRADE"]: r for r in v if r["FAMILY"] == "TOTAL"}
    assert float(tot["CONCRETE"]["INDEPENDENT_RECOMPUTE"]) == pytest.approx(158.070256, abs=1e-6)
    assert float(tot["REINFORCEMENT"]["INDEPENDENT_RECOMPUTE"]) == pytest.approx(18845.961347, abs=1e-6)
    for trade in ("CONCRETE", "REINFORCEMENT"):
        fam = [float(r["INDEPENDENT_RECOMPUTE"]) for r in agree if r["TRADE"] == trade and r["FAMILY"] != "TOTAL"]
        assert math.fsum(fam) == pytest.approx(float(tot[trade]["INDEPENDENT_RECOMPUTE"]), abs=1e-6)
    rd = next(r for r in v if r["FAMILY"] == "README_TABLE_3DP")
    assert rd["RESULT"] == "ROUNDING_ONLY" and float(rd["PUBLISHED_MINUS_INDEPENDENT"]) == pytest.approx(0.001)
    # two families straight from their stage registers, without the builder
    s4 = math.fsum(float(r["net_bbs_kg"]) for r in rows("FOOTING_BBS_NET.csv", R / "alsenan_footing_rebar_s4"))
    assert s4 == pytest.approx(float(next(r for r in agree if r["TRADE"] == "REINFORCEMENT" and
                                          r["FAMILY"] == "FOOTINGS")["INDEPENDENT_RECOMPUTE"]), abs=1e-6)


def test_inventory_lanes_deltas_and_s9_c01(s9conc):
    assert all(r["RESULT"] == "PASS" for r in rows("02_S9_INVENTORY_VERIFICATION.csv"))
    inv = rows("01_COMPONENT_INVENTORY.csv", S9)
    assert len(inv) == 560 == len({r["COMPONENT_ID"] for r in inv}) == len(s9conc)
    dl = rows("10_S9_DELTA_REGISTER.csv", S9)
    d = [r for r in dl if r["CHANGE_KIND"] == "CONCRETE_QUANTITY_RELEASED"]
    assert len(d) == 110 and math.fsum(float(r["DELTA_M3"]) for r in d) == pytest.approx(145.86616, abs=1e-6)
    rel = {r["COMPONENT_ID"]: f(r["RELEASED_M3"]) for r in s9conc if r["LANE"] == "RELEASED_S9_DELTA"}
    assert {r["COMPONENT_ID"] for r in d} == set(rel)
    assert all(float(r["DELTA_M3"]) == pytest.approx(rel[r["COMPONENT_ID"]], abs=1e-9) for r in d)
    c01d = [r for r in dl if r["DELTA_ID"] == "S9-C01"]
    assert len(c01d) == 1 and float(c01d[0]["DELTA_KG"]) == pytest.approx(-1217.128)
    bars = rows("03_REINFORCEMENT_BOQ_RECONCILIATION.csv", S9)
    c01 = [b for b in bars if b["CORRECTIONS"] == "S9-C01"]
    assert len(c01) == 288 and math.fsum(float(b["NOT_RELEASED_KG"] or 0) for b in c01) == pytest.approx(1217.128)
    assert all(b["LANE"] not in RELEASED for b in c01)
    # the 98.994 m3 conditional point lives on unreleased rows only
    assert all(not f(r["CONDITIONAL_M3"]) for r in s9conc if r["LANE"] in RELEASED)
    assert all(not f(r["RELEASED_M3"]) for r in s9conc if r["LANE"] not in RELEASED)


# ------------------------------------------------------------------ B. bands
def _dxf():
    ST_DXF.read_bytes()                                       # a missing private drawing fails with its path
    import ezdxf
    return ezdxf.readfile(str(ST_DXF))


def test_bands_redetected_from_the_drawing(bands):
    doc = _dxf()
    dense, sunken = {}, []
    for e in doc.modelspace().query("HATCH"):
        if e.dxf.layer != "S-HAT.BAT" or e.dxf.solid_fill or e.dxf.pattern_name != "ANSI31":
            continue
        ln = e.pattern.lines[0]
        a = math.radians(ln.angle)
        sp = abs(-ln.offset[0] * math.sin(a) + ln.offset[1] * math.cos(a))
        p = e.paths[0]
        pts = [(v[0], v[1]) for v in p.vertices] if hasattr(p, "vertices") else \
            [(ed.start.x, ed.start.y) for ed in p.edges if hasattr(ed, "start")]
        area = abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2e6
        if abs(sp - 100) < 0.5:
            dense[e.dxf.handle] = area
        elif abs(sp - 250) < 0.5:
            sunken.append(e.dxf.handle)
    assert set(dense) == {b["DXF_HANDLE"] for b in bands} and len(dense) == 8
    for b in bands:
        assert dense[b["DXF_HANDLE"]] == pytest.approx(float(b["AREA_M2"]), abs=1e-6)
    assert math.fsum(dense.values()) == pytest.approx(4.947346, abs=1e-6)
    assert len(sunken) == 6


def test_band_register_classes_overlaps_and_states(bands, s9conc):
    assert len({b["BAND_ID"] for b in bands}) == 8 == len({b["DXF_HANDLE"] for b in bands})
    ref = J(PKG / "04_BAND_EVIDENCE.json")["legend_reference_spacing_mm"]
    lane = {r["COMPONENT_ID"]: r for r in s9conc}
    rows_ = Counter(b["S9_COMPONENT_SAME_FOOTPRINT"] for b in bands)
    for b in bands:
        sp = float(b["PDF_SPACING_MODEL_MM"])
        assert b["LEGEND_MATCH"] == "CANTILEVER_PORTION"
        assert abs(sp - ref["CANTILEVER_PORTION"]) / ref["CANTILEVER_PORTION"] <= 0.06
        assert abs(sp - ref["BEARING_WALL"]) / ref["BEARING_WALL"] > 0.06
        assert float(b["SLAB_PANEL_OVERLAP_M2"]) == 0 and float(b["COLUMN_OVERLAP_M2"]) == 0
        assert b["THICKNESS_MM"].startswith("UNKNOWN") and float(b["RELEASED_M3"]) == 0 == float(b["RELEASED_KG"])
        r = lane[b["S9_COMPONENT_SAME_FOOTPRINT"]]
        assert r["LANE"] not in RELEASED and not f(r["RELEASED_M3"]) and r["FAMILY"] == "BEAMS"
        poly = json.loads(b["POLYGON_LOCAL_MM"])
        xs, ys = [p[0] for p in poly], [p[1] for p in poly]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        assert sorted([w, h]) == pytest.approx(sorted([float(b["WIDTH_MM"]), float(b["LENGTH_MM"])]), abs=0.2)
    assert set(rows_.values()) == {1}


def test_unique_ownership_after_s9a(bands, deltas, s9conc):
    tr = [d for d in deltas if d["CHANGE_KIND"] == "OWNERSHIP_TRANSFER"]
    bd = [d for d in deltas if d["CHANGE_KIND"].startswith("BAND_")]
    assert len(bd) == 8 and len(tr) == 7
    assert all(float(d["DELTA_M3"]) == 0 and float(d["DELTA_KG"]) == 0 for d in deltas)
    not_ca = {b["S9_COMPONENT_SAME_FOOTPRINT"] for b in bands if not b["OWNER_DECISION"].startswith("BEAMS")}
    assert {d["COMPONENT_ID"] for d in tr} == not_ca
    lane = {r["COMPONENT_ID"]: r["LANE"] for r in s9conc}
    for d in tr:
        assert d["FROM_LANE"] == lane[d["COMPONENT_ID"]] and d["TO_LANE"].startswith("SUPERSEDED")
    assert not [d for d in deltas if d["TO_LANE"] in RELEASED]
    inv = {r["COMPONENT_ID"]: r["CONCRETE_LANE"] for r in rows("01_COMPONENT_INVENTORY.csv", S9)}
    view = {k: v for k, v in inv.items() if k not in {d["COMPONENT_ID"] for d in tr}}
    for d in bd:
        assert d["COMPONENT_ID"] not in view
        view[d["COMPONENT_ID"]] = d["TO_LANE"]
    assert len(view) == 561
    rep = (PKG / "12_STRUCTURAL_COMPLETENESS_REPORT.md").read_text(encoding="utf-8")
    assert "(561 records)" in rep and "| **All** | 561 |" in rep


# ------------------------------------------------------------------ C. beams, slabs, columns
def test_beam_readings_recomputed_and_no_slab_counted_twice(beams):
    assert len(beams) == 150 and all(float(b["RELEASED_M3"]) == 0 for b in beams)
    for b in beams:
        if not b["V_TOTAL_DEPTH_M3"]:
            continue
        B, H, Lm, t = (float(b[k]) for k in ("B_MM", "H_MM", "L_M", "SLAB_T_MM"))
        assert float(b["V_TOTAL_DEPTH_M3"]) == pytest.approx(B * H * Lm / 1e6, abs=2e-6)
        assert float(b["V_BELOW_SLAB_M3"]) == pytest.approx(B * (H + t) * Lm / 1e6, abs=2e-6)
        assert float(b["SLAB_STRIP_M3"]) == pytest.approx(B * t * Lm / 1e6, abs=2e-6)
    cond = [b for b in beams if b["S9A_STATE"].startswith(("CONDITIONAL", "BAND_IS"))]
    tot = next(r for r in rows("06_BEAM_CONVENTION_TOTALS.csv") if r["GROUP"] == "ALL" and
               r["SET"].startswith("conditional"))
    assert len(cond) == int(tot["BEAMS"]) == 103
    a = math.fsum(float(b["V_TOTAL_DEPTH_M3"]) for b in cond)
    bb = math.fsum(float(b["V_BELOW_SLAB_M3"]) for b in cond)
    assert a == pytest.approx(float(tot["TOTAL_DEPTH_M3"]), abs=1e-5)
    assert bb == pytest.approx(float(tot["BELOW_SLAB_M3"]), abs=1e-5)
    assert bb - a == pytest.approx(float(tot["SENSITIVITY_M3"]), abs=1e-5)
    o = {r["CHECK_ID"]: r for r in rows("07_BEAM_SLAB_COLUMN_OVERLAP_AUDIT.csv")}
    assert o["BO-01"]["RESULT"] == "PASS" and o["BO-01"]["DETAIL"].startswith("243 of 243")
    assert o["BO-02"]["RESULT"] == "PASS" and o["BO-02"]["DETAIL"] == "0 m2"
    assert o["BO-04"]["RESULT"] == "INFO" and int(o["BO-04"]["COUNT"]) == 10


def test_gross_to_net_on_every_s9_row(s9conc):
    n = 0
    for r in s9conc:
        g, d, net = f(r["GROSS_M3"]), f(r["DEDUCTIONS_M3"]), f(r["NET_M3"])
        if g is not None and net is not None:
            assert g - (d or 0.0) == pytest.approx(net, abs=1e-6), r["COMPONENT_ID"]
            n += 1
        if r["LANE"] in RELEASED:
            assert f(r["RELEASED_M3"]) == pytest.approx(net, abs=1e-6), r["COMPONENT_ID"]
    assert n >= 110


def test_ground_beam_classes_and_column_kinds():
    gb = rows("08_GROUND_BEAM_AUDIT.csv")
    assert len(gb) == 62 and all(r["PROBLEM_KIND"] and r["NEEDED"] for r in gb)
    labels = ["< 2.5 m (30x30)", "2.5 - 5 m (30x40)", "> 5 m (30x60)"]
    cls = lambda x: labels[0 if x < 2.5 else (1 if x < 5.0 else 2)]  # noqa: E731
    for r in gb:
        cc, cl = f(r["CC_M"]), f(r["CLEAR_M"])
        if cc is not None:
            assert r["CLASS_BY_CC"] == cls(cc)
        if cl is not None:
            assert r["CLASS_BY_CLEAR"] == cls(cl)
        if cc is not None and cl is not None:
            assert (r["CLASS_CHANGES_WITH_BASIS"] == "True") == (cls(cc) != cls(cl))
        if r["PROBLEM_KIND"] == "MISSING_SOURCE_INFORMATION":
            assert not r["M3_EXCLUSIVE_TITLES_CC_BASIS"] and not r["M3_EXCLUSIVE_TITLES_CLEAR_BASIS"]
    k = Counter(r["PROBLEM_KIND"] for r in gb)
    assert k["RELEASED_IN_S9"] == 6 and k["MISSING_SOURCE_INFORMATION"] == 30
    assert sum(v for x, v in k.items() if x.startswith("INTERPRETATION")) == 18
    col = rows("09_COLUMN_AUDIT.csv")
    assert len(col) == 28
    ck = Counter(r["PROBLEM_KIND"].split(" + ")[0] for r in col)
    assert ck["INTERPRETATION_SCHEDULE_STOREY_ROW"] + ck["INTERPRETATION_TYPE_TAG"] == 19
    assert ck["GENUINE_CONFLICT"] + ck["GENUINE_CONFLICT_ONE_DIMENSION"] == 9
    lift = [r for r in col if r["LIFT_COLUMN"] == "True"]
    assert len(lift) == 4 and all("LIFT_PIT_CONFLICT" in r["PROBLEM_KIND"] for r in lift)
    for r in lift:
        assert min(json.loads(r["DRAWN_CM"])) in (20.0, 25.0) and min(json.loads(r["SCHEDULE_CM"])) == 30.0
    h = {"GF": 4.5, "1F": 4.2, "2F": 4.2}
    for r in col:
        if r["FLOOR"] in h:
            sc = json.loads(r["SCHEDULE_CM"])
            assert float(r["M3_SCHEDULE"]) == pytest.approx(sc[0] * sc[1] / 1e4 * h[r["FLOOR"]], abs=1e-6)


# ------------------------------------------------------------------ conservation and lanes
def test_concrete_and_steel_conserved(s):
    rec = rows("11_CONCRETE_AND_STEEL_RECONCILIATION.csv")
    s9 = J(S9 / "14_RELEASE_SUMMARY.json")
    for trade, key in (("CONCRETE", "released_concrete_m3_by_family"),
                       ("REINFORCEMENT", "released_reinforcement_kg_by_family")):
        fam = {r["FAMILY"]: r for r in rec if r["TRADE"] == trade and r["S9A_DELTA"] != "" and r["FAMILY"] != "TOTAL"}
        assert set(fam) == set(s9[key])
        for k, r in fam.items():
            assert float(r["S9A_DELTA"]) == 0 and float(r["S9A_RELEASED"]) == float(r["S9_RELEASED"]) == s9[key][k]
        tot = next(r for r in rec if r["TRADE"] == trade and r["FAMILY"] == "TOTAL")
        assert math.fsum(float(r["S9A_RELEASED"]) for r in fam.values()) == pytest.approx(
            float(tot["S9A_RELEASED"]), abs=1e-5)
    assert all(c["RESULT"] == "PASS" for c in rows("15_CONSERVATION_CHECKS.csv"))
    assert len(rows("15_CONSERVATION_CHECKS.csv")) == 17


def test_no_conditional_value_leaks_into_a_released_total(bands):
    rec = rows("11_CONCRETE_AND_STEEL_RECONCILIATION.csv")
    for r in rec:
        if r["S9A_CONDITIONAL_LOW"] or r["S9A_CONDITIONAL_HIGH"]:
            assert r["S9A_RELEASED"] == "" and r["S9A_DELTA"] == ""
    assert all(not r.get("RELEASED_M3") or float(r["RELEASED_M3"]) == 0 for r in rows("05_BEAM_CONVENTION_COMPARISON.csv"))
    assert all(float(b["RELEASED_M3"]) == 0 for b in bands)
    total = next(float(r["S9A_RELEASED"]) for r in rec if r["TRADE"] == "CONCRETE" and r["FAMILY"] == "TOTAL")
    assert total == pytest.approx(158.070256, abs=1e-6)


def test_a_missing_dimension_is_never_zero(beams):
    miss = [b for b in beams if b["MISSING"]]
    assert miss and all(b["V_TOTAL_DEPTH_M3"] == "" == b["V_BELOW_SLAB_M3"] for b in miss)
    assert all(b["V_TOTAL_DEPTH_M3"] != "" for b in beams if not b["MISSING"] and
               not b["S9A_STATE"].startswith(("RE_OWNED", "BLOCKED")))
    rfi = {r["RFI_ID"]: r for r in rows("13_ENGINEER_RFI_REGISTER.csv")}
    assert rfi["RFI-A09"]["UNLOCKS_M3_LOW"] == "" == rfi["RFI-A09"]["UNLOCKS_M3_HIGH"]
    assert rfi["RFI-A03"]["UNLOCKS_KG"] == ""


def test_rfis_problem_types_and_unlock_ranking():
    rfi = rows("13_ENGINEER_RFI_REGISTER.csv")
    assert len(rfi) == 10 == len({r["RFI_ID"] for r in rfi})
    assert all(r["PROBLEM_TYPE"].startswith(("INTERPRETATION", "MISSING_SOURCE_INFORMATION")) and r["EFFECT"]
               for r in rfi)
    un = rows("14_UNLOCK_RANKING.csv")
    up = [f(r["UNLOCKS_M3_HIGH"]) if f(r["UNLOCKS_M3_HIGH"]) is not None else (f(r["UNLOCKS_M3_LOW"]) or 0.0)
          for r in un]
    assert up == sorted(up, reverse=True)
    assert un[0]["RFI_ID"] == "RFI-A01" and un[0]["RANK_CONCRETE"] == "1"
    assert next(r for r in un if r["RANK_STEEL"] == "1")["RFI_ID"] == "RFI-A02"


# ------------------------------------------------------------------ E. visual package
def _parents(root):
    return {c: p for p in root.iter() for c in p}


def _pts(s):
    return [tuple(float(v) for v in xy.split(",")) for xy in s.split()]


def test_visual_band_coordinates_match_the_register(bands):
    reg = {b["BAND_ID"]: (b["SHEET"], json.loads(b["POLYGON_LOCAL_MM"])) for b in bands}
    seen = Counter()
    for p in sorted((PKG / "visual").glob("*.svg")):
        root = ET.parse(p).getroot()
        par = _parents(root)
        for el in root.iter():
            bid = el.get("data-band")
            if not bid:
                continue
            g = par[el]
            while g is not None and g.get("data-view") is None:
                g = par.get(g)
            assert g is not None, (p.name, bid)
            v = json.loads(g.get("data-view"))
            sheet, poly = reg[bid]
            assert sheet in g.get("data-sheet"), (p.name, bid)
            got = [(x / v["k"] + v["x0"], v["y1"] - y / v["k"]) for x, y in _pts(el.get("points"))]
            tol = 0.006 / v["k"] + 1e-6
            assert len(got) == len(poly)
            for (a, b), (c, d) in zip(got, poly):
                assert abs(a - c) <= tol and abs(b - d) <= tol, (p.name, bid)
            seen[p.name] += 1
    assert seen["03_BAND_DETAILS.svg"] == 8 and seen["03_BANDS_ON_PLAN.svg"] == 8
    assert sum(v for k, v in seen.items() if k.startswith("02_LOCATION_MAP")) == 8


def test_visual_footings_and_beam_markers_sit_at_register_positions():
    focc = {r["footing_id"]: r["outline"]["bbox"] for r in J(S1 / "FOOTING_OCCURRENCE_REGISTER.json")["rows"]
            if r.get("outline") and r["outline"].get("bbox")}
    tags = {r["beam_id"]: r["tag_position_mm"] for r in J(S1 / "BEAM_OCCURRENCE_REGISTER.json")["rows"]
            if r.get("tag_position_mm")}
    n_f = n_b = 0
    for p in sorted((PKG / "visual").glob("02_LOCATION_MAP_*.svg")):
        root = ET.parse(p).getroot()
        par = _parents(root)
        for el in root.iter():
            g = par.get(el)
            while g is not None and g.get("data-view") is None:
                g = par.get(g)
            if g is None:
                continue
            v = json.loads(g.get("data-view"))
            tol = 0.006 / v["k"] + 1e-6
            if el.tag == SVG + "rect" and el.get("data-id") in focc:
                a, b, c, d = focc[el.get("data-id")]
                x, y = float(el.get("x")) / v["k"] + v["x0"], v["y1"] - float(el.get("y")) / v["k"]
                assert abs(x - a) <= tol and abs(y - d) <= tol
                assert abs(float(el.get("width")) / v["k"] - (c - a)) <= 2 * tol
                n_f += 1
            if el.get("data-beam") in tags:
                m = re.match(r"M([-\d.]+) ([-\d.]+)", el.get("d"))
                x, y = float(m.group(1)) / v["k"] + v["x0"], v["y1"] - (float(m.group(2)) + 5) / v["k"]
                tx, ty = tags[el.get("data-beam")]
                assert abs(x - tx) <= tol and abs(y - ty) <= tol + 1e-3
                n_b += 1
    assert n_f == len(focc) and n_b > 80


def test_visual_labels_index_and_page():
    idx = J(PKG / "visual" / "VISUAL_INDEX.json")
    files = {x["file"] for x in idx["figures"]}
    assert files == {p.name for p in (PKG / "visual").glob("*.svg")} and len(files) == 20
    html = (PKG / "visual" / "S9A_VISUAL_QA.html").read_text(encoding="utf-8")
    for x in idx["figures"]:
        assert x["labels"] and set(x["labels"]) <= LABELS
        root = ET.parse(PKG / "visual" / x["file"]).getroot()
        assert {el.get("data-label") for el in root.iter() if el.get("data-label")} == set(x["labels"])
        assert f'data-figure="{x["figure"]}"' in html and f'id="{x["figure"]}"' in html
    for n in range(1, 11):
        assert f'id="s{n}"' in html
    assert "<script" in html and "localStorage" in html and "try{" in html
    m = J(MANIFEST)
    assert {f"visual/{n}" for n in files} | {"visual/S9A_VISUAL_QA.html", "visual/VISUAL_INDEX.json"} <= \
        set(m["outputs"])


def test_hygiene():
    for p in sorted(list(PKG.iterdir()) + list((PKG / "visual").iterdir())):
        if p.is_file() and p.suffix in (".md", ".csv", ".json", ".jsonl", ".svg", ".html"):
            assert not HYG.search(p.read_text(encoding="utf-8")), p.name


def test_rebuild_byte_identical():
    m = J(MANIFEST)
    before = {k: (PKG / k).read_bytes() for k in m["outputs"]}
    before[MANIFEST.name] = MANIFEST.read_bytes()
    subprocess.run([sys.executable, "-I", str(PKG / "build_s9a.py")], check=True, cwd=ROOT, capture_output=True,
                   timeout=900)
    after = {k: (PKG / k).read_bytes() for k in before}
    assert before == after
