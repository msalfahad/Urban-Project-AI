"""PRE-S8 (research/pre_s8_structural_completeness): structural completeness audit, excavation to roof.

No kg is calculated here, nothing frozen moves and S8 is not started. The checks below:

- every S1 / stage population is conserved in the census, one row per element;
- every brief family is searched, and an absence is backed by zero hits;
- the Arabic whole-word match does not invent a boundary wall inside the word for beams;
- the new conflicts (tower dome, dome ring arcs) are registered;
- all ten brief interfaces are audited;
- every S8 candidate is checked against every source channel."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "pre_s8_structural_completeness"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
OUTPUTS = ["00_README.md", "01_FAMILY_POPULATION_SEARCH.csv", "02_STRUCTURAL_ELEMENT_CENSUS.csv",
           "03_CONCRETE_COVERAGE_MATRIX.csv", "04_REBAR_COVERAGE_MATRIX.csv", "05_STAGE_OWNERSHIP_REGISTER.csv",
           "06_S8_CANDIDATE_REGISTER.csv", "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv", "08_SOURCE_CONFLICT_REGISTER.csv",
           "09_MISSING_REINFORCEMENT_COMPONENTS.csv", "10_S8_SOURCE_EXHAUSTION.csv", "11_S8_READINESS_DECISION.json",
           "12_PRE_S8_SUMMARY.json"]
BRIEF_FIELDS = ["ELEMENT_ID", "ELEMENT_FAMILY", "FLOOR", "SOURCE_PAGE", "DXF_HANDLES", "PHYSICAL_GEOMETRY",
                "CONCRETE_QUANTITY_STATE", "REBAR_COMPONENTS", "EXISTING_STAGE_OWNER", "NEW_S8_OWNER",
                "SOURCE_AUTHORITY", "MISSING_INFORMATION", "CONFLICT", "QA_STATE"]
BRIEF_INTERFACES = ["FOOTING -> STARTER -> COLUMN", "GROUND BEAM -> COLUMN", "COLUMN -> BEAM", "BEAM -> SLAB",
                    "SLAB -> STAIR", "SLAB -> CANTILEVER", "WALL -> FOUNDATION", "LIFT WALL -> PIT BASE",
                    "POOL WALL -> POOL BASE", "TANK WALL -> TANK BASE"]
BRIEF_FAMILIES = ["LEAN_BLINDING_CONCRETE", "ISOLATED_FOOTING", "COMBINED_FOOTING", "STRIP_FOOTING", "NECK_PEDESTAL",
                  "STARTER_DOWEL", "STRAP_BEAM", "GROUND_BEAM", "GROUND_SLAB", "COLUMN", "STRUCTURAL_WALL",
                  "RETAINING_WALL", "SHEAR_OR_CORE_WALL", "BEAM", "ELEVATED_SLAB", "SUNKEN_SLAB_OR_STEP",
                  "CANTILEVER_OR_BALCONY", "STAIR_AND_LANDING", "LIFT_PIT_AND_WALLS", "WATER_TANK", "SWIMMING_POOL",
                  "DOME_OR_SPECIAL_ROOF", "RC_PARAPET", "UPSTAND_OR_KERB", "EQUIPMENT_BASE_OR_PLINTH", "OPENING_TRIM"]


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def census():
    return rows(PKG / "02_STRUCTURAL_ELEMENT_CENSUS.csv")


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "12_PRE_S8_SUMMARY.json")


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("build_pre_s8", PKG / "build_pre_s8.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ------------------------------------------------------------------ freeze and no-change guarantees
def test_freeze_manifest_still_matches():
    m = J(PKG / "13_PRE_S8_FREEZE_MANIFEST.json")
    assert m["round"] == "PRE_S8" and m["state"] == "FROZEN_ANALYSIS_NO_KG" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    assert DR.verify_frozen(PKG / "13_PRE_S8_FREEZE_MANIFEST.json", ROOT)["round"] == "PRE_S8"


def test_every_frozen_stage_still_matches_and_s7_is_unchanged(summary):
    assert set(summary["frozen_baselines"]) == {"S4", "S4.1", "S5", "S5.1", "S6", "S6.1", "AD1", "D1.1", "D1.2",
                                                "PRE-S7", "PRE-S7.1", "S7", "S7A"}
    tot = J(ROOT / "research/alsenan_slab_rebar_s7/09_S7_PROJECT_SUMMARY.json")["totals_kg"]
    assert summary["s7_total_kg_unchanged"] == tot["RESTRICTED_S7_PROJECT_BASIS_KG"]
    assert abs(tot["RESTRICTED_S7_PROJECT_BASIS_KG"] - 3802.015364542) < 1e-6
    assert summary["kg_calculated_here"] == 0 and summary["s8_started"] is False and summary["references_read"] == []


def test_stage_totals_are_copied_from_the_frozen_summaries(summary):
    d12 = J(ROOT / "research/d1_2_footing_cover_audit/05_CORRECTED_RELEASE_SUMMARY.json")["combined"]["parts"]
    s31 = J(ROOT / "research/alsenan_column_rebar_s3_1/COLUMN_RELEASE_REGISTER.json")["totals_kg"]
    kg = summary["stage_kg"]
    assert kg["S3.1"] == s31["total"]
    assert kg["S4.1 (+D1.2)"] == d12["S4.1"]["project_basis_kg"]
    assert kg["S5.1 (+AD1, D1.1)"] == d12["S5.1"]["project_basis_kg"]
    assert kg["S6.1 (+D1.1)"] == d12["S6.1"]["project_basis_kg"]


# ------------------------------------------------------------------ census structure and conservation
def test_every_row_carries_the_fourteen_brief_fields(census):
    assert set(BRIEF_FIELDS) <= set(census[0])
    ids = [r["ELEMENT_ID"] for r in census]
    assert len(ids) == len(set(ids))
    known = set(ids)
    for r in census:
        assert r["ELEMENT_ID"] and r["ELEMENT_FAMILY"] and r["FLOOR"] and r["CONCRETE_QUANTITY_STATE"], r
        assert r["EXISTING_STAGE_OWNER"] and r["NEW_S8_OWNER"] and r["SOURCE_AUTHORITY"] and r["QA_STATE"], r
        assert r["ROW_KIND"] in ("ELEMENT", "POPULATION_RECORD", "CONFLICT_CANDIDATE", "FACE_OF_ELEMENT",
                                 "COMPONENT_EVIDENCE", "TYPICAL_DETAIL_ONLY")
        if r["PARENT_ELEMENT"] and not r["PARENT_ELEMENT"].startswith("S7 slab population"):
            assert r["PARENT_ELEMENT"] in known, r["ELEMENT_ID"]
        if r["ROW_KIND"] in ("FACE_OF_ELEMENT", "COMPONENT_EVIDENCE"):
            assert r["PARENT_ELEMENT"], r["ELEMENT_ID"]


def test_populations_are_conserved(census):
    ids = {r["ELEMENT_ID"] for r in census}
    s1 = {k: J(S1 / f"{k}.json")["rows"] for k in ("FOOTING_OCCURRENCE_REGISTER", "COLUMN_OCCURRENCE_REGISTER",
                                                     "SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER")}
    assert {r["footing_id"] for r in s1["FOOTING_OCCURRENCE_REGISTER"]} <= ids
    assert {r["column_id"] for r in s1["COLUMN_OCCURRENCE_REGISTER"]} <= ids
    assert {r["special_id"] for r in s1["SPECIAL_STRUCTURAL_OCCURRENCE_REGISTER"]
            if r["kind"] != "SECTION_DETAIL_CALLOUT"} <= ids
    s5 = rows(ROOT / "research/alsenan_ground_system_rebar_s5/GROUND_SYSTEM_REBAR_OCCURRENCES.csv")
    s6 = rows(ROOT / "research/alsenan_superstructure_beam_rebar_s6/SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")
    assert {r["occurrence_id"] for r in s5} <= ids and {r["occurrence_id"] for r in s6} <= ids
    pre7 = rows(ROOT / "research/alsenan_slab_rebar_pre_s7/01_SLAB_PANEL_CENSUS.csv")
    for p in pre7:
        assert (p["SLAB_PANEL_ID"] in ids) == (p["PANEL_CLASS"] != "OUTSIDE_BUILDING_OR_COURT"), p["SLAB_PANEL_ID"]


def test_faces_attach_to_one_parent_element(census):
    by = {r["ELEMENT_ID"]: r for r in census}
    dome = [r for r in census if r["ROW_KIND"] == "FACE_OF_ELEMENT" and r["PARENT_ELEMENT"].startswith("SPC-DOME")]
    assert len(dome) == 8 and Counter(r["PARENT_ELEMENT"] for r in dome) == {"SPC-DOME-1": 4, "SPC-DOME-2": 4}
    assert by["SP-GF_ROOF_SLAB-21"]["PARENT_ELEMENT"] == "SPC-STAIR-SP-GF_ROOF_SLAB-21"
    assert {by["SP-2F_ROOF_SLAB-01"]["PARENT_ELEMENT"], by["SP-2F_ROOF_SLAB-02"]["PARENT_ELEMENT"]} == {
        "SPC-WATER_TANK-SFRS"}
    gs = [r for r in census if r["PARENT_ELEMENT"] == "SPC-GROUND_SLAB"]
    assert len(gs) == 21
    for s in [r for r in census if r["ELEMENT_ID"].startswith("SPC-STAIR_BEAM")]:
        assert by[s["PARENT_ELEMENT"]]["EXISTING_STAGE_OWNER"].startswith("S6.1")


def test_element_count_counts_each_physical_element_once(census, summary):
    counted = [r for r in census if r["ROW_KIND"] in ("ELEMENT", "POPULATION_RECORD", "CONFLICT_CANDIDATE")]
    assert len(counted) == summary["elements_total"] and len(census) == summary["census_rows"]
    assert summary["rows_by_kind"] == dict(sorted(Counter(r["ROW_KIND"] for r in census).items()))


# ------------------------------------------------------------------ population search
def test_every_brief_family_is_searched():
    fam = {r["FAMILY"]: r for r in rows(PKG / "01_FAMILY_POPULATION_SEARCH.csv")}
    assert set(BRIEF_FAMILIES) <= set(fam)
    for k in ("STRIP_FOOTING", "RETAINING_WALL", "SHEAR_OR_CORE_WALL", "UPSTAND_OR_KERB", "EQUIPMENT_BASE_OR_PLINTH",
              "RAFT_OR_PILE", "STRUCTURAL_STEEL"):
        assert fam[k]["STATE"] == "ABSENT_IN_ISSUED_DOCUMENTS" and fam[k]["DXF_TEXT_HITS"] == "0" and \
            fam[k]["CENSUS_OCCURRENCES"] == "0", k
    for k in ("ISOLATED_FOOTING", "COMBINED_FOOTING", "NECK_PEDESTAL", "GROUND_BEAM", "COLUMN", "BEAM",
              "ELEVATED_SLAB", "STAIR_AND_LANDING", "LIFT_PIT_AND_WALLS", "SWIMMING_POOL", "DOME_OR_SPECIAL_ROOF"):
        assert fam[k]["STATE"] == "PRESENT" and int(fam[k]["CENSUS_OCCURRENCES"]) > 0, k
    assert fam["STARTER_DOWEL"]["STATE"].startswith("COMPONENT_FAMILY")
    assert fam["STRUCTURAL_WALL"]["STATE"].startswith("CANDIDATE_ONLY")
    assert fam["SPECIAL_COLUMN"]["STATE"].startswith("PRESENT_AS_COMPONENT")


def test_arabic_terms_match_whole_words_only(mod):
    assert mod._ar_match("علي المقاول مطابقة تفاصيل الدروة", "الدروة")
    assert not mod._ar_match("الجسور بطول ثلث البحر في الاتجاهين", "سور")       # fence word inside 'beams'
    assert mod._ar_match("حمام سباحة", "حمام سباحة")
    fam = {r["FAMILY"]: r for r in rows(PKG / "01_FAMILY_POPULATION_SEARCH.csv")}
    assert json.loads(fam["BOUNDARY_WALL"]["HITS_BY_SHEET"]).get("GFRS") is None


def test_lift_is_bound_to_the_ff_footing(census):
    by = {r["ELEMENT_ID"]: r for r in census}
    ff = by["FTG-FF-18688-14112"]
    assert ff["ELEMENT_FAMILY"].startswith("LIFT_FOOTING") and "supports 4 column" in ff["PHYSICAL_GEOMETRY"]
    w = by["PS8-LIFT-WALLS"]
    assert w["PARENT_ELEMENT"] == "SPC-LIFT_PIT" and "1C64" in json.loads(w["DXF_HANDLES"])


def test_tower_dome_conflict_is_registered(census, summary):
    by = {r["ELEMENT_ID"]: r for r in census}
    t = by["PS8-DOME-TOWER-ARCH-ONLY"]
    assert t["ROW_KIND"] == "CONFLICT_CANDIDATE" and "P7757:1300" in json.loads(t["DXF_HANDLES"])
    conf = {r["CONFLICT_ID"]: r for r in rows(PKG / "08_SOURCE_CONFLICT_REGISTER.csv")}
    assert {"PS8-C01", "PS8-C02", "PS8-C03", "PS8-C04"} <= set(conf)
    assert "PS8-DOME-TOWER-ARCH-ONLY" in summary["previously_omitted"]


def test_dome_ring_arcs_need_an_ownership_transfer(census):
    arcs = [r for r in census if r["ELEMENT_ID"].startswith("ARC:FFRS:BA00")]
    assert len(arcs) == 6
    for r in arcs:
        assert r["S8_SCOPE"] == "COMPONENT_OF_OWNED_ELEMENT" and r["QA_STATE"] == "COUNTED_OWNED_TRANSFER_PENDING"
        assert r["EXISTING_STAGE_OWNER"].startswith("S6.1 (BLOCKED_TYPE")


# ------------------------------------------------------------------ coverage, interfaces, readiness
def test_concrete_lines_are_real_urban_lines_never_re_summed():
    boq = J(ROOT / "tests/alsenan/registers_v3b/BOQ_LINES_V3B.json")
    lines = {f"{ln['line_id']} {ln['code']}": ln for ln in boq["lines"] if ln["trade"] == "CONCRETE"}
    for r in rows(PKG / "03_CONCRETE_COVERAGE_MATRIX.csv"):
        used = json.loads(r["URBAN_LINES"])
        assert set(used) <= set(lines), used
        if used:
            exp = sum(lines[u]["release"]["technical"]["qty"] or 0.0 for u in used)
            assert abs(float(r["V3B_LINE_TECHNICAL_M3_SHARED"]) - exp) < 1e-6
        assert "never re-summed" in r["NOTE"]


def test_all_brief_interfaces_are_audited():
    inter = {r["INTERFACE"]: r for r in rows(PKG / "07_INTERFACE_DOUBLE_COUNT_AUDIT.csv")}
    assert set(BRIEF_INTERFACES) <= set(inter)
    for r in inter.values():
        assert r["STATE"] and r["BARS_OWNED"] and r["SIDE_A"] and r["SIDE_B"]
    assert inter["SLAB -> CANTILEVER"]["STATE"] == "NOT_OWNED"
    sup = rows(ROOT / "research/alsenan_slab_rebar_s7/06_S7_SUPPORT_SUMMARY.csv")
    band = [s for s in sup if s["BEARING_WALL_CANDIDATE_BAND"] == "True"]
    assert band and all(float(s["TOP_EXTENSION_KG"] or 0) == 0 for s in band)


def test_every_s8_candidate_is_checked_on_every_channel(mod):
    ex = rows(PKG / "10_S8_SOURCE_EXHAUSTION.csv")
    assert ex
    for r in ex:
        for ch in mod.CHANNELS:
            assert r[f"CH_{ch}"], (r["S8_CANDIDATE"], ch)
        assert r["READINESS"] in ("READY_PARTIAL", "BLOCKED_NEEDS_AUTHORITY", "READY")
        assert r["MISSING"]
        assert "no bar is made from generic practice" in r["RULE"]
    dec = J(PKG / "11_S8_READINESS_DECISION.json")
    assert dec["decision"].startswith("PRE-S8 COMPLETE - S8 NOT STARTED")
    assert set(dec["candidates"]) == {r["S8_CANDIDATE"] for r in ex} and dec["recommended_s8_order"]


def test_missing_components_carry_no_quantity():
    miss = rows(PKG / "09_MISSING_REINFORCEMENT_COMPONENTS.csv")
    assert miss and all(r["QUANTITY"] == "NONE (unquantified)" for r in miss)
    comps = {(r["FAMILY"], r["COMPONENT"]) for r in miss}
    assert ("FOOTING", "BOXED") in comps and any(c == "TEMPERATURE" for _, c in comps)


# ------------------------------------------------------------------ blindness, registry, rebuild
def test_builder_is_blind():
    src = (PKG / "build_pre_s8.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze", "rebar_truth", "rough_rebar", "benchmark", "DONORS", "donor", "oracle",
                "rebar_sanity", "Quotation", "pricing", ".xlsx", "control_plane", "registers_v3b_eval",
                "registers_b1", "POST_FREEZE_MCP"):
        assert bad not in src, bad
    for line in src.splitlines():
        if line.startswith(("import ", "from ")):
            assert line.split()[1] in ("__future__", "csv", "hashlib", "io", "json", "re", "sys", "collections",
                                       "pathlib", "engine.source"), line


def test_registry_lists_the_builder():
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/pre_s8_structural_completeness/build_pre_s8.py"' in reg


def test_rebuild_is_byte_identical():
    m = J(PKG / "13_PRE_S8_FREEZE_MANIFEST.json")
    before = {k: (PKG / k).read_bytes() for k in list(m["outputs"]) + ["13_PRE_S8_FREEZE_MANIFEST.json"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_pre_s8.py")], check=True, capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k
