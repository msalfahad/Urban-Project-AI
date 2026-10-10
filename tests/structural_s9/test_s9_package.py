"""S9 package: the whole-building structural BOQ reconciliation (blind, frozen before the old BOQ is read).

The released concrete is recomputed here from the raw S1 / S2 / S5 / PRE-S7 registers with code independent of the
builder (own shoelace, own overlap, own filters); the released steel is re-summed from the frozen stage registers and
summaries. Passing tests prove arithmetic and reading, not engineering approval."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
R = ROOT / "research"
PKG = R / "alsenan_structural_s9"
MANIFEST = PKG / "16_S9_FREEZE_MANIFEST.json"
S1, S2 = R / "alsenan_structural_census_s1", R / "alsenan_structural_s2"
HYG = re.compile(r"YEARS 2013|7757-[A-Z]|[؀-ۿ]{3,}")
RELEASED = {"RELEASED_FROZEN_STAGE", "RELEASED_S9_DELTA"}
FIREWALL = re.compile(r"registers_v3b|R9_1|alsenan_arch_truth_05|post_freeze|pre_s8_structural_completeness/0[2-7]_")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name, pkg=PKG):
    with open(pkg / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return None if v in (None, "") else float(v)


@pytest.fixture(scope="module")
def s():
    return J(PKG / "14_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def conc():
    return rows("02_CONCRETE_BOQ_RECONCILIATION.csv")


@pytest.fixture(scope="module")
def bars():
    return rows("03_REINFORCEMENT_BOQ_RECONCILIATION.csv")


@pytest.fixture(scope="module")
def s2():
    return {c["element_id"]: c["release_state"] for c in J(S2 / "ALSENAN_COMPONENT_RELEASE.json")["components"]
            if c["component"] == "CONCRETE"}


def released(conc, family):
    return {x["COMPONENT_ID"]: f(x["RELEASED_M3"]) for x in conc if x["FAMILY"] == family and x["LANE"] in RELEASED}


# ------------------------------------------------------------------ freeze and firewall
def test_frozen_before_comparison_over_unchanged_stages(s):
    m = J(MANIFEST)
    assert m["state"] == "FROZEN_BEFORE_COMPARISON" and m["references_read"] == [] == s["references_read"]
    DR.verify_frozen(MANIFEST, ROOT)
    assert len(m["frozen_baselines"]) == 29 == len(s["frozen_baselines"])
    for p in sorted(R.glob("*/*_MANIFEST.json")):
        if J(p).get("state") in ("FROZEN_BEFORE_COMPARISON", "DATED_CORRECTION_LAYER") and p != MANIFEST:
            DR.verify_frozen(p, ROOT)
    for stage, sha in m["stage_indexes"].items():
        d = {"S1": S1, "S2": S2, "S3": R / "alsenan_column_rebar_s3", "S3.1": R / "alsenan_column_rebar_s3_1"}[stage]
        assert hashlib.sha256((d / "INDEX.json").read_bytes()).hexdigest() == sha
    assert not [p for p in m["inputs"] if FIREWALL.search(p)]
    src = (PKG / "build_s9.py").read_text(encoding="utf-8")
    assert "BOQ_LINES_V3B" not in src and "registers_v3b/" not in src and "alsenan_arch_truth_05/" not in src
    assert not [p for p in m["outputs"] if "post_freeze" in p or p.endswith(".xlsx")]
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    for p in ("engine/source/structural_reconciliation.py", "research/alsenan_structural_s9/build_s9.py",
              "research/alsenan_structural_s9/post_freeze/post_freeze_comparison.py"):
        assert f'"{p}"' in reg


def test_partial_boq_never_complete_and_gate_incomplete(s):
    readme = (PKG / "00_README.md").read_text(encoding="utf-8")
    rep = (PKG / "08_STRUCTURAL_COMPLETENESS_REPORT.md").read_text(encoding="utf-8")
    assert "partial structural BOQ, not a complete building estimate" in readme
    assert "It is not a complete building" in rep and "INCOMPLETE" in readme and "INCOMPLETE" in rep
    assert "INCOMPLETE" in s["gate_note"] and "GREEN" not in readme + rep
    boq = rows("07_RELEASED_STRUCTURAL_BOQ.csv")
    assert all("PARTIAL" in x["SECTION"] for x in boq if x["SECTION"].startswith("TOTAL"))


# ------------------------------------------------------------------ concrete, recomputed from the raw registers
def test_footings_recomputed_from_s1_schedule_with_overlap_and_ff_once(conc, s2, s):
    fdef = {r["footing_type"]: r for r in J(S1 / "FOOTING_DEFINITION_REGISTER.json")["rows"]}
    occ = J(S1 / "FOOTING_OCCURRENCE_REGISTER.json")["rows"]

    def box(r):
        x0, y0, x1, y1 = r["outline"]["bbox"]
        return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)
    dedu = defaultdict(float)
    for i, a in enumerate(occ):
        for b in occ[i + 1:]:
            (ax0, ay0, ax1, ay1), (bx0, by0, bx1, by1) = box(a), box(b)
            w, h = min(ax1, bx1) - max(ax0, bx0), min(ay1, by1) - max(ay0, by0)
            if w > 0 and h > 0:
                da, db = fdef[a["type"]]["D_cm"], fdef[b["type"]]["D_cm"]
                shallow = a if da <= db else b
                dedu[shallow["footing_id"]] += w * h / 1e6 * min(da, db) / 100
    mine = {}
    for r in occ:
        if not r["type"] or s2.get(r["footing_id"]) != "VERIFIED" or r["terminal_state"] != "COUNTED_AND_DEFINED":
            continue
        d = fdef[r["type"]]
        x0, y0, x1, y1 = box(r)
        drawn = sorted([(x1 - x0) / 1000, (y1 - y0) / 1000])
        if abs(drawn[0] - min(d["L_cm"], d["W_cm"]) / 100) < 0.002 and \
                abs(drawn[1] - max(d["L_cm"], d["W_cm"]) / 100) < 0.002:
            mine[r["footing_id"]] = d["L_cm"] * d["W_cm"] * d["D_cm"] / 1e6 - dedu[r["footing_id"]]
    got = released(conc, "FOOTINGS")
    assert set(mine) == set(got) and len(got) == 25
    for k in mine:
        assert got[k] == pytest.approx(mine[k], abs=1e-9)
    assert math.fsum(mine.values()) == pytest.approx(s["released_concrete_m3_by_family"]["FOOTINGS"], abs=1e-6)
    assert sum(dedu.values()) == pytest.approx(0.14 * 0.30, abs=1e-9) and dedu["FTG-FN-28608-17612"] > 0
    # FF 4.60 x 4.50 x 0.55 = 11.385 m3: once, in the footing family; the lift family keeps a reference only
    ff = [x for x in conc if f(x["RELEASED_M3"]) and abs(f(x["RELEASED_M3"]) - 4.6 * 4.5 * 0.55) < 1e-9]
    assert [x["COMPONENT_ID"] for x in ff] == ["FTG-FF-18688-14112"] and ff[0]["OWNER_FAMILY"] == "FOOTINGS"
    lift_ftg = next(x for x in conc if x["COMPONENT_ID"] == "LIFT-01-FTG")
    assert lift_ftg["LANE"] == "EXCLUDED_OWNED_BY_OTHER_FAMILY" and not lift_ftg["RELEASED_M3"]
    conflict = next(x for x in conc if x["COMPONENT_ID"].startswith("FTG-CONFLICT_F_F10"))
    assert conflict["LANE"] == "SOURCE_CONFLICT" and not conflict["RELEASED_M3"]


def test_columns_recomputed_on_the_printed_floor_to_floor(conc, s2, s):
    occ = J(S1 / "COLUMN_OCCURRENCE_REGISTER.json")["rows"]
    h = {x["storey"]: x["floor_to_floor_m"] for x in J(S1 / "STRUCTURAL_LEVEL_REGISTER.json")["intervals"]}
    assert (h["GF"], h["1F"], h["2F"], h["FOUNDATION"]) == (4.5, 4.2, 4.2, None)
    mine = {r["column_id"]: r["schedule_section_cm"][0] * r["schedule_section_cm"][1] / 1e4 * h[r["floor"]]
            for r in occ if r["floor"] != "FOUNDATION" and s2.get(r["column_id"]) == "VERIFIED"
            and r["drawn_vs_schedule"] == "MATCH" and r["schedule_section_cm"]}
    got = released(conc, "COLUMNS")
    assert set(mine) == set(got)
    for k in mine:
        assert got[k] == pytest.approx(mine[k], abs=1e-9)
    assert math.fsum(mine.values()) == pytest.approx(s["released_concrete_m3_by_family"]["COLUMNS"], abs=1e-6)
    # no foundation-storey neck is released (founding level not printed); the lift columns are a source conflict
    fnd = [x for x in conc if x["FAMILY"] == "COLUMNS" and x["STOREY"] == "FOUNDATION"]
    assert fnd and not [x for x in fnd if x["LANE"] in RELEASED]
    lift = {"COL-C1-X09-Y09-FOUNDATION", "COL-C2-X09-Y07-FOUNDATION", "COL-C2-X10-Y09-FOUNDATION",
            "COL-C9-X10-Y07-FOUNDATION"}
    assert {x["COMPONENT_ID"] for x in fnd if x["LANE"] == "SOURCE_CONFLICT"} == lift
    assert all("200 / 250 drawn vs 300 schedule" in x["FLAGS"] for x in fnd if x["COMPONENT_ID"] in lift)


def test_ground_beams_recomputed_from_s5_explicit_sections(conc, s):
    mine = {}
    for name in ("GROUND_BEAM_REBAR_SUMMARY.csv", "STRAP_BEAM_REBAR_SUMMARY.csv"):
        for r in rows(name, R / "alsenan_ground_system_rebar_s5"):
            if r["width_state"] == r["depth_state"] == "SOURCE_EXPLICIT":
                mine[r["occurrence_id"]] = float(r["member_clear_concrete_length_m"]) * float(r["width_mm"]) * \
                    float(r["depth_mm"]) / 1e6
    got = released(conc, "GROUND_BEAMS")
    assert set(mine) == set(got) and len(got) == 6
    for k in mine:
        assert got[k] == pytest.approx(mine[k], abs=1e-9)
    assert math.fsum(mine.values()) == pytest.approx(s["released_concrete_m3_by_family"]["GROUND_BEAMS"], abs=1e-6)
    # the p.13 length-class sections come from D1.1's frozen source search, never constants
    d11 = J(R / "d1_1_stirrup_authority_audit/06_CORRECTED_RELEASE_SUMMARY.json")
    keys = " ".join(d11["source_search"]["drawn_link_corners"])
    assert "GB_LT_2_5M (30x30)" in keys and "GB_LT_5M (30x40)" in keys and "GB_GT_5M (30x60)" in keys


def _shoelace(pts):
    return abs(sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))) / 2


def test_slab_plates_recomputed_with_an_own_shoelace(conc, s2, s):
    thick = {r["SLAB_PANEL_ID"]: r for r in rows("02_THICKNESS_REGISTER.csv", R / "alsenan_slab_rebar_pre_s7")}
    tank = {r["PANEL_ID"] for r in rows("04_CONCRETE_QTO.csv", R / "alsenan_water_tank_s8_4") if r["PANEL_ID"]}
    mine, verified = {}, 0
    for r in J(S1 / "SLAB_PANEL_REGISTER.json")["rows"]:
        if r["floor"] == "GROUND_SLAB_SOG" or r["class"] in ("OPEN_TO_BELOW", "OUTSIDE_BUILDING_OR_COURT", "DOME_ZONE",
                                                               "STAIR_FLIGHT_ZONE", "STAIR_IN_VOID_ZONE"):
            continue
        verified += s2.get(r["panel_id"]) == "VERIFIED"
        if r["panel_id"] in tank or s2.get(r["panel_id"]) != "VERIFIED":
            continue
        pts = [(x / 1000, y / 1000) for x, y in r["polygon_mm"]]
        if pts[0] == pts[-1]:
            pts = pts[:-1]
        a = _shoelace(pts) - sum(_shoelace([(x / 1000, y / 1000) for x, y in hh]) for hh in r.get("holes_mm") or [])
        t = thick[r["panel_id"]]
        assert t["STATE"] == "RESOLVED" and abs(a - r["area_m2"]) < 0.002
        mine[r["panel_id"]] = r["area_m2"] * float(t["EFFECTIVE_THICKNESS_MM"]) / 1000
    got = released(conc, "SLABS")
    assert set(mine) == set(got) and len(got) == 47 and verified == 49     # + the two S8.4 tank panels
    for k in mine:
        assert got[k] == pytest.approx(mine[k], abs=1e-9)
    assert math.fsum(mine.values()) == pytest.approx(s["released_concrete_m3_by_family"]["SLABS"], abs=1e-6)
    assert not {x["COMPONENT_ID"] for x in conc if x["COMPONENT_ID"] in tank and x["LANE"] in RELEASED and
                x["FAMILY"] == "SLABS"}


def test_frozen_stage_concrete_carried_unchanged(conc, s):
    fam = s["released_concrete_m3_by_family"]
    ref = {"GROUND_SLAB": J(R / "alsenan_ground_slab_s8_1/10_S8_1_SUMMARY.json")["concrete_m3"],
           "DOMES": J(R / "alsenan_dome_ring_s8_3/15_S8_3_SUMMARY.json")["released"]["concrete_m3"],
           "WATER_TANK_ROOF": J(R / "alsenan_water_tank_s8_4/14_S8_4_SUMMARY.json")["released"]["concrete_m3"],
           "LINTELS": J(R / "alsenan_lintels_s8_6a/11_S8_6A_SUMMARY.json")["corrected"]["m3"],
           "STAIRS": J(R / "alsenan_stairs_s8_7/16_S8_7_SUMMARY.json")["released"]["concrete_m3"]}
    for k, v in ref.items():
        assert fam[k] == pytest.approx(v, abs=1e-6), k
    assert fam["LINTELS"] == pytest.approx(0.366) and fam["STAIRS"] == pytest.approx(0.516582788, abs=1e-6)
    assert "BEAMS" not in fam and "LIFT" not in fam and "POOL" not in fam
    total = math.fsum(f(x["RELEASED_M3"]) for x in conc if x["LANE"] in RELEASED)
    assert total == pytest.approx(s["released_concrete_m3_total"], abs=1e-6) == math.fsum(fam.values())
    delta = math.fsum(f(x["DELTA_M3"]) for x in rows("10_S9_DELTA_REGISTER.csv") if x["DELTA_M3"])
    assert delta == pytest.approx(s["released_concrete_m3_s9_delta"], abs=1e-6)
    assert total - delta == pytest.approx(s["released_concrete_m3_frozen_stages"], abs=1e-6)


# ------------------------------------------------------------------ reinforcement and precedence
def test_rebar_chains_against_stage_summaries(bars, s):
    g = defaultdict(float)
    for b in bars:
        if b["LANE"] in RELEASED:
            g[b["FAMILY"]] += float(b["AUTHORITATIVE_KG"])
    fam = s["released_reinforcement_kg_by_family"]
    for k in g:
        assert g[k] == pytest.approx(fam[k], abs=1e-5), k
    s5 = J(R / "alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json")
    s51 = J(R / "alsenan_ground_system_rebar_s5_1/S5_1_RELEASE_SUMMARY.json")
    ad1 = J(R / "ad1_authority_decisions/07_AD1_SUMMARY.json")["kg_corrections"]["conservation_s5"]["correction_kg"]
    d11 = R / "d1_1_stirrup_authority_audit"
    d11_s5 = math.fsum(float(x["CORRECTION_KG"]) for x in rows("04_S5_1A_CORRECTIONS.csv", d11))
    d11_s6 = math.fsum(float(x["CORRECTION_KG"]) for x in rows("03_S6_1A_CORRECTIONS.csv", d11))
    gb = s5["known_source_derived_ground_system_rebar_kg"] + s51["delta_known_kg"] + ad1 + d11_s5
    # the bar rows carry the stages' 6-decimal kg, the summaries their unrounded totals: agree within 0.1 g
    assert fam["GROUND_BEAMS"] == pytest.approx(gb, abs=1e-4) and gb == pytest.approx(1436.23167, abs=1e-4)
    s6 = J(R / "alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")
    s61 = J(R / "alsenan_superstructure_beam_rebar_s6_1/S6_1_RELEASE_SUMMARY.json")
    bm = s6["known_source_derived_superstructure_beam_rebar_kg"] + s61["delta_known_kg"] + d11_s6
    assert fam["BEAMS"] == pytest.approx(bm, abs=1e-4)
    s4 = J(R / "alsenan_footing_rebar_s4/FOOTING_REBAR_RELEASE_SUMMARY.json")["accurate_summary"]["project"]
    assert fam["FOOTINGS"] == pytest.approx(s4["released_kg"], abs=1e-4)
    s7 = J(R / "alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json")["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    assert fam["SLABS"] == pytest.approx(s7, abs=1e-4)
    # S8.6 is superseded by S8.6A: the original and the corrected lintel steel are never added
    s86 = J(R / "alsenan_lintels_s8_6/14_S8_6_SUMMARY.json")["released"]["kg"]
    s86a = J(R / "alsenan_lintels_s8_6a/11_S8_6A_SUMMARY.json")["corrected"]["kg"]
    assert fam["LINTELS"] == pytest.approx(s86a, abs=1e-6) and fam["LINTELS"] < s86
    assert s["released_reinforcement_kg_total"] == pytest.approx(math.fsum(fam.values()), abs=1e-6)


def test_s9_c01_column_tie_paths_moved_to_conditional(bars, s):
    reg = J(R / "alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json")["rows"]
    vlb = [p for p in reg if p["release_state"] in ("VERIFIED", "LOWER_BOUND")]
    tie = [p for p in vlb if p["component"] == "TIES" and p["length_kind"] in ("TIE_CORE_PATH", "HOOK_1", "HOOK_2")]
    c01 = math.fsum(p["kg"] for p in tie)
    assert c01 == pytest.approx(s["s9_c01_retracted_kg"], abs=1e-6) == pytest.approx(1217.128, abs=1e-6)
    assert s["released_reinforcement_kg_by_family"]["COLUMNS"] == pytest.approx(
        math.fsum(p["kg"] for p in vlb) - c01, abs=1e-6)
    corr = [x for x in rows("10_S9_DELTA_REGISTER.csv") if x["DELTA_ID"] == "S9-C01"]
    assert len(corr) == 1 and corr[0]["COMPONENT_ID"] == f"{len(tie)} S3.1 parts" and len(tie) == 288
    assert corr[0]["CHANGE_KIND"] == "REINFORCEMENT_AUTHORITY_CORRECTION"
    assert float(corr[0]["DELTA_KG"]) == pytest.approx(-c01, abs=1e-6)
    moved = [b for b in bars if b["CORRECTIONS"] == "S9-C01"]
    assert len(moved) == 288 and all(b["LANE"] == "CONDITIONAL_NOT_RELEASED" and not b["AUTHORITATIVE_KG"]
                                     for b in moved)
    # the released column laps / anchorage / starters are only S3.1's printed-rule parts
    extra = {b["SOURCE_AUTHORITY"] for b in bars if b["FAMILY"] == "COLUMNS" and b["LANE"] in RELEASED
             and not b["BAR_ROLE"].startswith("MAIN_BARS")}
    assert extra <= {"P8-N09", "P13-FOOTING-TYP", "P15-TWISTED"}


def test_precedence_one_authoritative_version_each():
    p = rows("04_OWNERSHIP_AND_PRECEDENCE_REGISTER.csv")
    by = defaultdict(list)
    for x in p:
        by[(x["TRADE"], x["FAMILY"])].append(x)
    for k, v in by.items():
        assert sum(x["AUTHORITATIVE"] == "True" for x in v) == 1, k
    lin = {x["VERSION"]: x for x in by[("REBAR", "LINTELS")]}
    assert lin["S8.6"]["SUPERSEDED"] == "True" and lin["S8.6A"]["AUTHORITATIVE"] == "True"
    assert lin["S8.6A"]["KIND"] == "SUPERSEDING"
    col = {x["VERSION"]: x for x in by[("REBAR", "COLUMNS")]}
    assert col["S9-C01"]["AUTHORITATIVE"] == "True" and col["S3"]["SUPERSEDED"] == col["S3.1"]["SUPERSEDED"] == "True"
    beams = by[("CONCRETE", "BEAMS")]
    assert any("not measured as zero" in x["WHY"] for x in beams)


# ------------------------------------------------------------------ conservation, lanes, ownership
def test_lanes_owners_and_no_leaks(conc, bars, s):
    ids = [x["COMPONENT_ID"] for x in conc]
    assert len(ids) == len(set(ids)) == s["components"] and all(x["OWNER_FAMILY"] for x in conc)
    for x in conc:
        if x["LANE"] in RELEASED:
            assert f(x["RELEASED_M3"]) == f(x["NET_M3"]) is not None
            assert f(x["GROSS_M3"]) - f(x["DEDUCTIONS_M3"]) == pytest.approx(f(x["NET_M3"]), abs=1e-9)
        else:
            assert not x["RELEASED_M3"], x["COMPONENT_ID"]
    for b in bars:
        assert (b["LANE"] in RELEASED) == bool(b["AUTHORITATIVE_KG"]), b["ITEM_ID"]
        if b["AUTHORITATIVE_KG"]:
            assert float(b["AUTHORITATIVE_KG"]) >= 0
    cons = rows("12_CONSERVATION_CHECKS.csv")
    assert len(cons) == 22 and {x["RESULT"] for x in cons} == {"PASS"}
    assert not [x for x in rows("11_OVERLAP_AND_DOUBLE_COUNT_AUDIT.csv") if x["RESULT"] != "PASS"]
    boq = rows("07_RELEASED_STRUCTURAL_BOQ.csv")
    m3 = math.fsum(float(x["QUANTITY"]) for x in boq if x["SECTION"] == "A1 CONCRETE")
    kg = math.fsum(float(x["QUANTITY"]) for x in boq if x["SECTION"] == "A2 REINFORCEMENT")
    assert m3 == pytest.approx(s["released_concrete_m3_total"], abs=1e-5)
    assert kg == pytest.approx(s["released_reinforcement_kg_total"], abs=1e-4)
    assert all(x["DIA_MM"] for x in boq if x["SECTION"] == "A2 REINFORCEMENT")
    fl = rows("06_FLOOR_SUMMARY.csv")
    assert fl


def test_unmeasured_never_zero_and_missing_register(conc):
    for x in conc:
        if x["LANE"] in ("BLOCKED_UNQUANTIFIED", "SOURCE_CONFLICT", "CONDITIONAL_NOT_RELEASED"):
            assert x["UNRESOLVED_REASON"] or x["EVIDENCE_STATUS"], x["COMPONENT_ID"]
            assert x["NET_M3"] in ("", None) or x["LANE"] == "CONDITIONAL_NOT_RELEASED"
    miss = rows("05_MISSING_AND_BLOCKED_REGISTER.csv")
    cats = defaultdict(int)
    for x in miss:
        for c in json.loads(x["CATEGORIES"]):
            cats[c.split(" ")[0]] += 1
    for c in ("REBAR_MEASURED_CONCRETE_MISSING", "OWNED_NO_QUANTITY", "CONDITIONAL_ONLY",
              "POSSIBLE_MULTI_STAGE_COUNT", "ABSENT_FROM_OLD_BOQ"):
        assert cats[c] > 0, c
    assert cats["CONCRETE_MEASURED_REBAR_MISSING"] == 0                 # every released concrete row has its steel
    beams = [x for x in conc if x["FAMILY"] == "BEAMS"]
    assert beams and not [x for x in beams if x["LANE"] in RELEASED]
    cond = [x for x in beams if x["LANE"] == "CONDITIONAL_NOT_RELEASED"]
    assert cond
    for x in cond:                       # B x H x L .. B x (H + 0.16) x L, or an upper bound only (curved bands)
        lo, hi = json.loads(x["CONDITIONAL_RANGE_M3"])
        assert hi > 0 and (lo is None and "UPPER_BOUND_ONLY" in x["FLAGS"] or lo < hi), x["COMPONENT_ID"]
        if lo is not None:
            d = json.loads(x["DIMENSIONS"])
            assert hi - lo == pytest.approx(d["B_mm"] / 1000 * 0.16 * lo / (d["B_mm"] * d["H_mm"] / 1e6), rel=1e-6)


def test_stairs_lift_and_pool_stay_blocked(conc, bars):
    st = [x for x in conc if x["FAMILY"] == "STAIRS" and x["LANE"] in RELEASED]
    assert len(st) == 3 and all(x["LANE"] == "RELEASED_FROZEN_STAGE" for x in st)
    assert math.fsum(f(x["RELEASED_M3"]) for x in st) == pytest.approx(0.516582788, abs=1e-6)
    sb = [b for b in bars if b["FAMILY"] == "STAIRS" and b["LANE"] in RELEASED]
    assert math.fsum(float(b["AUTHORITATIVE_KG"]) for b in sb) == pytest.approx(59.020862261, abs=1e-6)
    lift = [x for x in conc if x["FAMILY"] == "LIFT"]
    assert lift and not [x for x in lift if x["LANE"] in RELEASED]
    assert {x["LANE"] for x in lift} <= {"BLOCKED_UNQUANTIFIED", "INDICATIVE_ONLY_NOT_RELEASED", "NOT_APPLICABLE",
                                         "NOT_IN_SOURCE", "EXCLUDED_OWNED_BY_OTHER_FAMILY"}
    walls = [x for x in lift if x["LANE"] == "INDICATIVE_ONLY_NOT_RELEASED"]
    assert len(walls) == 4 and not [b for b in bars if b["FAMILY"] == "LIFT" and b["LANE"] in RELEASED]
    assert not [x for x in conc if x["FAMILY"] == "POOL" and x["LANE"] != "BLOCKED_UNQUANTIFIED"]
    readme = (PKG / "00_README.md").read_text(encoding="utf-8")
    assert "110 - 120 mm unfinished riser is not used as a repeated concrete riser" in readme
    assert "preferred research alternative, not approved" in readme


def test_rfis_carried_and_consolidated(s):
    r = rows("09_ENGINEER_RFI_REGISTER.csv")
    assert len(r) == s["rfis"] and len({x["RFI_ID"] for x in r}) == len(r)
    by = defaultdict(int)
    for x in r:
        by[x["SOURCE_STAGE"]] += 1
    assert by["S8.7C"] == len(rows("09_PRIORITISED_RFI.csv", R / "alsenan_stairs_s8_7c"))
    assert by["S8.8"] == len(rows("14_RFI_QUESTIONS.csv", R / "alsenan_lift_s8_8"))
    s9 = [x for x in r if x["SOURCE_STAGE"] == "S9"]
    assert len(s9) == 9 and {x["PRIORITY"] for x in s9} == {"P1", "P2", "P3"}
    assert any("200 / 250 vs 300" in x["QUESTION"] for x in s9)


def test_hygiene():
    for p in sorted(PKG.iterdir()):
        if p.is_file() and p.suffix in (".md", ".csv", ".json", ".jsonl"):
            assert not HYG.search(p.read_text(encoding="utf-8")), p.name


def test_rebuild_byte_identical():
    m = J(MANIFEST)
    before = {k: (PKG / k).read_bytes() for k in m["outputs"]}
    before[MANIFEST.name] = MANIFEST.read_bytes()
    subprocess.run([sys.executable, "-I", str(PKG / "build_s9.py")], check=True, cwd=ROOT, capture_output=True,
                   timeout=900)
    after = {k: (PKG / k).read_bytes() for k in before}
    assert before == after
