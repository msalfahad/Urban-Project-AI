"""D1.2 package (research/d1_2_footing_cover_audit): footing cover / bar-length authority errata over frozen S4.1.

Every number is re-derived here from the frozen S4 provenance and the S4.1 delta rows - never against a reference
total."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import cover_authority as CA

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "d1_2_footing_cover_audit"
R = ROOT / "research"
S4 = R / "alsenan_footing_rebar_s4"
S41 = R / "alsenan_footing_rebar_s4_1"
D11 = R / "d1_1_stirrup_authority_audit"
FROZEN = {"S4": S4 / "S4_FREEZE_MANIFEST.json",
          "S4.1": S41 / "S4_1_FREEZE_MANIFEST.json",
          "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
          "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
          "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
          "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
          "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
          "D1.1": D11 / "D1_1_FREEZE_MANIFEST.json"}
BUILDER = "research/d1_2_footing_cover_audit/build_d1_2_footing_cover_audit.py"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "05_CORRECTED_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def audit():
    return rows(PKG / "03_FOOTING_COVER_AUDIT.csv")


@pytest.fixture(scope="module")
def corr():
    return rows(PKG / "04_S4_1A_COVER_AUTHORITY_CORRECTION.csv")


@pytest.fixture(scope="module")
def frozen_parts():
    """The S4 parts that carry kg, with their frozen inputs, and the one S4.1 row that carries the kg."""
    prov = {}
    for line in (S4 / "FOOTING_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        d = json.loads(line)
        if d.get("kg"):
            prov[d["part_id"]] = d
    mass = {}
    for r in rows(S41 / "S4_1_DELTA_COMPONENTS.csv"):
        if float(r["NEW_KNOWN_QUANTITY"] or 0) > 0:
            assert r["BASELINE_COMPONENT_ID"] not in mass
            mass[r["BASELINE_COMPONENT_ID"]] = r
    assert set(prov) == set(mass)
    return {cid: (prov[cid], mass[cid]) for cid in prov}


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("00_README.md", "01_SOURCE_SEARCH.md", "02_COVER_BASIS.json", "03_FOOTING_COVER_AUDIT.csv",
              "04_S4_1A_COVER_AUTHORITY_CORRECTION.csv", "05_CORRECTED_RELEASE_SUMMARY.json", "06_PROVENANCE.jsonl",
              "TEST_RUN.md", "D1_2_FREEZE_MANIFEST.json", "source_search_inputs/D1_2_VISUAL_SEARCH.json"):
        assert (PKG / n).is_file(), n


def test_d1_2_freeze_manifest_still_matches():
    m = J(PKG / "D1_2_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN" and m["round"] == "D1.2" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        assert m[group]
        for k, h in m[group].items():
            assert sha(base / k) == h, (group, k)
    assert BUILDER in m["code"] and "engine/source/cover_authority.py" in m["code"]
    assert set(m["frozen_baselines"]) == set(FROZEN)


def test_frozen_s4_s4_1_and_other_stages_are_immutable(summary):
    for name, man in FROZEN.items():
        m = J(man)
        base = man.parent
        for group, b in (("code", ROOT), ("inputs", ROOT), ("outputs", base)):
            for k, h in m.get(group, {}).items():
                assert sha(b / k) == h, (name, group, k)
        assert summary["frozen"][name]["manifest_sha256"] == sha(man), name
        assert J(PKG / "D1_2_FREEZE_MANIFEST.json")["inputs"][str(man.relative_to(ROOT))] == sha(man), name
    assert not summary["flags"]["frozen_outputs_changed"]


def test_rebuild_is_byte_identical():
    man = J(PKG / "D1_2_FREEZE_MANIFEST.json")
    before = {k: (PKG / k).read_bytes() for k in man["outputs"]}
    before["D1_2_FREEZE_MANIFEST.json"] = (PKG / "D1_2_FREEZE_MANIFEST.json").read_bytes()
    subprocess.run([sys.executable, "-I", str(ROOT / BUILDER)], check=True, capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (ROOT / BUILDER).read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3", "ACI", "BS 8666",
                "Eurocode", "EN 1992", "75 mm", "assumed_cover"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert BUILDER in RP.ACCURATE_BUILDERS
    assert "engine/source/cover_authority.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ source search
def test_the_70_mm_rule_is_a_minimum(summary):
    rule = summary["rule"]
    assert rule["kind"] == CA.MINIMUM and CA.wording_kind(rule["wording"]) == CA.MINIMUM
    assert "لا يقل" in rule["wording"] and "7سم" in rule["wording"] and "الملاصقة للتربة" in rule["wording"]
    assert "not be less than" in rule["english"]
    assert rule["exact_in_any_footing_detail"] is False
    basis = J(PKG / "02_COVER_BASIS.json")
    assert set(basis["rules"]["wording_kind"].values()) == {CA.MINIMUM}
    assert basis["rules"]["r4"]["scope"] == "minimum cover" and basis["rules"]["r4"]["value"] == 70
    assert basis["rules"]["note"]["rule_id"] == "P8-N22" and basis["rules"]["note"]["page"] == 8


def test_no_footing_detail_fixes_the_cover(summary):
    basis = J(PKG / "02_COVER_BASIS.json")
    for name in ("SHALLOW", "DEEP"):
        d = basis["footing_details"][name]
        assert d["ticks_on_bottom_bar_line"] == 0 and d["ticks_on_bar_leg_lines"] == 0
        assert d["dimension_ticks"] > 0                                  # the detail is dimensioned elsewhere
    vis = J(PKG / "source_search_inputs" / "D1_2_VISUAL_SEARCH.json")
    for name in ("SHALLOW", "DEEP"):
        assert vis["p13_footing_details"][name]["bar_to_concrete_face_dimension"] == "NONE"
        assert vis["p13_footing_details"][name]["cover_annotation"] == "NONE"
    dx = basis["dxf"]
    assert dx["cover_text_hits"] == 0 and dx["arabic_cover_hits"] == 0 and dx["texts_scanned"] > 1000
    assert dx["seven_point_five_cm"]["layers"] == ["S-DIM.SCH"] and dx["note_22_in_dxf"] is False
    ss = summary["source_search"]
    assert ss == {"dxf_cover_hits": 0, "dxf_texts_scanned": dx["texts_scanned"], "ocr_footing_cover_hits": 0,
                  "p13_ticks_on_bar_lines": 0}


def test_cover_basis_is_minimum_project_cover_70(summary):
    b = summary["cover_basis"]
    assert b == {"basis": CA.MINIMUM_PROJECT_COVER, "label": "MINIMUM_PROJECT_COVER_70", "source": "GENERAL_RULE",
                 "value_mm": 70.0}
    assert J(PKG / "02_COVER_BASIS.json")["basis"] == b
    assert J(PKG / "02_COVER_BASIS.json")["outcomes_considered"] == [
        "EXACT_PROJECT_COVER_70", "MINIMUM_PROJECT_COVER_70", "DERIVED_EXACT_COVER", "BOUNDED_COVER", "UNRESOLVED"]


# ------------------------------------------------------------------ the parts
def test_every_mass_bearing_part_is_audited_once(audit, frozen_parts):
    assert len(audit) == len(frozen_parts) == 60
    ids = [f"{a['OCCURRENCE_ID']}:{a['COMPONENT']}" for a in audit]
    assert len(set(ids)) == 60 and set(ids) == set(frozen_parts)
    assert {a["S4_1_DELTA_ID"] for a in audit} == {m["DELTA_ID"] for _, m in frozen_parts.values()}
    k = Counter(f"{a['LAYERING']}:{a['COMPONENT']}" for a in audit)
    assert k == {"SINGLE_LAYER:BOTTOM_LONG": 20, "SINGLE_LAYER:BOTTOM_SHORT": 20, "TWO_LAYER:BOTTOM_LONG": 5,
                 "TWO_LAYER:BOTTOM_SHORT": 5, "TWO_LAYER:TOP_LONG": 5, "TWO_LAYER:TOP_SHORT": 5}


def test_straight_run_is_span_minus_140_and_a_maximum(audit, frozen_parts):
    for a in audit:
        p, _ = frozen_parts[f"{a['OCCURRENCE_ID']}:{a['COMPONENT']}"]
        inp = p["provenance"]["INPUTS"]
        assert float(inp["cover_1_mm"]) == float(inp["cover_2_mm"]) == 70.0
        span = float(inp["raw_span_mm"])
        assert float(a["FOOTING_DIMENSION_MM"]) == span
        assert abs(float(a["CURRENT_LENGTH_MM"]) - (span - 140.0)) < 1e-9
        assert abs(float(inp["net_straight_mm"]) - (span - 140.0)) < 1e-9
        assert a["A_STRAIGHT_SEGMENT_STATE"] == a["NEW_LENGTH_STATE"] == CA.SOURCE_MAXIMUM_STRAIGHT_RUN
        assert a["A_STRAIGHT_SEGMENT_DIRECTION"] == CA.UPPER
        # any actual cover above the minimum gives a shorter straight run
        assert CA.straight_run_mm(span, 71, 71) < float(a["CURRENT_LENGTH_MM"])


def test_rate_counts_rederived_and_count_directions(audit, frozen_parts):
    for a in audit:
        p, _ = frozen_parts[f"{a['OCCURRENCE_ID']}:{a['COMPONENT']}"]
        inp = p["provenance"]["INPUTS"]
        if a["LAYERING"] == "SINGLE_LAYER":
            assert a["COUNT_MODE"] == "EXPLICIT_COUNT" and a["B_COUNT_DIRECTION"] == CA.EXACT
            assert int(a["COUNT_USED"]) == int(inp["count_value"])
        else:
            assert a["COUNT_MODE"] == "BARS_PER_METRE" and a["B_COUNT_DIRECTION"] == CA.NONE
            n = math.ceil(float(inp["count_value"]) * (float(inp["distribution_mm"]) - 140.0) / 1000.0 - 1e-9)
            assert int(a["COUNT_USED"]) == int(inp["count_used"]) == n
            # a larger actual cover can only lower the count; the edge-bar convention raises it
            assert CA.count_at_cover(float(inp["count_value"]), float(inp["distribution_mm"]), 100) <= n
            assert int(a["COUNT_WITH_EDGE_BARS"]) >= n


def test_kg_is_rederived_and_unchanged(audit, frozen_parts, corr):
    total = 0.0
    for a in audit:
        p, m = frozen_parts[f"{a['OCCURRENCE_ID']}:{a['COMPONENT']}"]
        inp = p["provenance"]["INPUTS"]
        d = int(inp["dia_mm"])
        kg = int(inp["count_used"]) * (float(inp["raw_span_mm"]) - 140.0) / 1000.0 * d * d / 162.0
        assert abs(kg - float(p["kg"])) < 1e-6 and abs(kg - float(m["NEW_KNOWN_QUANTITY"])) < 1e-4
        assert abs(float(a["KG_AT_MIN_COVER"]) - kg) < 1e-4
        total += float(p["kg"])
    assert abs(total - J(S41 / "S4_1_RELEASE_SUMMARY.json")["s4_1_known_kg"]) < 1e-6
    assert abs(total - 3629.5995) < 1e-3
    assert all(float(c["CORRECTION_KG"]) == 0.0 for c in corr)


def test_every_part_moves_to_project_basis_numeric_and_none_stays_a_lower_bound(audit, corr, frozen_parts):
    assert all(a["ORIGINAL_STATE"] == CA.LOWER_BOUND for a in audit)
    assert all(a["MASS_STATE"] == CA.PROJECT_BASIS_NUMERIC and a["MASS_DIRECTION"] == CA.NONE for a in audit)
    assert all(a["AS_BUILT_KG_STATE"] == "NOT_ESTABLISHED" for a in audit)
    assert all(a["C_END_PORTIONS_STATE"] == "BLOCKED_UNQUANTIFIED" for a in audit)
    assert not any(c["NEW_MASS_STATE"] == CA.LOWER_BOUND for c in corr)
    assert {c["COMPONENT_ID"] for c in corr} == set(frozen_parts)
    for c in corr:
        assert c["RECORD_TYPE"] == CA.RECORD_TYPE and c["COVER_BASIS"] == CA.MINIMUM_PROJECT_COVER
        assert c["ORIGINAL_STATE"] == CA.LOWER_BOUND and c["NEW_MASS_STATE"] == CA.PROJECT_BASIS_NUMERIC
        assert c["NEW_LENGTH_STATE"] == CA.SOURCE_MAXIMUM_STRAIGHT_RUN
        assert abs(float(c["RETAINED_NUMERIC_KG"]) - float(c["ORIGINAL_KG"])) < 1e-9
    # every S4.1 row in the LOWER_BOUND state (the kg rows and their zero-kg portions) belongs to a corrected part
    lb = {r["BASELINE_COMPONENT_ID"] for r in rows(S41 / "S4_1_DELTA_COMPONENTS.csv")
          if r["NEW_RELEASE_STATE"] == CA.LOWER_BOUND}
    assert lb == {c["COMPONENT_ID"] for c in corr}


def test_the_three_uncertainties_are_kept_apart(audit):
    for a in audit:
        run, cnt = a["A_STRAIGHT_SEGMENT_DIRECTION"], a["B_COUNT_DIRECTION"]
        assert CA.with_unquantified_additions(CA.combine(run, cnt), 1) == a["MASS_DIRECTION"]
        assert a["C_END_PORTIONS"] in ("U-bar legs / 45° hooks / bends SHAPE_FOUND_LENGTH_BLOCKED",
                                       "END_TREATMENT_NOT_ESTABLISHED")


# ------------------------------------------------------------------ figures
def test_correction_conservation(summary, corr):
    s = summary["s4_1"]
    cons = s["conservation"]
    assert cons["all_pass"] and all(cons["checks"].values()) and cons["correction_kg"] == 0.0
    assert cons["original_known"] == cons["corrected_known"] == J(S41 / "S4_1_RELEASE_SUMMARY.json")["s4_1_known_kg"]
    recs = [{k: float(c[k]) for k in ("CORRECTION_KG", "RETAINED_NUMERIC_KG", "ORIGINAL_KG")} for c in corr]
    assert CA.conservation(cons["original_known"], recs, cons["corrected_known"])["all_pass"]
    assert s["parts_affected"] == 60 and abs(s["kg_affected"] - cons["original_known"]) < 1e-9
    assert s["by_layering"]["SINGLE_LAYER"]["parts"] == 40 and s["by_layering"]["TWO_LAYER"]["parts"] == 20
    assert abs(s["by_layering"]["SINGLE_LAYER"]["kg"] + s["by_layering"]["TWO_LAYER"]["kg"] - s["kg_affected"]) < 1e-6


def test_two_figures_kept_apart(summary):
    s = summary["s4_1"]
    assert abs(s["known_numerical_kg_at_min_cover"] - 3629.5995) < 1e-3 and s["known_actual_as_built_kg"] is None
    c = summary["combined"]
    d11 = J(D11 / "06_CORRECTED_RELEASE_SUMMARY.json")["combined"]
    assert abs(c["project_drawing_basis_kg"] - d11["corrected_kg"]) < 1e-6
    p = c["parts"]
    assert abs(sum(v["project_basis_kg"] for v in p.values()) - c["project_drawing_basis_kg"]) < 1e-6
    assert p["S4.1"]["as_built_lower_bound_kg"] is None
    assert abs(p["S5.1"]["as_built_lower_bound_kg"] + p["S6.1"]["as_built_lower_bound_kg"]
               - c["as_built_lower_bound_known_kg"]) < 1e-6
    assert round(c["project_drawing_basis_kg"], 2) == 9080.60 and round(c["as_built_lower_bound_known_kg"], 2) == 5451.00
    assert c["s5_s6_cover_independent"]["s5_components_checked"] > 0
    assert c["s5_s6_cover_independent"]["s6_components_checked"] > 0


# ------------------------------------------------------------------ provenance / flags
def test_provenance_carries_every_audit_and_correction(audit, corr):
    lines = [json.loads(x) for x in (PKG / "06_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    k = Counter(x["kind"] for x in lines)
    assert k["AUDIT"] == len(audit) and k[CA.RECORD_TYPE] == len(corr)
    s41 = sha(S41 / "S4_1_FREEZE_MANIFEST.json")
    assert all(x["frozen_s4_1_manifest"] == s41 for x in lines)


def test_summary_flags(summary):
    assert summary["flags"] == {"actual_cover_assumed": False, "cover_invented": False,
                                "frozen_outputs_changed": False, "plotted_scale_used": False,
                                "pre_s7_started": False, "references_read": [], "silent_lower_bound": False}
    assert summary["round"] == "D1.2" and summary["baseline_head"] == "1384bf3"
    assert summary["policy"] == "FOOTING_COVER_AUTHORITY_AUDIT_V1"
    assert summary["cover_policy"] == CA.policy_record()
