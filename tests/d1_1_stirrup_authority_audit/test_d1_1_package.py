"""D1.1 package (research/d1_1_stirrup_authority_audit): link-path authority errata over frozen S6.1 / S5.1.

Every number is re-derived here from the frozen S6.1 / S5.1 delta rows and their own summaries - never against a
reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_correction as DC

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "d1_1_stirrup_authority_audit"
R = ROOT / "research"
S61 = R / "alsenan_superstructure_beam_rebar_s6_1"
S51 = R / "alsenan_ground_system_rebar_s5_1"
FROZEN = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
          "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
          "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
          "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
          "S6.1": S61 / "S6_1_FREEZE_MANIFEST.json",
          "S5.1": S51 / "S5_1_FREEZE_MANIFEST.json",
          "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json"}
AD1 = R / "ad1_authority_decisions"
STR2 = "STR2_OUTER_PLUS_ONE_INNER_4_LEG"
STR3 = "STR3_OUTER_PLUS_TWO_INNER_6_LEG"
BLOCKED = "BLOCKED_UNQUANTIFIED"
DC_CANDIDATE = "CANDIDATE_ONLY"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "06_CORRECTED_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def audit():
    return rows(PKG / "02_STIRRUP_PATH_AUDIT.csv")


@pytest.fixture(scope="module")
def c6():
    return rows(PKG / "03_S6_1A_CORRECTIONS.csv")


@pytest.fixture(scope="module")
def c5():
    return rows(PKG / "04_S5_1A_CORRECTIONS.csv")


@pytest.fixture(scope="module")
def reg():
    return rows(PKG / "05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv")


@pytest.fixture(scope="module")
def released():
    out = {}
    for stage, p in (("S6.1", S61 / "S6_1_DELTA_COMPONENTS.csv"), ("S5.1", S51 / "S5_1_DELTA_COMPONENTS.csv")):
        out[stage] = [r for r in rows(p) if r["CHANGE_KIND"] == "QUANTITY_RELEASED"]
    return out


def f(x):
    return float(x) if x not in ("", None) else 0.0


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("00_README.md", "01_SOURCE_SEARCH.md", "02_STIRRUP_PATH_AUDIT.csv", "03_S6_1A_CORRECTIONS.csv",
              "04_S5_1A_CORRECTIONS.csv", "05_TOPOLOGY_COUNT_DIAMETER_REGISTER.csv",
              "06_CORRECTED_RELEASE_SUMMARY.json", "07_PROVENANCE.jsonl", "TEST_RUN.md", "D1_1_FREEZE_MANIFEST.json"):
        assert (PKG / n).is_file(), n


def test_d1_1_freeze_manifest_still_matches():
    m = J(PKG / "D1_1_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert sha(base / k) == h, (group, k)


def test_frozen_s4_s5_s6_s4_1_s6_1_s5_1_and_ad1_are_immutable(summary):
    for name, man in FROZEN.items():
        m = J(man)
        base = man.parent
        for group, b in (("code", ROOT), ("inputs", ROOT), ("outputs", base)):
            for k, h in m.get(group, {}).items():
                assert sha(b / k) == h, (name, group, k)
        assert summary["frozen"][name]["manifest_sha256"] == sha(man), name
    assert not summary["flags"]["frozen_outputs_changed"]


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "D1_1_FREEZE_MANIFEST.json")["outputs"]}
    before["D1_1_FREEZE_MANIFEST.json"] = (PKG / "D1_1_FREEZE_MANIFEST.json").read_bytes()
    subprocess.run([sys.executable, "-I", str(PKG / "build_d1_1_stirrup_audit.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (PKG / "build_d1_1_stirrup_audit.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3", "ACI", "BS 8666",
                "Eurocode", "EN 1992"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/d1_1_stirrup_authority_audit/build_d1_1_stirrup_audit.py" in RP.ACCURATE_BUILDERS
    assert "engine/source/delta_correction.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ source search
def test_source_search_finds_no_bend_radius_hook_length_or_closure(summary):
    ss = summary["source_search"]
    assert ss["bend_radius_in_source"] is False
    assert ss["hook_length_in_source"] is False
    assert ss["closure_in_source"] is False
    assert ss["radial_dimensions"] == 0 and ss["dxf_texts_scanned"] > 1000
    for k in ("BEND_RADIUS", "BEND_DIAMETER", "CENTRELINE_BEND_GEOMETRY", "CLOSURE_LAP"):
        assert ss["findings"][k].startswith("SOURCE_EXPECTED_NOT_LOCATED"), k
    assert ss["drawn_link_corners"] and all(v.startswith("ROUNDED") for v in ss["drawn_link_corners"].values())
    md = (PKG / "01_SOURCE_SEARCH.md").read_text(encoding="utf-8")
    assert "P8-N03" in md and "P8-N22" in md


def test_mathematics_is_recorded(summary):
    m = summary["mathematics"]
    assert m["sharp_loop"] == "2W + 2T" and m["rounded_loop"] == "2W + 2T - (8 - 2 pi) R"
    assert "MODELLED_POLYGONAL_EQUIVALENT" in m["conclusion"]


# ------------------------------------------------------------------ the link paths
def test_every_released_row_is_audited_once(audit, released):
    for stage in ("S6.1", "S5.1"):
        ids = [a["ORIGINAL_DELTA_ID"] for a in audit if a["STAGE"] == stage]
        assert len(ids) == len(set(ids))
        assert set(ids) == {r["DELTA_ID"] for r in released[stage]}, stage


def test_every_sharp_path_is_a_modelled_polygonal_equivalent(audit):
    links = [a for a in audit if a["OBJECT_KIND"] == "LINK_CORE_PATH"]
    assert len(links) == 88 + 6
    for a in links:
        b, h, c, d = f(a["B_MM"]), f(a["H_MM"]), f(a["COVER_MM"]), f(a["LINK_DIA_MM"])
        W, T = b - 2 * c - d, h - 2 * c - d
        assert f(a["SHARP_PATH_MM"]) == pytest.approx(DC.sharp_loop_mm(W, T))
        kg = int(a["COUNT"]) * DC.sharp_loop_mm(W, T) / 1000.0 * d * d / 162.0
        assert f(a["ORIGINAL_KG"]) == pytest.approx(kg, abs=2e-6), a["AUDIT_ID"]
        assert a["CLASSIFICATION"] == DC.MODELLED_POLYGONAL_EQUIVALENT
        assert a["BEND_RADIUS_R"] == "NOT_IN_SOURCE" and a["CLOSURE"] == "NOT_IN_SOURCE"
        assert a["HOOK_LENGTH"].startswith("NOT_IN_SOURCE")
        assert f(a["SOURCE_SAFE_KG"]) == 0.0
        assert f(a["MODELLED_ONLY_KG"]) == f(a["BLOCKED_KG"]) == f(a["ORIGINAL_KG"])
        assert a["AUDIT_RESULT"] == "RETRACTED_TO_MODELLED" and a["MASS_USE"].startswith("QA_ONLY")


@pytest.mark.parametrize("stage,fixture,n,prefix", [("S6.1", "c6", 88, "S6_1"), ("S5.1", "c5", 6, "S5_1")])
def test_errata_retract_every_link_kg(request, released, stage, fixture, n, prefix):
    cs = request.getfixturevalue(fixture)
    assert len(cs) == n
    core = {r["DELTA_ID"]: r for r in released[stage] if r["PORTION"] == "CORE_PATH"}
    assert {c["ORIGINAL_DELTA_ID"] for c in cs} == set(core)
    pkg = S61 if stage == "S6.1" else S51
    s = J(pkg / f"{prefix}_RELEASE_SUMMARY.json")
    assert sum(f(c["ORIGINAL_KG"]) for c in cs) == pytest.approx(s["delta_by_kind_kg"]["stirrup_core_path"],
                                                                 abs=1e-4)
    for c in cs:
        assert c["RECORD_TYPE"] == DC.RECORD_TYPE
        assert c["NEW_AUTHORITY_STATE"] == DC.MODELLED_POLYGONAL_EQUIVALENT
        assert c["NEW_RELEASE_STATE"] == BLOCKED
        assert f(c["CORRECTION_KG"]) == pytest.approx(-f(c["ORIGINAL_KG"])) and f(c["CORRECTION_KG"]) < 0
        assert f(c["RETAINED_KG"]) == 0.0
        assert f(c["ORIGINAL_KG"]) == pytest.approx(f(core[c["ORIGINAL_DELTA_ID"]]["DELTA_KNOWN_QUANTITY"]),
                                                    abs=2e-6)
        assert c["TOPOLOGY_KEPT"] == c["COUNT_KEPT"] == c["DIAMETER_KEPT"] == "YES"
        assert c["CORRECTION_REASON"] and c["SOURCE_EVIDENCE"]


def test_corrections_are_never_positive_and_modelled_keeps_zero(c6, c5):
    for c in c6 + c5:
        assert f(c["CORRECTION_KG"]) <= 0
        if c["NEW_AUTHORITY_STATE"] not in DC.RETAINING_STATES:
            assert f(c["RETAINED_KG"]) == 0.0


# ------------------------------------------------------------------ what stays released
def test_s6_1_longitudinal_and_planted_releases_unaffected(audit, summary):
    s = J(S61 / "S6_1_RELEASE_SUMMARY.json")["delta_by_kind_kg"]
    kept = [a for a in audit if a["STAGE"] == "S6.1" and a["AUDIT_RESULT"] == "RETAINED"]
    long_ = [a for a in kept if a["OBJECT_KIND"] == "LONGITUDINAL_BASE_BAR"]
    extra = [a for a in kept if a["OBJECT_KIND"] == "PLANTED_COLUMN_EXTRA_PROJECTION"]
    assert {a["MARK"] for a in long_} == {"B3", "B26"} and [a["MARK"] for a in extra] == ["B26"]
    assert sum(f(a["SOURCE_SAFE_KG"]) for a in long_) == pytest.approx(s["longitudinal_base_bars"], abs=1e-4)
    assert sum(f(a["SOURCE_SAFE_KG"]) for a in extra) == pytest.approx(s["planted_column_extra"], abs=1e-5)
    for a in kept:
        assert a["CLASSIFICATION"] == "INDEPENDENT_OF_BEND_GEOMETRY"
        assert f(a["SOURCE_SAFE_KG"]) == f(a["ORIGINAL_KG"]) and f(a["BLOCKED_KG"]) == 0.0
    o = summary["s6_1"]["other_retained_kg"]
    assert o["longitudinal_base_bars"] == pytest.approx(s["longitudinal_base_bars"])
    assert o["planted_column_extra"] == pytest.approx(s["planted_column_extra"])


def test_cb7_and_other_stirrup_counts_retained(audit, summary):
    counts = summary["s6_1"]["stirrup_counts_retained"]
    assert counts["CBO-GFRS-CB7-BL003#1"] == 39 and counts["CBO-GFRS-CB7-BL003#2"] == 41
    kept = {(a["OCCURRENCE_ID"], a["SPAN_INDEX"]): int(a["DELTA_COUNT"]) for a in audit
            if a["OBJECT_KIND"] == "STIRRUP_COUNT"}
    assert len(kept) == len(counts) == 5
    assert all(counts[f"{o}#{s}"] == n for (o, s), n in kept.items())


def test_s5_1_through_support_release_unaffected(audit, summary):
    s = J(S51 / "S5_1_RELEASE_SUMMARY.json")["delta_by_kind_kg"]
    ts = [a for a in audit if a["STAGE"] == "S5.1" and a["OBJECT_KIND"] == "THROUGH_SUPPORT_PORTION"]
    assert ts and all(a["AUDIT_RESULT"] == "RETAINED" for a in ts)
    assert sum(f(a["SOURCE_SAFE_KG"]) for a in ts) == pytest.approx(s["longitudinal_through_support"], abs=1e-4)
    assert summary["s5_1"]["other_retained_kg"]["through_support"] == pytest.approx(25.60, abs=0.005)


def test_correction_conservation(summary, c6, c5):
    ad1 = rows(AD1 / "05_S5_AD1_CORRECTIONS.csv")
    s6, s5 = summary["s6_1"], summary["s5_1"]
    assert s6["conservation"]["all_pass"] and s5["conservation"]["all_pass"]
    assert s5["conservation_link_only"]["all_pass"]
    assert s6["d1_known_kg"] + sum(f(c["CORRECTION_KG"]) for c in c6) == pytest.approx(s6["corrected_known_kg"],
                                                                                        abs=1e-4)
    link5 = s5["d1_known_kg"] + sum(f(c["CORRECTION_KG"]) for c in c5)
    assert link5 == pytest.approx(s5["corrected_known_kg_link_only"], abs=1e-4)
    assert link5 + sum(f(c["CORRECTION_KG"]) for c in ad1) == pytest.approx(s5["corrected_known_kg"], abs=1e-4)
    assert s5["ad1_correction_kg"] == pytest.approx(-47.366667, abs=1e-5) and s5["ad1_corrections"] == len(ad1) == 6
    for s in (s6, s5):
        assert s["link_kg_retained"] == 0.0 and s["link_kg_retracted"] == pytest.approx(s["link_core_path_kg_released"])
    assert s6["corrected_known_kg"] == pytest.approx(s6["frozen_s6_known_kg"] + sum(s6["other_retained_kg"].values()))
    assert s5["corrected_known_kg"] == pytest.approx(s5["frozen_s5_known_kg"] + sum(s5["other_retained_kg"].values())
                                                     + s5["ad1_correction_kg"])
    cb = summary["combined"]
    assert cb["corrected_kg"] == pytest.approx(summary["s4_1"]["known_kg"] + s6["corrected_known_kg"] +
                                               s5["corrected_known_kg"])
    assert cb["d1_kg"] - cb["corrected_kg_link_only"] == pytest.approx(s6["link_kg_retracted"] +
                                                                       s5["link_kg_retracted"])
    assert cb["corrected_kg_link_only"] - cb["corrected_kg"] == pytest.approx(-s5["ad1_correction_kg"])
    assert cb["frozen_s4_s5_s6_kg"] <= cb["corrected_kg"] <= cb["d1_kg"]


# ------------------------------------------------------------------ topology / count / diameter
def test_register_keeps_four_facts_separate(reg):
    assert len(reg) == 180
    s61_sets = rows(S61 / "S6_1_STIRRUP_TOPOLOGY.csv")
    assert sum(1 for r in reg if r["STAGE"] == "S6.1") == len(s61_sets)
    no_detail = {r["GB_SPAN_ID"] for r in rows(AD1 / "06_GB_CONCENTRATED_REACTION_REGISTER.csv")
                 if r["NO_DETAIL_CASE"] == "True"}
    for r in reg:
        assert r["A_LINK_TOPOLOGY"]
        if r["OCCURRENCE_ID"] in no_detail:
            assert r["STAGE"] == "S5.1" and r["TOPOLOGY_STATE"].startswith(DC_CANDIDATE)
            assert not r["B_LINK_COUNT"] and not r["C_LINK_DIAMETER_MM"]
        else:
            assert r["TOPOLOGY_STATE"].startswith("SOURCE_FOUND_DERIVED")
        assert r["D_LINK_CUT_LENGTH"] == BLOCKED and r["LINK_MASS"] == BLOCKED
        assert r["HOOK_EXTENSION"] == BLOCKED
        assert r["HOOK_SHAPE"] in ("SOURCE_EXPLICIT_SHAPE_ONLY", "NOT_ESTABLISHED")
        assert int(r["LEGS"]) == 2 * int(r["LINKS"])
    assert sum(1 for r in reg if r["TOPOLOGY_STATE"].startswith(DC_CANDIDATE)) == len(no_detail) == 18


def test_str2_topology_survives_the_mass_block(reg):
    s2 = [r for r in reg if r["A_LINK_TOPOLOGY"] == STR2]
    assert {r["MARK"] for r in s2 if r["STAGE"] == "S5.1"} == {"SB1", "SB3"}
    assert len([r for r in s2 if r["STAGE"] == "S6.1"]) == 9
    for r in s2:
        assert r["LINKS"] == "2" and r["LEGS"] == "4" and r["D_LINK_CUT_LENGTH"] == BLOCKED
        assert r["INNER_LINK"].startswith(BLOCKED)


def test_str3_topology_survives_the_mass_block(reg):
    s3 = [r for r in reg if r["A_LINK_TOPOLOGY"] == STR3]
    assert [r["MARK"] for r in s3] == ["SB2"]
    r = s3[0]
    assert r["LINKS"] == "3" and r["LEGS"] == "6" and r["D_LINK_CUT_LENGTH"] == BLOCKED
    assert "SOURCE_CONFLICT" in r["TOPOLOGY_STATE"]


def test_known_count_and_diameter_with_unknown_mass(reg, c6, c5):
    by = {}
    for r in reg:
        by[(r["OCCURRENCE_ID"], r["SPAN_INDEX"])] = r
    with_count = [r for r in reg if r["B_LINK_COUNT"]]
    assert len(with_count) == 116 and all(r["LINK_MASS"] == BLOCKED for r in with_count)
    for c in c6 + c5:
        span = c["ORIGINAL_DELTA_COMPONENT_ID"].split("|SPAN")[1].split(":")[0] \
            if "|SPAN" in c["ORIGINAL_DELTA_COMPONENT_ID"] else "1"
        r = by[(c["OCCURRENCE_ID"], span)]
        assert int(r["B_LINK_COUNT"]) == int(c["COUNT"]), c["CORRECTION_ID"]
        assert float(r["C_LINK_DIAMETER_MM"]) == float(c["LINK_DIA_MM"]), c["CORRECTION_ID"]
        assert r["A_LINK_TOPOLOGY"] == c["TOPOLOGY"]
        assert float(r["MODELLED_SHARP_PATH_MM_QA_ONLY"]) == float(c["MODELLED_SHARP_PATH_MM"])


def test_topology_register_summary(summary, reg):
    t = summary["topology_count_diameter"]
    assert t["stirrup_sets"] == len(reg) == t["cut_length_blocked"]
    assert t["by_topology"] == dict(Counter(r["A_LINK_TOPOLOGY"] for r in reg))
    assert t["with_count"] == 116 and t["with_diameter"] == sum(1 for r in reg if r["C_LINK_DIAMETER_MM"])
    assert t["topology_state"] == {"CANDIDATE_ONLY": 18, "ESTABLISHED": 162}
    assert t["hook_extension_blocked"] == 180 and sum(t["hook_shape"].values()) == 180
    assert all(r["COUNT_BASIS"].startswith("RATE x") for r in reg if r["B_LINK_COUNT"])


# ------------------------------------------------------------------ provenance / flags
def test_provenance_carries_every_audit_and_erratum(audit, c6, c5):
    lines = [json.loads(x) for x in (PKG / "07_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    k = Counter(x["kind"] for x in lines)
    assert k["AUDIT"] == len(audit) and k[DC.RECORD_TYPE] == len(c6) + len(c5)
    for x in lines:
        if x["kind"] == DC.RECORD_TYPE:
            assert set(DC.FIELDS) <= set(x) and x["CORRECTION_KG"] <= 0


def test_summary_flags(summary):
    fl = summary["flags"]
    assert fl == {"external_code_used": False, "frozen_outputs_changed": False, "hook_length_used_as_proof": False,
                  "normal_delta_rule_changed": False, "plotted_scale_used": False, "pre_s7_started": False,
                  "q2_analysis_promoted": False, "references_read": []}
    assert summary["baseline_head"] == "59f2083" and summary["revision"] == 2
    ad = summary["authority_decisions"]
    assert ad["decisions"] == [f"AD-{i}" for i in range(1, 10)] and ad["q2_analysis_promoted"] is False
    assert ad["q2_prior_analysis"] == "CLAUDE_ENGINEERING_ANALYSIS"
    assert ad["manifest_sha256"] == sha(AD1 / "AD1_FREEZE_MANIFEST.json")
