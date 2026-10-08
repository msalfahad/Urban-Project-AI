"""S7 package (research/alsenan_slab_rebar_s7): restricted project-basis slab rebar QTO over frozen PRE-S7.1.

Claims are re-derived here from the package's own registers, the frozen PRE-S7.1 / PRE-S7 registers and the frozen
S1 panel polygons - never against a reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from engine.source import delta_release as DR
from engine.source import slab_qto_authority as Q
from engine.source import slab_rebar_qto as S7

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_slab_rebar_s7"
P71 = ROOT / "research" / "alsenan_slab_rebar_pre_s7_1"
PRE = ROOT / "research" / "alsenan_slab_rebar_pre_s7"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
OUTPUTS = ["00_README.md", "01_S7_RELEASE_ITEMS.csv", "02_S7_BLOCKED_ITEMS.csv", "03_S7_COMPONENT_SUMMARY.csv",
           "04_S7_BAR_RUNS.csv", "05_S7_PANEL_SUMMARY.csv", "06_S7_SUPPORT_SUMMARY.csv", "07_S7_FLOOR_SUMMARY.csv",
           "08_S7_DIAMETER_SUMMARY.csv", "09_S7_PROJECT_SUMMARY.json", "10_S7_PROVENANCE.jsonl",
           "11_S7_1_CANDIDATES.csv"]
TANK = {"SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02"}
LIGHTWELL = "SP-GF_ROOF_SLAB-21"
OVERRIDE_SUPPORT = "SUP-GF_ROOF_SLAB-037"
OVERRIDDEN_TOP = ("P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax", "P15-TOP-EXTEND-50PCT")
TOL = 1e-6


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, base=PKG):
    with open(base / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def js(v):
    return json.loads(v) if v not in ("", None) else None


def f(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def rel():
    return rows("01_S7_RELEASE_ITEMS.csv")


@pytest.fixture(scope="module")
def blk():
    return rows("02_S7_BLOCKED_ITEMS.csv")


@pytest.fixture(scope="module")
def runs():
    return rows("04_S7_BAR_RUNS.csv")


@pytest.fixture(scope="module")
def comps():
    return rows("03_S7_COMPONENT_SUMMARY.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "09_S7_PROJECT_SUMMARY.json")


@pytest.fixture(scope="module")
def cands():
    return rows("11_S7_RELEASE_CANDIDATES.csv", P71)


@pytest.fixture(scope="module")
def strips():
    return {r["LOCAL_BAR_STRIP_ID"]: r for r in rows("07_LOCAL_BAR_STRIPS.csv", P71)}


@pytest.fixture(scope="module")
def s1():
    return {r["panel_id"]: r for r in J(S1 / "SLAB_PANEL_REGISTER.json")["rows"]}


@pytest.fixture(scope="module")
def census():
    return {r["SLAB_PANEL_ID"]: r for r in rows("01_SLAB_PANEL_CENSUS.csv", PRE)}


def area_m2(s1, p):
    r = s1[p]
    return (Q.polygon_area(r["polygon_mm"]) - sum(Q.polygon_area(h) for h in r["holes_mm"] or [])) / 1e6


# ------------------------------------------------------------------ package / freeze / blindness
def test_deliverables_exist():
    for n in OUTPUTS + ["12_S7_FREEZE_MANIFEST.json", "TEST_RUN.md", "build_s7.py"]:
        assert (PKG / n).is_file(), n


def test_freeze_manifest_still_matches():
    m = J(PKG / "12_S7_FREEZE_MANIFEST.json")
    assert m["round"] == "S7" and m["state"] == "FROZEN_BEFORE_REFERENCE_COMPARISON"
    assert m["references_read_before_freeze"] == [] and m["baseline"] == "ac7a477"
    assert set(m["outputs"]) == set(OUTPUTS)
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG), ("decision_records", ROOT),
                        ("candidate_registers", ROOT)):
        assert m[group], group
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    assert DR.verify_frozen(PKG / "12_S7_FREEZE_MANIFEST.json", ROOT)["round"] == "S7"
    assert not any("post_freeze" in k for g in ("code", "inputs", "outputs") for k in m[g])


def test_eleven_frozen_stages_still_match():
    m = J(PKG / "12_S7_FREEZE_MANIFEST.json")
    assert set(m["frozen_baselines"]) == {"S4", "S4.1", "S5", "S6", "S6.1", "S5.1", "AD1", "D1.1", "D1.2", "PRE-S7",
                                          "PRE-S7.1"}
    mans = [i for i in m["inputs"] if i.endswith("FREEZE_MANIFEST.json")]
    assert len(mans) == 11
    for i in mans:
        assert hashlib.sha256((ROOT / i).read_bytes()).hexdigest() in m["frozen_baselines"].values()
        DR.verify_frozen(ROOT / i, ROOT)


def test_builder_is_blind():
    src = (PKG / "build_s7.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "U-C4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze_comparison", "rebar_truth", "source_exhaustion_04", "rough_rebar", "kg/m3 profile",
                "90 kg", "150 kg", "benchmark", "DONORS", "donor/", "alsenan_rebar_v3", "alsenan_rebar_v4", "ezdxf",
                "by_sha256", "rebar_sanity", "Quotation", "pricing", ".xlsx"):
        assert bad not in src, bad
    for line in src.splitlines():
        if line.startswith(("import ", "from ")):
            assert line.split()[1] in ("__future__", "csv", "hashlib", "importlib.util", "io", "json", "math", "sys",
                                       "collections", "pathlib", "engine.source"), line
    code = [ln for ln in src.splitlines() if "post_freeze" in ln]
    assert all("`post_freeze/`" in ln for ln in code), code          # named in the README text only, never opened


def test_firewall_registry_lists_s7():
    reg = (ROOT / "tests" / "structural_comparison_engine" / "rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"engine/source/slab_rebar_qto.py"' in reg
    assert '"research/alsenan_slab_rebar_s7/build_s7.py"' in reg


def test_rebuild_is_byte_identical():
    m = J(PKG / "12_S7_FREEZE_MANIFEST.json")
    before = {k: (PKG / k).read_bytes() for k in list(m["outputs"]) + ["12_S7_FREEZE_MANIFEST.json"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s7.py")], check=True, capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


# ------------------------------------------------------------------ population (§1, §4, §28)
def test_candidate_only_release(rel, cands, summary):
    ids = [r["PRE_S7_1_CANDIDATE_ID"] for r in rel]
    assert len(ids) == len(set(ids)) == 476 == summary["candidate_population"] == summary["released_items"]
    assert set(ids) == {c["QTO_ITEM_ID"] for c in cands}
    assert summary["blocked_candidates"] == 0
    assert len({r["COMPONENT_ID"] for r in rel}) == 309 == summary["released_components"]
    by = {c["QTO_ITEM_ID"]: c for c in cands}
    for r in rel:
        c = by[r["PRE_S7_1_CANDIDATE_ID"]]
        assert r["COMPONENT_ID"] == c["PARENT_COMPONENT_ID"] and r["DIRECTION"] == c["DIRECTION"]
        assert int(r["DIAMETER_MM"]) == int(c["DIA_MM"]) and f(r["RATE_PER_M"]) == f(c["RATE_PER_M"])
        assert f(r["DENSITY_FRACTION"]) == f(c["DENSITY_FRACTION"])


def test_every_pre_s7_1_item_terminates_once(rel, blk):
    items = [json.loads(x)["record"] for x in open(P71 / "12_PROVENANCE.jsonl", encoding="utf-8")
             if json.loads(x)["kind"] == "ITEM"]
    seen = Counter([r["PRE_S7_1_CANDIDATE_ID"] for r in rel] + [b["PRE_S7_1_ITEM_ID"] for b in blk
                                                                 if b["PRE_S7_1_ITEM_ID"]])
    assert set(seen) == {i["QTO_ITEM_ID"] for i in items} and len(items) == 1210
    assert all(v == 1 for v in seen.values())
    lanes = Counter(b["S7_LANE"] for b in blk)
    assert set(lanes) <= set(S7.NO_MASS_LANES)
    assert {r["S7_LANE"] for r in rel} == {S7.PROJECT_BASIS_QTO}


def test_components_terminate_in_one_of_six_lanes(comps):
    assert Counter(c["S7_TERMINAL_LANE"] for c in comps) == {"PROJECT_BASIS_QTO": 309, "BLOCKED_UNQUANTIFIED": 156,
                                                            "EXCLUDED_SPECIAL_STRUCTURE": 18, "SOURCE_CONFLICT": 5}
    assert {c["S7_TERMINAL_LANE"] for c in comps} <= set(S7.LANES)
    assert len({c["COMPONENT_ID"] for c in comps}) == len(comps)
    for c in comps:
        if c["S7_TERMINAL_LANE"] != S7.PROJECT_BASIS_QTO:
            assert c["KG"] == "" and int(c["RELEASED_ITEMS"]) == 0, c["COMPONENT_ID"]
        else:
            assert f(c["KG"]) > 0
    rd = {r["COMPONENT_ID"]: r["AD2_STATE"] for r in rows("08_UPDATED_COMPONENT_READINESS.csv", P71)}
    for c in comps:
        if c["COMPONENT_ID"] in rd:
            assert {"RELEASED_ALL": "RELEASED_ALL", "RELEASED_PARTIAL": "RELEASED_PARTIAL",
                    "TRANSFERRED_S8": "EXCLUDED_S8"}.get(rd[c["COMPONENT_ID"]], c["S7_STATE"]) == c["S7_STATE"]


# ------------------------------------------------------------------ rate density (§5, §6)
def test_rate_density_formula_on_every_item(rel):
    for r in rel:
        rate, frac, W = f(r["RATE_PER_M"]), f(r["DENSITY_FRACTION"]), f(r["TRANSVERSE_WIDTH_M"])
        L = f(r["EQUIVALENT_TOTAL_LENGTH_M"])
        run = f(r["RUN_LENGTH_M"]) + f(r["EXTENSION_LENGTH_M"])
        assert abs(f(r["EQUIVALENT_BAR_COUNT"]) - rate * frac * W) <= 1e-8, r["S7_ITEM_ID"]
        assert abs(L - rate * frac * W * run) <= 1e-6 * max(L, 1.0), r["S7_ITEM_ID"]
        assert r["PHYSICAL_BBS_COUNT"] == "UNRESOLVED" and r["EXPLICIT_COUNT"] == ""


def test_no_integer_rounding_and_no_plus_one(rel):
    counts = [f(r["EQUIVALENT_BAR_COUNT"]) for r in rel]
    assert sum(abs(c - round(c)) > 1e-6 for c in counts) > 100          # densities, not whole bars
    for r in rel:
        c = f(r["EQUIVALENT_BAR_COUNT"])
        exact = f(r["RATE_PER_M"]) * f(r["DENSITY_FRACTION"]) * f(r["TRANSVERSE_WIDTH_M"])
        assert abs(c - exact) <= 1e-8 and abs(c - (exact + 1)) > 0.5      # never N x W + 1
        assert abs(c - math.ceil(exact)) > 1e-9 or abs(exact - math.ceil(exact)) <= 1e-9


def test_unit_mass_d2_over_162(rel, summary):
    for r in rel:
        d = int(r["DIAMETER_MM"])
        assert abs(f(r["UNIT_MASS_KG_M"]) - d * d / 162.0) <= 1e-9
        assert abs(f(r["KG"]) - f(r["EQUIVALENT_TOTAL_LENGTH_M"]) * d * d / 162.0) <= 1e-6 * max(f(r["KG"]), 1.0)
    assert not summary["flags"]["kg_per_m2_or_m3_factor_used"]


def test_rate_times_rectangle_on_rectangular_panels(rel, runs, strips):
    by_item = defaultdict(list)
    for x in runs:
        by_item[x["S7_ITEM_ID"]].append(x)
    n = 0
    for r in rel:
        if r["BAR_ROLE"] in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50") and r["IRREGULAR_PANEL"] == "False":
            xs = by_item[r["S7_ITEM_ID"]]
            for x in xs:
                s = strips[x["STRIP_ID"]]
                L0, L1 = js(s["LOCAL_CLEAR_SPAN_MM"])                # face to face (a chamfer strip is a trapezoid)
                assert abs(f(x["RUN_LENGTH_MM"]) - 0.5 * (L0 + L1)) <= 0.1
            W = sum(f(x["STRIP_WIDTH_MM"]) for x in xs) / 1000.0
            runs_ = {round(f(x["RUN_LENGTH_MM"]), 3) for x in xs}
            if len(runs_) == 1:                                   # a true rectangle: rate x width x run
                n += 1
                assert abs(f(r["EQUIVALENT_TOTAL_LENGTH_M"]) - S7.rectangle_length_m(
                    f(r["RATE_PER_M"]), W, runs_.pop() / 1000.0, fraction=f(r["DENSITY_FRACTION"]))) <= 1e-6
    assert n >= 30


# ------------------------------------------------------------------ local strips (§7, §14)
def test_bar_runs_use_the_pre_s7_1_strips(runs, strips):
    for x in runs:
        s = strips[x["STRIP_ID"]]
        assert x["PANEL_ID"] == s["PANEL"] and x["DIRECTION"] == s["BAR_DIRECTION"]
        assert abs(f(x["STRIP_WIDTH_MM"]) - f(s["STRIP_WIDTH_MM"])) <= 0.05 + 1e-9    # 07 prints 0.1 mm
        L0, L1 = js(s["LOCAL_CLEAR_SPAN_MM"])
        assert abs(f(x["BASE_RUN_MM"]) - 0.5 * (L0 + L1)) <= 0.1 or x["BAR_ROLE"].endswith("CROSSING")
        assert int(x["OPENING_INTERSECTION"]) == int(s["OPENING_INTERSECTIONS"]) == 0
        for k in ("START_BOUNDARY", "END_BOUNDARY", "SUPPORT_RELATION"):
            assert x[k]


def test_strip_integration_reconciles_to_panel_geometry(runs, s1, census):
    full = defaultdict(float)                     # density-1 footprint of each panel and direction
    seen = set()
    for x in runs:
        if x["BAR_ROLE"] in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50") and x["STRIP_ID"] not in seen:
            seen.add(x["STRIP_ID"])
            full[(x["PANEL_ID"], x["DIRECTION"])] += f(x["STRIP_WIDTH_MM"]) * f(x["BASE_RUN_MM"]) / 1e6
    assert len(full) == 90
    for (p, d), v in full.items():
        assert abs(v - area_m2(s1, p)) <= 1e-4 * max(1.0, area_m2(s1, p)), (p, d)
    irregular = {p for p, d in full if census[p]["RECTANGULARITY"] and float(census[p]["RECTANGULARITY"]) < 0.9999}
    assert irregular                                # irregular panels are measured by strips, not bounding boxes
    for p in irregular:
        x0, y0, x1, y1 = (min(q[0] for q in s1[p]["polygon_mm"]), min(q[1] for q in s1[p]["polygon_mm"]),
                          max(q[0] for q in s1[p]["polygon_mm"]), max(q[1] for q in s1[p]["polygon_mm"]))
        bbox = (x1 - x0) * (y1 - y0) / 1e6
        for d in ("X", "Y"):
            if (p, d) in full:
                assert full[(p, d)] < bbox - 1e-3


def test_bottom_family_covers_its_panel_exactly_once(rel, s1):
    fam = defaultdict(lambda: defaultdict(float))
    rate = {}
    for r in rel:
        if r["OWNER_KIND"] == "PANEL":
            k = (r["PANEL_ID"], r["DIRECTION"])
            fam[k][r["BAR_ROLE"]] += f(r["EQUIVALENT_TOTAL_LENGTH_M"])
            rate[k] = f(r["RATE_PER_M"])
    for k, v in fam.items():
        assert abs(v.get("BOTTOM_IN_PANEL", 0) + 2 * v.get("BOTTOM_CONTINUING_50", 0) -
                   rate[k] * area_m2(s1, k[0])) <= 1e-4 * rate[k] * area_m2(s1, k[0]), k
        assert v.get("BOTTOM_CURTAILED_50", 0) <= v.get("BOTTOM_CONTINUING_50", 0) + 1e-9


def test_strips_do_not_overlap(runs):
    by = defaultdict(list)
    for x in runs:
        layer = "TOP" if x["BAR_ROLE"].startswith("TOP") else "BOTTOM"
        if layer == "BOTTOM" and x["BAR_ROLE"] not in ("BOTTOM_SUPPORT_CROSSING",):
            if x["BAR_ROLE"] == "BOTTOM_CURTAILED_50":
                continue                                          # the curtailed half lies inside the continuing one
        reg = js(x["REGION_TS_MM"])
        by[(x["FLOOR"], x["DIRECTION"], layer, x["BAR_ROLE"] == "BOTTOM_IN_PANEL" or
            x["BAR_ROLE"] == "BOTTOM_CONTINUING_50")].append((x["BAR_RUN_ROW_ID"], *reg))
    for k, regs in by.items():
        assert S7.strip_overlaps(regs, tol=0.5) == [], k
    # the in-panel footprint and the crossings of one floor / direction never overlap either
    merged = defaultdict(list)
    for (fl, d, layer, _), regs in by.items():
        merged[(fl, d, layer)] += regs
    for k, regs in merged.items():
        assert S7.strip_overlaps(regs, tol=0.5) == [], k


# ------------------------------------------------------------------ 50 / 50 and 0.125 L (§8, §9)
def test_fifty_plus_fifty_is_one_hundred(runs):
    dens = defaultdict(float)
    for x in runs:
        if x["BAR_ROLE"] in ("BOTTOM_IN_PANEL", "BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50"):
            dens[x["STRIP_ID"]] += f(x["DENSITY_FRACTION"])
    assert dens and all(abs(v - 1.0) <= 1e-12 for v in dens.values())
    for x in runs:
        if x["BAR_ROLE"] in ("BOTTOM_CONTINUING_50", "BOTTOM_CURTAILED_50", "BOTTOM_SUPPORT_CROSSING"):
            assert f(x["DENSITY_FRACTION"]) == 0.5


def test_curtailed_runs_use_the_frozen_0125L(runs, strips):
    stopping = ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT", "END_UNRESOLVED", "END_OBLIQUE",
                "END_NO_SUPPORT_RECORD")
    for x in runs:
        if x["BAR_ROLE"] != "BOTTOM_CURTAILED_50":
            continue
        s = strips[x["STRIP_ID"]]
        n = sum(s[k] in stopping for k in ("START_CONDITION", "END_CONDITION"))
        base = f(x["BASE_RUN_MM"])
        assert int(x["STOPPING_ENDS"]) == n
        assert abs(f(x["CURTAILMENT_DEDUCTION_MM"]) - 0.125 * n * base) <= 1e-6 * base
        assert abs(f(x["RUN_LENGTH_MM"]) - base * (1 - 0.125 * n)) <= 1e-6 * base


def test_curtailment_authority_is_split(rel):
    cur = [r for r in rel if r["BAR_ROLE"] == "BOTTOM_CURTAILED_50"]
    assert len(cur) == 87
    for r in cur:
        assert f(r["SOURCE_RATIO"]) == 0.125 and r["SOURCE_RATIO_RULE"] == "P15-BOT-STOP-0.125L"
        assert r["SOURCE_RATIO_AUTHORITY"] == "PROJECT_SOURCE"
        assert r["SPAN_BASIS_AUTHORITY"] == r["MEASUREMENT_ORIGIN_AUTHORITY"] == "PROJECT_SOURCE"
        assert r["MEASUREMENT_ORIGIN"] == "FACE_OF_SUPPORT" and r["SPAN_BASIS"].startswith("CLEAR_SPAN")
        assert "P15-BOT-STOP-0.125L" in js(r["SOURCE_RULE_IDS"]) and "PROJECT_SOURCE" in r["DENSITY_AUTHORITY"]
        assert (Q.URBAN_LOCAL_BAR_LINE_RULE + " (AD2-D14)" in js(r["URBAN_RULE_IDS"])) == (r["IRREGULAR_PANEL"] ==
                                                                                           "True")
        assert abs(f(r["CALCULATED_EXTENT_M"]) - f(r["CURTAILMENT_DEDUCTION_M"])) <= 1e-12


# ------------------------------------------------------------------ top bars (§2, §10, §11, §12)
def test_one_third_is_project_source_and_the_face_origin_is_urban(rel, runs):
    ext = [r for r in rel if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION"]
    assert len(ext) == 215
    for r in ext:
        assert abs(f(r["SOURCE_RATIO"]) - 1 / 3) <= 1e-9 and r["SOURCE_RATIO_AUTHORITY"] == "PROJECT_SOURCE"
        assert r["SOURCE_RATIO_RULE"] == "P4-6-NOTE-2-TOP-OVER-BEAMS"
        assert r["MEASUREMENT_ORIGIN"].startswith("SUPPORT_FACE")
        assert r["MEASUREMENT_ORIGIN_AUTHORITY"] == r["SPAN_BASIS_AUTHORITY"] == "URBAN_OWNER_MEASUREMENT_RULE"
        assert Q.URBAN_TOP_EXTENT_RULE in js(r["URBAN_RULE_IDS"])
        assert Q.URBAN_TOP_EXTENT_RULE not in (r["SOURCE_RATIO_RULE"], r["SOURCE_RATIO_AUTHORITY"])
        assert f(r["RUN_LENGTH_M"]) == 0 and abs(f(r["CALCULATED_EXTENT_M"]) - f(r["EXTENSION_LENGTH_M"])) <= 1e-12
    for x in runs:
        if x["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION":
            assert abs(f(x["EXTENSION_LENGTH_MM"]) - f(x["BASE_RUN_MM"]) / 3.0) <= 1e-6
            assert x["END_USED"] in ("START", "END")


def test_same_role_generic_rule_never_added(rel, runs):
    for r in rel:
        assert not set(js(r["SOURCE_RULE_IDS"])) & set(OVERRIDDEN_TOP), r["S7_ITEM_ID"]
        assert "0.25" not in r["LENGTH_AUTHORITY"] and "0.30" not in r["LENGTH_AUTHORITY"]
    top = [(r["SUPPORT_ID"], r["BAR_ROLE"], r["PANEL_ID"]) for r in rel if r["LAYER"] == "TOP"]
    assert S7.duplicates(top) == []
    for role in ("TOP_OVER_SUPPORT_EXTENSION", "TOP_SUPPORT_CROSSING"):
        ends = [(x["STRIP_ID"], x["END_USED"]) for x in runs if x["BAR_ROLE"] == role]
        assert S7.duplicates(ends) == [], role                # NO_SUPPORT_TOP_BAR_DOUBLE_COUNT


def test_top_steel_is_owned_by_the_support(rel):
    sup = {r["SUPPORT_ID"]: r for r in rows("06_S7_SUPPORT_SUMMARY.csv")}
    owned = defaultdict(float)
    for r in rel:
        if r["LAYER"] == "TOP" or r["BAR_ROLE"] == "BOTTOM_SUPPORT_CROSSING":
            assert r["OWNER_KIND"] == "SUPPORT" and r["OWNER"] == r["SUPPORT_ID"]
            owned[r["SUPPORT_ID"]] += f(r["KG"])
        else:
            assert r["OWNER_KIND"] == "PANEL" and r["OWNER"] == r["PANEL_ID"] and r["SUPPORT_ID"] == ""
    for sid, kg in owned.items():
        assert abs(f(sup[sid]["SUPPORT_OWNED_KG"]) - kg) <= 1e-6


def test_local_top_override_carries_no_kg_and_no_general_bar(rel, blk, summary):
    # the 3Ø16/Top replaces the plan-note-2 TOP bar there; the bottom bars crossing the same beam are another role
    assert not [r for r in rel if r["SUPPORT_ID"] == OVERRIDE_SUPPORT and r["LAYER"] == "TOP"]
    ov = [b for b in blk if b["ITEM"] == "TOP_LOCAL_OVERRIDE_GROUP"]
    assert len(ov) == 1 and ov[0]["SUPPORT_ID"] == OVERRIDE_SUPPORT and ov[0]["EXPLICIT_COUNT"] == "3"
    assert ov[0]["COUNT_RELEASED"] == "True" and ov[0]["KG"] == "" and ov[0]["DIA_MM"] == "16"
    assert summary["totals_kg"]["LOCAL_TOP_EXPLICIT_KG"] == 0.0
    assert S7.explicit_count_mass(3, 16, count_authority=S7.PROJECT_SOURCE,
                                  length_authority=S7.AUTHORITY_BLOCKED)["kg"] is None


def test_explicit_counts_carry_no_kg(blk):
    ex = [b for b in blk if b["COUNT_BASIS"] == "SOURCE_EXPLICIT_COUNT"]
    assert len(ex) == 5 and all(b["KG"] == "" and b["COUNT_RELEASED"] == "True" for b in ex)
    assert all(b["RATE_PER_M"] == "" for b in ex)                # a finite count is never a per-metre rate


# ------------------------------------------------------------------ crossings, mismatch, lap (§13, §14)
def test_crossings_are_the_frozen_candidates(rel):
    c = Counter(r["BAR_ROLE"] for r in rel)
    assert c["TOP_SUPPORT_CROSSING"] == 55 and c["BOTTOM_SUPPORT_CROSSING"] == 25
    assert S7.duplicates([(r["SUPPORT_ID"], r["PANEL_ID"], r["DIRECTION"], r["BAR_ROLE"]) for r in rel
                          if r["BAR_ROLE"].endswith("CROSSING")]) == []
    for r in rel:
        if r["BAR_ROLE"].endswith("CROSSING"):
            a, b = r["PANEL_ID"].split("|")
            assert a < b                                           # counted from the lower-id face only


def test_mismatch_supports_split_left_right(rel, blk):
    splits = rows("06_SUPPORT_MISMATCH_SPLITS.csv", P71)
    assert len(splits) == 32 and len({s["SUPPORT_ID"] for s in splits}) == 31
    bx = {(r["SUPPORT_ID"], r["PANEL_ID"], r["DIRECTION"]) for r in rel if r["BAR_ROLE"] == "BOTTOM_SUPPORT_CROSSING"}
    inpanel = {(r["PANEL_ID"], r["DIRECTION"]) for r in rel if r["OWNER_KIND"] == "PANEL"}
    trans = {(b["OWNER"], b["DIRECTION"]) for b in blk if b["ITEM"] == "BOTTOM_TRANSITION"}
    for s in splits:
        d = s["BAR_DIRECTION"]
        assert (s["SUPPORT_ID"], f"{s['LEFT_PANEL']}|{s['RIGHT_PANEL']}", d) not in bx
        for side in ("LEFT", "RIGHT"):
            if "(RESOLVED)" in s[f"{side}_SPEC"]:
                assert (s[f"{side}_PANEL"], d) in inpanel          # each side keeps its own run to the face
                # its transition is blocked (recorded at the support record of its own view: one beam can carry
                # two records, PRE-S7 C-10)
                assert (s[f"{side}_PANEL"], d) in trans


def test_no_hidden_lap(rel, blk):
    for r in rel:
        for bad in ("LAP", "SPLICE", "TRANSITION", "DEVELOPMENT", "ANCHORAGE", "HOOK"):
            assert bad not in r["BAR_ROLE"]
    kinds = Counter(b["ITEM"] for b in blk)
    assert kinds["BOTTOM_TRANSITION"] == 59 and kinds["BOTTOM_RUN_LAP_SPLICE"] == 15
    assert all(b["KG"] == "" for b in blk if b["CATEGORY"] == "TRANSITION_LAP_SPLICE")


# ------------------------------------------------------------------ cover, temperature, sunken, S8 (§15-§19)
def test_minimum_25mm_cover_and_40cl_never_used(rel, summary):
    for r in rel:
        txt = " ".join(r.values())
        assert "MINIMUM_PROJECT_COVER" not in txt and "40 CL" not in txt and "25 mm" not in txt
        assert r["S7_LANE"] == "PROJECT_BASIS_QTO"
    assert summary["project_basis_numeric_items"] == 0 and summary["source_derived_physical_items"] == 0
    assert S7.cover_portion(True)["lane"] == S7.PROJECT_BASIS_NUMERIC


def test_anchorage_and_end_cover_stay_blocked(blk, summary):
    a = [b for b in blk if b["CATEGORY"] == "ANCHORAGE_END_COVER"]
    assert len(a) == 174 and all(b["KG"] == "" for b in a)
    assert summary["BLOCKED_ANCHORAGE_COMPONENTS"] == len({b["COMPONENT_ID"] for b in a})


def test_temperature_excluded(rel, blk, comps, summary):
    t = [b for b in blk if b["CATEGORY"] == "TEMPERATURE"]
    assert len(t) == 94 and all(b["KG"] == "" and b["S7_LANE"] == "BLOCKED_UNQUANTIFIED" for b in t)
    tc = {c["COMPONENT_ID"] for c in comps if c["COMPONENT"].startswith("TEMPERATURE")}
    assert not {r["COMPONENT_ID"] for r in rel} & tc
    assert summary["BLOCKED_TEMPERATURE_COMPONENTS"] == 94
    assert all(c["KG"] == "" for c in comps if c["COMPONENT_ID"] in tc)


def test_sunken_base_mesh_included_and_extras_blocked(rel, blk, summary):
    sunk = {"SP-1F_ROOF_SLAB-02", "SP-GF_ROOF_SLAB-04", "SP-GF_ROOF_SLAB-05", "SP-GF_ROOF_SLAB-12",
            "SP-GF_ROOF_SLAB-24", "SP-GF_ROOF_SLAB-29"}
    mesh = {r["PANEL_ID"] for r in rel if r["OWNER_KIND"] == "PANEL" and r["SUNKEN_PANEL"] == "True"}
    assert mesh == sunk and set(summary["sunken_panels_base_mesh_kg"]) == sunk
    ex = [b for b in blk if b["CATEGORY"] == "SUNKEN_EXTRA"]
    assert len(ex) == 18 and {b["OWNER"] for b in ex} == sunk and all(b["KG"] == "" for b in ex)
    assert Counter(b["ITEM"] for b in ex) == {"SUNKEN_STEP_VERTICAL_REBAR": 6, "SUNKEN_EDGE_EXTRA": 6,
                                              "LEVEL_CHANGE_DETAIL": 6}
    assert summary["BLOCKED_SUNKEN_EXTRA_COMPONENTS"] == 18


def test_water_tank_and_gf21_excluded(rel, blk, comps):
    for r in rel:
        touched = set(r["PANEL_ID"].split("|")) | {r["OWNER"]}
        assert not touched & (TANK | {LIGHTWELL}), r["S7_ITEM_ID"]
    ex = [c for c in comps if c["S7_TERMINAL_LANE"] == "EXCLUDED_SPECIAL_STRUCTURE"]
    assert len(ex) == 18 and all(c["KG"] == "" for c in ex)
    assert sum(c["OWNER"] in TANK or c["OWNER"].startswith("SUP-2F") for c in ex) == 17
    gf21 = [b for b in blk if b["S8_REGION"] == "STAIR_LIGHTWELL_REGION"]
    assert gf21 and all(b["S7_LANE"] == "EXCLUDED_SPECIAL_STRUCTURE" and b["KG"] == "" for b in gf21)
    assert any((b["CONFLICT_REF"] or "").startswith("C-01") for b in gf21)
    assert all(b["KG"] == "" for b in blk if b["S7_LANE"] == "EXCLUDED_SPECIAL_STRUCTURE")


# ------------------------------------------------------------------ openings, oblique, edges, conflicts (§20-§23)
def test_opening_clipping_and_trim_blocked(rel, runs, s1, census, blk):
    ins = [p for p, c in census.items() if c["SCOPE"] == "IN_SCOPE_S7"]
    assert all(not s1[p]["holes_mm"] for p in ins)              # no in-scope panel has an interior opening
    assert all(x["OPENING_INTERSECTION"] == "0" for x in runs)
    voids = {p for p, c in census.items() if c["SCOPE"] == "VOID_OR_OPENING"}
    assert not any(set(r["PANEL_ID"].split("|")) & voids for r in rel)
    trim = [b for b in blk if b["CATEGORY"] == "OPENING_TRIM"]
    assert len(trim) == 6 and all(b["KG"] == "" for b in trim)
    assert {b["OWNER"] for b in trim} == {"OP-SP-GF_ROOF_SLAB-09", "OP-SP-GF_ROOF_SLAB-13", "OP-SP-1F_ROOF_SLAB-06"}


def test_oblique_and_edge_blockers(blk, cands):
    cand = {c["QTO_ITEM_ID"] for c in cands}
    ob = [b for b in blk if "Q-OBLIQUE" in js(b["QUESTIONS"])]
    assert len(ob) == 44 and all(b["KG"] == "" and b["PRE_S7_1_ITEM_ID"] not in cand for b in ob)
    ed = [b for b in blk if b["ITEM"] == "TOP_AT_UNRECORDED_EDGE"]
    assert len(ed) == 24 and all(b["KG"] == "" and b["CATEGORY"] == "EDGE_WITHOUT_SUPPORT_RECORD" for b in ed)


def test_source_conflicts_stay_open(blk, summary):
    sc = [b for b in blk if b["S7_LANE"] == "SOURCE_CONFLICT"]
    assert len(sc) == 5 and all(b["KG"] == "" for b in sc)
    assert {b["CONFLICT_REF"].split()[0] for b in sc} == {"C-03", "C-04"}
    assert [c.split()[0] for c in summary["open_source_conflicts"]] == ["C-01", "C-03", "C-04", "C-06", "C-09"]


def test_blocked_items_carry_no_kg(blk):
    assert blk and all(b["KG"] == "" for b in blk)
    assert {b["S7_LANE"] for b in blk} <= set(S7.NO_MASS_LANES)


def test_s7_1_candidates_carry_zero_kg(rel, blk):
    s71 = rows("11_S7_1_CANDIDATES.csv")
    released = {r["PRE_S7_1_CANDIDATE_ID"] for r in rel}
    blocked = {b["PRE_S7_1_ITEM_ID"] for b in blk}
    assert s71 and all(f(r["KG_IN_S7"]) == 0.0 for r in s71)
    assert all(r["PRE_S7_1_ITEM_ID"] in blocked and r["PRE_S7_1_ITEM_ID"] not in released for r in s71)


# ------------------------------------------------------------------ reconciliation (§25-§28)
def test_bar_runs_reconcile_to_items(rel, runs):
    by = defaultdict(float)
    n = Counter()
    for x in runs:
        by[x["S7_ITEM_ID"]] += f(x["KG"])
        n[x["S7_ITEM_ID"]] += 1
    for r in rel:
        assert abs(by[r["S7_ITEM_ID"]] - f(r["KG"])) <= 1e-6 * max(f(r["KG"]), 1.0)
        assert n[r["S7_ITEM_ID"]] == int(r["STRIPS"])


def test_diameter_reconciliation(rel, summary):
    dia = rows("08_S7_DIAMETER_SUMMARY.csv")
    T = summary["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    for d in dia:
        rs = [r for r in rel if r["DIAMETER_MM"] == d["DIAMETER_MM"]]
        assert abs(sum(f(r["KG"]) for r in rs) - f(d["KG"])) <= 1e-6
        assert abs(sum(f(r["EQUIVALENT_TOTAL_LENGTH_M"]) for r in rs) - f(d["EQUIVALENT_LENGTH_M"])) <= 1e-6
        assert abs(f(d["PCT_OF_RESTRICTED_S7_KG"]) - 100 * f(d["KG"]) / T) <= 1e-6
    assert abs(sum(f(d["KG"]) for d in dia) - T) <= 1e-6
    assert abs(sum(f(d["PCT_OF_RESTRICTED_S7_KG"]) for d in dia) - 100.0) <= 1e-6


def test_floor_reconciliation(rel, summary):
    fl = {r["FLOOR"]: r for r in rows("07_S7_FLOOR_SUMMARY.csv")}
    assert set(fl) == {"GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB", "TOTAL"}
    for k in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB"):
        rs = [r for r in rel if r["FLOOR"] == k]
        assert abs(sum(f(r["KG"]) for r in rs) - f(fl[k]["PROJECT_BASIS_KG"])) <= 1e-6
        assert abs(f(fl[k]["PANEL_OWNED_KG"]) + f(fl[k]["SUPPORT_OWNED_KG"]) - f(fl[k]["PROJECT_BASIS_KG"])) <= 1e-6
        assert abs(f(fl[k]["BOTTOM_MAIN_KG"]) + f(fl[k]["TOP_SUPPORT_KG"]) - f(fl[k]["PROJECT_BASIS_KG"])) <= 1e-6
        assert int(fl[k]["RELEASED_ITEMS"]) == len(rs)
    T = summary["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    assert abs(f(fl["TOTAL"]["PROJECT_BASIS_KG"]) - T) <= 1e-6
    assert abs(sum(f(fl[k]["PROJECT_BASIS_KG"]) for k in ("GF_ROOF_SLAB", "1F_ROOF_SLAB", "2F_ROOF_SLAB")) - T) <= 1e-6


def test_project_reconciliation(rel, comps, summary):
    t = summary["totals_kg"]
    T = t["RESTRICTED_S7_PROJECT_BASIS_KG"]
    by = defaultdict(float)
    for r in rel:
        by[r["BAR_ROLE"]] += f(r["KG"])
    assert abs(t["BOTTOM_IN_PANEL_FULL_DENSITY_KG"] - by["BOTTOM_IN_PANEL"]) <= 1e-6
    assert abs(t["CONTINUING_BOTTOM_KG"] - by["BOTTOM_CONTINUING_50"]) <= 1e-6
    assert abs(t["CURTAILED_BOTTOM_KG"] - by["BOTTOM_CURTAILED_50"]) <= 1e-6
    assert abs(t["BOTTOM_SUPPORT_CROSSING_KG"] - by["BOTTOM_SUPPORT_CROSSING"]) <= 1e-6
    assert abs(t["TOP_EXTENSION_KG"] - by["TOP_OVER_SUPPORT_EXTENSION"]) <= 1e-6
    assert abs(t["TOP_SUPPORT_CROSSING_KG"] - by["TOP_SUPPORT_CROSSING"]) <= 1e-6
    assert abs(t["BOTTOM_MAIN_PROJECT_BASIS_KG"] - (t["BOTTOM_IN_PANEL_FULL_DENSITY_KG"] + t["CONTINUING_BOTTOM_KG"]
                                                    + t["CURTAILED_BOTTOM_KG"] + t["BOTTOM_SUPPORT_CROSSING_KG"])) <= 1e-6
    assert abs(t["TOP_SUPPORT_PROJECT_BASIS_KG"] - (t["TOP_EXTENSION_KG"] + t["TOP_SUPPORT_CROSSING_KG"])) <= 1e-6
    assert abs(t["SUPPORT_CROSSING_KG"] - (t["BOTTOM_SUPPORT_CROSSING_KG"] + t["TOP_SUPPORT_CROSSING_KG"])) <= 1e-6
    assert abs(T - (t["BOTTOM_MAIN_PROJECT_BASIS_KG"] + t["TOP_SUPPORT_PROJECT_BASIS_KG"] +
                    t["LOCAL_TOP_EXPLICIT_KG"])) <= 1e-6
    assert abs(T - sum(f(r["KG"]) for r in rel)) <= 1e-6
    assert abs(T - sum(f(c["KG"]) for c in comps if c["KG"])) <= 1e-6
    pan = sum(f(p["PANEL_OWNED_KG"]) for p in rows("05_S7_PANEL_SUMMARY.csv") if p["PANEL_OWNED_KG"])
    sup = sum(f(s["SUPPORT_OWNED_KG"]) for s in rows("06_S7_SUPPORT_SUMMARY.csv") if s["SUPPORT_OWNED_KG"])
    assert abs(pan + sup - T) <= 1e-6
    assert abs(summary["lengths_m"]["TOTAL_EQUIVALENT_BAR_LENGTH_M"] -
               sum(f(r["EQUIVALENT_TOTAL_LENGTH_M"]) for r in rel)) <= 1e-6
    assert all(summary["gates"].values()) and len(summary["gates"]) == 16


def test_lanes_labels_and_total_name(rel, blk, summary):
    for name in OUTPUTS:
        txt = (PKG / name).read_text(encoding="utf-8").upper()
        for bad in ("VERIFIED_PHYSICAL", "AS_BUILT", "SOURCE_EXACT", "FINAL_SLAB_REBAR"):
            assert bad not in txt, (name, bad)
    assert summary["total_name"] == "RESTRICTED_S7_PROJECT_BASIS_KG" and summary["total_is_final"] is False
    assert summary["flags"]["final_total_claimed"] is False
    fl = summary["flags"]
    assert fl["scope_widened"] is False and fl["references_read_before_freeze"] == [] and not fl["s7_1_started"]
    assert not fl["s8_started"] and not fl["rounded_counts"] and not fl["pre_s7_1_edited"]


def test_authority_corrections_recorded(summary):
    ac = {a["id"]: a for a in summary["authority_corrections"]}
    assert set(ac) == {"S7-AC01", "S7-AC02"}
    assert "PROJECT_SOURCE" in ac["S7-AC01"]["correction"] and "1/3" in ac["S7-AC01"]["correction"]
    assert "0.125" in ac["S7-AC02"]["correction"] and "PROJECT_SOURCE" in ac["S7-AC02"]["correction"]
    assert all(a["quantity_effect"].startswith("none") for a in ac.values())
