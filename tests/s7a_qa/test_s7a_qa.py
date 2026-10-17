"""S7A (research/alsenan_slab_rebar_s7a_qa): dated engineering QA over the frozen S7 slab release.

S7 must stay byte-identical. Reading A must reproduce S7's top extensions, and every other reading is
sensitivity-only, checked against its own definition. The interpretation must stay NOT_ESTABLISHED, with evidence on
both sides. The errata must cover every S7 'lower bound' claim and change no kg."""

from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import delta_release as DR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_slab_rebar_s7a_qa"
S7P = ROOT / "research" / "alsenan_slab_rebar_s7"
P71 = ROOT / "research" / "alsenan_slab_rebar_pre_s7_1"
OUTPUTS = ["00_README.md", "01_TOP_EXTENT_INTERPRETATIONS.csv", "02_SOURCE_EVIDENCE.json",
           "03_BAR_FAMILY_IDENTITY_QA.csv", "04_TOP_SENSITIVITY_SCENARIOS.csv", "05_TOP_SENSITIVITY_BY_END_CLASS.csv",
           "06_TOP_SENSITIVITY_BY_STRIP_END.csv", "07_BOTTOM_RULE_SUPPORT_TYPE_TABLE.csv",
           "08_END_CONDITION_AUDIT.csv", "09_S7_ERRATA.json", "10_S7A_SUMMARY.json"]
S7_TOTAL = 3802.015364542
SCEN = ("A", "B", "C", "D1", "D2", "E")


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    with open(p, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def f(v):
    return float(v) if v not in ("", None) else None


@pytest.fixture(scope="module")
def mod():
    spec = importlib.util.spec_from_file_location("build_s7a_qa", PKG / "build_s7a_qa.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "10_S7A_SUMMARY.json")


@pytest.fixture(scope="module")
def ends():
    return rows(PKG / "06_TOP_SENSITIVITY_BY_STRIP_END.csv")


# ------------------------------------------------------------------ freeze, S7 untouched
def test_freeze_manifest_still_matches():
    m = J(PKG / "11_S7A_FREEZE_MANIFEST.json")
    assert m["round"] == "S7A_QA" and m["state"] == "FROZEN_QA_LAYER_NO_RELEASE" and m["references_read"] == []
    assert set(m["outputs"]) == set(OUTPUTS)
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    assert DR.verify_frozen(PKG / "11_S7A_FREEZE_MANIFEST.json", ROOT)["round"] == "S7A_QA"


def test_s7_is_untouched(summary):
    m = DR.verify_frozen(S7P / "12_S7_FREEZE_MANIFEST.json", ROOT)
    assert m["round"] == "S7"
    tot = J(S7P / "09_S7_PROJECT_SUMMARY.json")["totals_kg"]["RESTRICTED_S7_PROJECT_BASIS_KG"]
    assert abs(tot - S7_TOTAL) < 1e-6 and abs(summary["s7_frozen_total_kg"] - tot) < 1e-12
    assert summary["s7_total_unchanged"] is True and summary["s7_files_edited"] is False
    assert summary["released"] is False and summary["state"] == "SENSITIVITY_ONLY_NO_RELEASE"
    assert J(PKG / "11_S7A_FREEZE_MANIFEST.json")["s7_total_kg"] == "3802.015364542"


# ------------------------------------------------------------------ sources
def test_note_2_is_read_and_decoded_from_the_dxf():
    ev = J(PKG / "02_SOURCE_EVIDENCE.json")
    assert set(ev["note2"]) == {"GFRS", "FFRS", "SFRS"}
    for sheet, rec in ev["note2"].items():
        assert rec["spec"]["raw"] == "5%%C10/m"
        assert rec["tail"]["decoded"] == "الجسور بطول ثلث البحر في الاتجاهين" and rec["tail"]["decode_state"] == \
            "DECODED"
        assert "يجب وضع حديد علوي للبلاطات فوق" in rec["head"]["decoded"]
        assert rec["tail"]["font_family"] == "ARABIC_KEYBOARD_101"
    assert {ev["note2"][s]["tail"]["handle"] for s in ev["note2"]} == {"DA", "E3", "EC"}


def test_the_only_other_span_word_is_the_sea_view_marker():
    ev = J(PKG / "02_SOURCE_EVIDENCE.json")
    other = [o for o in ev["span_word"] if o["space"] != "MODEL"]
    assert other and all("SEA VIEW" in o["siblings_in_block"] for o in other) and ev["span_word_homonym"] is True
    assert {o["handle"] for o in ev["span_word"] if o["space"] == "MODEL"} == {"DA", "E3", "EC"}


def test_beam_schedule_measures_per_side_from_the_support():
    bs = J(PKG / "02_SOURCE_EVIDENCE.json")["beam_schedule"]
    assert len(bs["per_side_pairs"]) >= 3
    for p in bs["per_side_pairs"]:
        a, b = p["offsets_from_joint"]
        assert abs(a - b) < 1.0 and a > 100                      # symmetric about the support: from each face
        assert p["left"] != p["right"]                            # each side named by its own span (Ln / Ln1 / Ln2)


def test_p15_draws_the_continuous_top_bar_into_both_spans():
    s = J(PKG / "02_SOURCE_EVIDENCE.json")["p15_strokes"]
    assert s["nts"] is True and s["top_stroke_over_continuous_beam"] is True
    e = s["drawn_extent_from_face_pt"]
    assert e["continuous_L1_side"] > 50 and e["continuous_L2_side"] > 50 and e["non_continuous_anchor"] > 50
    assert abs(s["drawn_ratio_to_L1"]["non_continuous_anchor"] - 0.25) < 0.01
    vis = J(PKG / "02_SOURCE_EVIDENCE.json")["p15_visual_reading_frozen"]
    assert vis["span_basis"]["L1"].startswith("CLEAR_SPAN") and vis["which_50_percent"] == "NOT_STATED"


def test_interpretation_is_not_established_and_both_sides_are_kept(summary):
    assert summary["finding"]["one_third_extent"] == "NOT_ESTABLISHED_BY_SOURCE"
    assert summary["interpretation_selected_by_reference"] is False and summary["references_read"] == []
    it = rows(PKG / "01_TOP_EXTENT_INTERPRETATIONS.csv")
    assert {r["READING_ID"] for r in it} == {"I-A", "I-B", "I-C", "I-D", "I-E", "I-F"}
    for r in it:
        assert "ESTABLISHED" not in r["STATE"] or "NOT_ESTABLISHED" in r["STATE"], r
        assert json.loads(r["SUPPORTING_EVIDENCE"]) and json.loads(r["CONTRARY_EVIDENCE"]), r["READING_ID"]
    a = next(r for r in it if r["READING_ID"] == "I-A")
    assert "URBAN_OWNER_MEASUREMENT_RULE" in a["AUTHORITY"]


def test_family_identity_is_supported_not_proven():
    fam = rows(PKG / "03_BAR_FAMILY_IDENTITY_QA.csv")
    top = [r for r in fam if r["RULE_A"].startswith("P15-TOP")]
    assert {r["RULE_A"] for r in top} == {"P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax", "P15-TOP-EXTEND-50PCT"}
    for r in top:
        assert r["QA_STATE"] == "SAME_FAMILY_SUPPORTED_NOT_PROVEN" and json.loads(r["CONFLICTING_EVIDENCE"])
        assert "BLOCKED_UNQUANTIFIED" in r["IF_SEPARATE_FAMILIES"]
    assert any(r["QA_STATE"].startswith("SEPARATE_FAMILY") for r in fam)


# ------------------------------------------------------------------ sensitivity
def test_reading_a_reproduces_s7_exactly(ends, summary):
    s7 = J(S7P / "09_S7_PROJECT_SUMMARY.json")["totals_kg"]
    runs = [r for r in rows(S7P / "04_S7_BAR_RUNS.csv") if r["BAR_ROLE"] == "TOP_OVER_SUPPORT_EXTENSION"]
    assert len(ends) == len(runs) == summary["top_extension_strip_ends"]
    by = {r["BAR_RUN_ROW_ID"]: r for r in runs}
    for e in ends:
        assert f(e["KG_A"]) == f(e["S7_FROZEN_KG"]) == f(by[e["BAR_RUN_ROW_ID"]]["KG"])
        assert abs(f(e["RECOMPUTED_A_REL_DEVIATION"])) <= 1e-4
    assert abs(math.fsum(f(e["KG_A"]) for e in ends) - s7["TOP_EXTENSION_KG"]) <= 1e-6
    sc = {r["SCENARIO"]: r for r in rows(PKG / "04_TOP_SENSITIVITY_SCENARIOS.csv")}
    assert abs(f(sc["A"]["S7_SCOPE_TOTAL_UNDER_SCENARIO_KG"]) - S7_TOTAL) < 1e-6
    assert sc["A"]["STATE"] == "S7_FROZEN_REPRODUCED"


def test_each_scenario_follows_its_own_definition(ends):
    cont, nonc, unres = ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT"), "END_NON_CONTINUOUS", "END_UNRESOLVED"
    for e in ends:
        a = f(e["KG_A"])
        k = {s: f(e[f"KG_{s}"]) for s in SCEN}
        assert abs(k["B"] - a / 2) <= 1e-9 * max(1, a)                    # L/6 per side = half of L/3
        assert k["E"] >= a - 1e-9                                          # max(L_own, L_opp) >= L_own
        assert k["D2"] >= k["D1"] - 1e-9
        if e["END_CLASS"] == nonc:
            assert abs(k["C"] - k["B"]) <= 1e-9 * max(1, a) and abs(k["D1"] - 0.75 * a) <= 1e-9 * max(1, a)
            assert abs(k["E"] - a) <= 1e-9 * max(1, a)
        if e["END_CLASS"] in cont and f(e["OPPOSITE_UNMATCHED_WIDTH_MM"]) == 0:
            assert k["D1"] >= 0.9 * a - 1e-9                              # 0.30 x max >= 0.30 x own = 0.9 x (own/3)
        if e["END_CLASS"] == unres:
            assert abs(k["D1"] - 0.75 * a) <= 1e-9 * max(1, a)


def test_scenarios_are_sensitivity_only_and_reconcile(summary):
    sc = rows(PKG / "04_TOP_SENSITIVITY_SCENARIOS.csv")
    assert [r["SCENARIO"] for r in sc] == list(SCEN)
    a = next(r for r in sc if r["SCENARIO"] == "A")
    for r in sc:
        assert r["RELEASED"] == "False"
        assert r["STATE"] == ("S7_FROZEN_REPRODUCED" if r["SCENARIO"] == "A" else "SENSITIVITY_ONLY")
        assert abs(f(r["S7_SCOPE_TOTAL_UNDER_SCENARIO_KG"]) - (S7_TOTAL - f(a["TOP_EXTENSION_KG"]) +
                                                              f(r["TOP_EXTENSION_KG"]))) <= 1e-6
        assert f(r["TOP_SUPPORT_CROSSING_KG"]) == f(a["TOP_SUPPORT_CROSSING_KG"])
    by_cls = rows(PKG / "05_TOP_SENSITIVITY_BY_END_CLASS.csv")
    for s in SCEN:
        assert abs(math.fsum(f(r[f"KG_{s}"]) for r in by_cls) - f(next(x for x in sc if x["SCENARIO"] == s)[
            "TOP_EXTENSION_KG"])) <= 1e-6
    lo, hi = summary["scenario_range_top_extension_kg"]
    assert lo < f(a["TOP_EXTENSION_KG"]) < hi                       # S7's reading is inside, not at a bound


def test_integration_helpers_on_synthetic_strips(mod):
    own = mod._lin(0.0, 1000.0, 3000.0, 3000.0)
    opp = mod._lin(0.0, 1000.0, 2000.0, 4000.0)
    assert abs(mod._int_max(own, opp, 0.0, 1000.0) - (3000 * 500 + 0.5 * (3000 + 4000) * 500)) < 1e-6
    pieces, amb = mod.opposite_pieces(0.0, 1000.0, [{"t0": 200.0, "t1": 1200.0, "fn": opp}])
    assert amb == 0 and [round(p[0]) for p in pieces] == [0, 200] and pieces[0][2] is None
    I, unmatched, ambiguous = mod.extension_integrals(own, "END_CONTINUOUS_RUN", pieces)
    assert abs(unmatched - 200.0) < 1e-9 and ambiguous == 0
    assert abs(I["A"] - 3000 * 1000 / 3) < 1e-6 and abs(I["B"] - I["A"] / 2) < 1e-6
    I2, _, _ = mod.extension_integrals(own, "END_NON_CONTINUOUS", [(0.0, 1000.0, None, 0)])
    assert abs(I2["D1"] - 0.25 * 3000 * 1000) < 1e-6 and abs(I2["E"] - I2["A"]) < 1e-6
    with pytest.raises(mod.Stop):
        mod.extension_integrals(own, "END_OBLIQUE", [(0.0, 1000.0, None, 0)])


# ------------------------------------------------------------------ bottom rules, end conditions
def test_bottom_rule_table_by_support_type():
    t = {r["END_CLASS"]: r for r in rows(PKG / "07_BOTTOM_RULE_SUPPORT_TYPE_TABLE.csv")}
    assert set(t) >= {"END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT", "END_NON_CONTINUOUS", "END_UNRESOLVED",
                      "END_OBLIQUE", "END_NO_SUPPORT_RECORD", "END_OPENING"}
    assert t["END_CONTINUOUS_RUN"]["APPLICABILITY"] == "SOURCE_APPLIES"
    assert t["END_UNRESOLVED"]["APPLICABILITY"].startswith("INFERRED") and t["END_UNRESOLVED"]["QA_FLAG"] == \
        "INFERRED_CONTINUITY"
    assert f(t["END_NON_CONTINUOUS"]["S7_STOP_DEDUCTION_KG"]) == 0.0
    assert f(t["END_UNRESOLVED"]["S7_STOP_DEDUCTION_KG"]) > 0


def test_every_strip_end_is_graded(summary):
    audit = rows(PKG / "08_END_CONDITION_AUDIT.csv")
    strips = rows(P71 / "07_LOCAL_BAR_STRIPS.csv")
    assert len(audit) == 2 * len(strips)
    g = Counter(r["CONTINUITY_GRADE"] for r in audit)
    assert dict(g) == summary["end_condition_grades"]
    for r in audit:
        if r["END_CLASS"] in ("END_UNRESOLVED", "END_OBLIQUE", "END_NO_SUPPORT_RECORD"):
            assert r["CONTINUITY_GRADE"] == "NOT_ESTABLISHED" and r["QA_FLAG"]
        if r["CONTINUITY_GRADE"].startswith("INFERRED"):
            assert r["QA_FLAG"] == "CONTINUITY_INFERRED_OR_UNRESOLVED"
        if r["END_CLASS"] in ("END_CONTINUOUS_RUN", "END_CONTINUOUS_SPLIT"):
            assert r["SAME_LEVEL_BASIS"].startswith("INFERRED_FROM_PANEL_CLASS")
    s7te = J(S7P / "09_S7_PROJECT_SUMMARY.json")["totals_kg"]["TOP_EXTENSION_KG"]
    assert abs(math.fsum(f(r["S7_TOP_EXTENSION_KG_AT_END"]) for r in audit) - s7te) <= 1e-6
    assert g["INFERRED_FROM_S1_EDGE_ONLY"] > 0 and g["NOT_ESTABLISHED"] > 0


# ------------------------------------------------------------------ errata
def test_errata_withdraws_every_s7_lower_bound_claim():
    e = J(PKG / "09_S7_ERRATA.json")
    assert e["id"] == "S7A-E01" and e["kg_change"] == 0.0 and e["s7_files_edited"] is False
    assert e["s7_total_unchanged"] is True and abs(e["s7_total_kg"] - S7_TOTAL) < 1e-6
    rel = rows(S7P / "01_S7_RELEASE_ITEMS.csv")
    hit = [r for r in rel if e["withdrawn_wording"] in r["QUANTITY_AUTHORITY"]]
    assert len(hit) == len(rel) == e["where"]["01_S7_RELEASE_ITEMS.csv QUANTITY_AUTHORITY"]["rows"] == 476
    for claim in e["where"]["post_freeze"]:
        line = (ROOT / claim["file"]).read_text(encoding="utf-8").splitlines()[claim["line"] - 1]
        assert claim["wording"] in line, claim
    md = (S7P / "post_freeze" / "S7_POST_FREEZE_COMPARISON.md").read_text(encoding="utf-8").splitlines()
    lb = [i + 1 for i, ln in enumerate(md) if "lower bound" in ln.lower() or "lower-bound" in ln.lower()]
    s7_claims = {i for i in lb if "restricted" in md[i - 1].lower()}
    assert s7_claims == {c["line"] for c in e["where"]["post_freeze"]}
    for i in set(lb) - s7_claims:                                    # the other uses label R3 / R4 states, not S7
        assert "R4 kg (lower bound" in md[i - 1] or "R3" in md[i - 1], md[i - 1]
    assert "not a proven bound of the physical steel in either direction" in e["replacement_wording"]


# ------------------------------------------------------------------ blindness, registry, rebuild
def test_builder_is_blind():
    src = (PKG / "build_s7a_qa.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze_comparison", "rebar_truth", "rough_rebar", "benchmark", "DONORS", "donor",
                "rebar_sanity", "Quotation", "pricing", ".xlsx", "R4_TOKENS", "REFERENCE_TOTALS"):
        assert bad not in src, bad
    for line in src.splitlines():
        if line.startswith(("import ", "from ")):
            assert line.split()[1] in ("__future__", "csv", "hashlib", "io", "json", "math", "re", "sys",
                                       "collections", "pathlib", "engine.source", "vector_pdf"), line
    pf = [ln for ln in src.splitlines() if "post_freeze" in ln]
    assert all("S7_POST_FREEZE_COMPARISON.md" in ln or "post_freeze" in ln.split("#")[0] and "\"" in ln
               for ln in pf), pf
    assert "open(" not in "".join(ln for ln in pf)                   # the claim lines are named, never opened


def test_registry_lists_the_builder():
    reg = (ROOT / "tests/structural_comparison_engine/rebar_product_registry.py").read_text(encoding="utf-8")
    assert '"research/alsenan_slab_rebar_s7a_qa/build_s7a_qa.py"' in reg


def test_rebuild_is_byte_identical():
    m = J(PKG / "11_S7A_FREEZE_MANIFEST.json")
    before = {k: (PKG / k).read_bytes() for k in list(m["outputs"]) + ["11_S7A_FREEZE_MANIFEST.json"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_s7a_qa.py")], check=True, capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k
