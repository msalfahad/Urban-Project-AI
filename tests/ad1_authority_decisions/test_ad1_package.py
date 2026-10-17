"""AD1 package (research/ad1_authority_decisions): owner authority decisions recorded before D1.1, and their errata
over the frozen S4 / S5 / S6 / S4.1 / S6.1 / S5.1 releases. Re-derived from the frozen registers here."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import authority_decisions as AD

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "ad1_authority_decisions"
R = ROOT / "research"
S5 = R / "alsenan_ground_system_rebar_s5"
S51 = R / "alsenan_ground_system_rebar_s5_1"
P51 = R / "pre_s5_1_source_resolution"
FROZEN = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
          "S5": S5 / "S5_FREEZE_MANIFEST.json",
          "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
          "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
          "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
          "S5.1": S51 / "S5_1_FREEZE_MANIFEST.json"}
RETRACTED = {"GSO-142-7D8-1", "GSO-15D-7C8-1"}


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "07_AD1_SUMMARY.json")


@pytest.fixture(scope="module")
def decisions():
    return {d["DECISION_ID"]: d for d in J(PKG / "01_AUTHORITY_DECISIONS.json")["decisions"]}


@pytest.fixture(scope="module")
def errata():
    return rows(PKG / "04_AUTHORITY_STATE_ERRATA.csv")


@pytest.fixture(scope="module")
def corrections():
    return rows(PKG / "05_S5_AD1_CORRECTIONS.csv")


@pytest.fixture(scope="module")
def loads():
    return {r["GB_SPAN_ID"]: r for r in rows(PKG / "06_GB_CONCENTRATED_REACTION_REGISTER.csv")}


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("00_README.md", "01_AUTHORITY_DECISIONS.json", "02_REJECTED_ANALYSIS_VALUES.csv",
              "03_COMPLIANCE_REGISTER.csv", "04_AUTHORITY_STATE_ERRATA.csv", "05_S5_AD1_CORRECTIONS.csv",
              "06_GB_CONCENTRATED_REACTION_REGISTER.csv", "07_AD1_SUMMARY.json", "08_PROVENANCE.jsonl",
              "AD1_FREEZE_MANIFEST.json"):
        assert (PKG / n).is_file(), n


def test_ad1_freeze_manifest_still_matches():
    m = J(PKG / "AD1_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert sha(base / k) == h, (group, k)


def test_frozen_stages_are_immutable(summary):
    for name, man in FROZEN.items():
        m = J(man)
        for group, b in (("code", ROOT), ("inputs", ROOT), ("outputs", man.parent)):
            for k, h in m.get(group, {}).items():
                assert sha(b / k) == h, (name, group, k)
        assert summary["frozen"][name]["manifest_sha256"] == sha(man), name


def test_rebuild_is_byte_identical():
    names = list(J(PKG / "AD1_FREEZE_MANIFEST.json")["outputs"]) + ["AD1_FREEZE_MANIFEST.json"]
    before = {k: (PKG / k).read_bytes() for k in names}
    subprocess.run([sys.executable, "-I", str(PKG / "build_ad1_authority_decisions.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (PKG / "build_ad1_authority_decisions.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m3"):
        assert bad not in src, bad
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert "research/ad1_authority_decisions/build_ad1_authority_decisions.py" in RP.ACCURATE_BUILDERS
    assert "engine/source/authority_decisions.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ authority of the decisions themselves
def test_nine_owner_decisions_with_their_rulings(decisions):
    assert list(decisions) == [f"AD-{i}" for i in range(1, 10)]
    for d in decisions.values():
        assert d["PROVENANCE"] == AD.OWNER_AUTHORITY_DECISION and d["IS_ENGINEER_CLAIM"] is False
        assert d["IS_DRAWING_NOTE"] is False
    r = {k: d["RULINGS"] for k, d in decisions.items()}
    assert r["AD-1"] == {"COMPONENT_EXISTENCE": "SOURCE_EXPLICIT", "INVERTED_U_TOPOLOGY": "SOURCE_EXPLICIT",
                         "HOOKS": "NOT_ESTABLISHED", "MEANING_OF_3_PLUS_N": "PROJECT_PATTERN_ONLY",
                         "DIAMETER": "SOURCE_EXPECTED_NOT_LOCATED", "EXISTENCE_WHERE_FN_CELL_BLANK": "UNRESOLVED",
                         "KG": "BLOCKED_UNQUANTIFIED"}
    assert r["AD-2"]["BEAM_ANCHORAGE_FROM_NOTE"] == r["AD-2"]["GROUND_BEAM_ANCHORAGE_FROM_NOTE"] == "NOT_A_PROJECT_RULE"
    assert r["AD-3"] == {"EXPLICIT_BEND_SHAPE": "SOURCE_EXPLICIT_SHAPE_ONLY", "UNDIMENSIONED_LEG_LENGTH": "NOT_ESTABLISHED"}
    assert r["AD-4"]["HOOK_EXTENSION"] == "BLOCKED_UNQUANTIFIED" and r["AD-4"]["CODE_HOOK_VALUES"] == "QA_ONLY"
    assert set(r["AD-5"].values()) == {"SOURCE_EXPECTED_NOT_LOCATED"}
    assert set(r["AD-6"].values()) == {"ENGINEERING_DERIVED_CONCENTRATED_REACTION"}
    assert r["AD-7"]["EXACT_STRUCTURAL_BEAM_DEPTH"] == "NOT_ESTABLISHED" and r["AD-7"]["ARCHITECTURAL_LEVELS"] == "BOUND_ONLY"
    assert r["AD-8"]["RULE_0_22_LN"] == "RETAINED_WHERE_SOURCE_ESTABLISHED"
    assert r["AD-8"]["RULE_0_3_LN2"] == r["AD-8"]["RULE_0_15_L"] == "UNRESOLVED"
    assert r["AD-8"]["RATE_5PHI8_PER_M"] == "RATE_COUNT_ONLY"
    assert r["AD-9"]["CEIL_H_OVER_S_MINUS_1"] == "NOT_A_PROJECT_RULE"
    assert r["AD-9"]["SIDE_BAR_COUNT_AND_KG"] == "BLOCKED_UNQUANTIFIED"


def test_q2_analysis_is_not_promoted_and_carries_no_confidence(summary):
    doc = J(PKG / "01_AUTHORITY_DECISIONS.json")
    q = doc["q2_prior_analysis"]
    assert q["PROVENANCE"] == AD.CLAUDE_ENGINEERING_ANALYSIS and q["PROMOTED_TO"] is None
    assert q["ENGINEER_CONFIRMATION"] == "NONE" and q["CONFIDENCE_CARRIED"] is False

    def keys(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k
                yield from keys(v)
        elif isinstance(o, list):
            for v in o:
                yield from keys(v)
    for p in ("01_AUTHORITY_DECISIONS.json", "07_AD1_SUMMARY.json"):
        assert not [k for k in keys(J(PKG / p)) if "percent" in k.lower() or k.lower().startswith("confidence")
                    and k != "CONFIDENCE_CARRIED" and k != "confidence_carried"], p
    assert summary["flags"]["q2_analysis_promoted"] is False and summary["flags"]["engineer_claim_created"] is False


def test_only_the_workflow_engineer_claim_is_on_record(summary):
    pec = summary["engineer_claims_on_record"]
    assert [p["claim_id"] for p in pec] == ["PEC-CLAIM-2026-10-08-01"]
    assert pec[0]["authorises_assumptions"] is False and pec[0]["effect"].startswith("workflow only")


def test_rejected_values_are_qa_only_and_name_the_analysis_values():
    rv = rows(PKG / "02_REJECTED_ANALYSIS_VALUES.csv")
    assert all(r["ALLOWED_USE"] == "QA_ONLY" and r["PROMOTED"] == "False" and r["QUANTITY_BASIS"] == "False"
               for r in rv)
    assert all(r["PROVENANCE"] in AD.NEVER_PROMOTED for r in rv)
    text = " ".join(r["VALUE"] for r in rv)
    for v in ("12Ø", "20d", "ACI", "Ø8/15", "0.9-1.0 m", "ceil(h / s) - 1", "70Ø / 40Ø", "0.3 Ln2", "NTS"):
        assert v in text, v


# ------------------------------------------------------------------ errata by decision
def test_boxed_state_errata(errata):
    b = [e for e in errata if e["DECISION_ID"] == "AD-1"]
    c = Counter((e["FACET"], e["NEW_STATE"]) for e in b)
    assert c == {("HOOKS", "NOT_ESTABLISHED"): 20, ("MEANING_OF_3_PLUS_N", "PROJECT_PATTERN_ONLY"): 20,
                 ("EXISTENCE", "UNRESOLVED"): 4}
    assert all("no hooks" in e["OLD_STATE"] for e in b if e["FACET"] == "HOOKS")
    assert all("FN cell blank" in e["OLD_STATE"] for e in b if e["FACET"] == "EXISTENCE")


def test_cb_end_legs_lose_their_depth_derived_length(errata):
    legs = [e for e in errata if e["DECISION_ID"] == "AD-3"]
    c = Counter((e["FACET"], e["NEW_STATE"]) for e in legs)
    assert c == {("LEG_LENGTH", "NOT_ESTABLISHED"): 14, ("LEG_SHAPE", "SOURCE_EXPLICIT_SHAPE_ONLY"): 14}
    assert all("h - 2c" in e["OLD_STATE"] for e in legs if e["FACET"] == "LEG_LENGTH")


def test_every_state_erratum_carries_zero_kg(errata):
    assert errata and all(float(e["KG_EFFECT"]) == 0.0 for e in errata)
    assert all(e["RECORD_TYPE"] == AD.FACET_ERRATUM for e in errata)


def test_ground_beam_reactions_are_engineering_derived(errata, loads):
    ev = {r["GB_SPAN_ID"]: json.loads(r["EVIDENCE_KINDS"]) for r in rows(P51 / "06_CONCENTRATED_LOAD_REGISTER.csv")}
    beam = {k for k, v in ev.items() if "BEAM_END_REACTION" in v}
    re = {e["TARGET_ID"] for e in errata if e["FACET"] == "CONCENTRATED_LOAD_STATE"}
    assert re == beam and len(re) == 28
    assert all(e["PROVENANCE"] == AD.ENGINEERING_DERIVED for e in errata if e["FACET"] == "CONCENTRATED_LOAD_STATE")
    for k, r in loads.items():
        assert (r["AD6_LOAD_STATE"] == AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION) == (k in beam)


def test_loaded_candidates_rederived_from_the_length_basis(loads):
    basis = {r["GB_SPAN_ID"]: r for r in rows(P51 / "05_LENGTH_BASIS_ANALYSIS.csv")}
    for k, r in loads.items():
        if r["AD6_LOAD_STATE"] != AD.ENGINEERING_DERIVED_CONCENTRATED_REACTION or \
                r["EXTERIOR_AUTHORITY"] == "EXTERIOR_SOURCE_VERIFIED":
            assert r["AD6_CANDIDATES"] == r["FROZEN_CANDIDATES"], k
            continue
        b = basis[k]
        bases = [json.loads(b[c]) for c in ("DETAIL_BY_CLEAR_LENGTH", "DETAIL_BY_CENTRELINE_LENGTH",
                                            "DETAIL_BY_CLEAR_CONCRETE_LENGTH")]
        always = ["P13-GB-EXTERIOR"] if r["EXTERIOR_AUTHORITY"] != "INTERIOR_SOURCE_VERIFIED" else []
        assert json.loads(r["AD6_CANDIDATES"]) == AD.loaded_candidates(bases, ("P13-GB-GT5M", "P13-GB-LT5M"),
                                                                        always), k


def test_kg_retracted_exactly_on_the_two_loaded_spans(corrections, loads):
    s5 = [c for c in rows(S5 / "GROUND_SYSTEM_REBAR_COMPONENTS.csv")
          if c["occurrence_id"] in RETRACTED and c["kg"] and float(c["kg"]) > 0]
    assert {(c["occurrence_id"], c["component"]) for c in s5} == \
        {(c["OCCURRENCE_ID"], c["COMPONENT"]) for c in corrections}
    by = {(c["occurrence_id"], c["component"]): float(c["kg"]) for c in s5}
    for c in corrections:
        assert float(c["ORIGINAL_KG"]) == pytest.approx(by[(c["OCCURRENCE_ID"], c["COMPONENT"])], abs=1e-6)
        assert float(c["CORRECTION_KG"]) == pytest.approx(-float(c["ORIGINAL_KG"])) and float(c["RETAINED_KG"]) == 0
        assert c["NEW_AUTHORITY_STATE"] == "QA_ONLY" and c["NEW_RELEASE_STATE"] == "BLOCKED_UNQUANTIFIED"
        assert c["DECISION_ID"] == "AD-6" and c["PROVENANCE"] == AD.ENGINEERING_DERIVED
    for k in RETRACTED:
        assert loads[k]["EFFECT"] == "KG_RETRACTED" and loads[k]["NO_DETAIL_CASE"] == "True"
        assert AD.NO_DETAIL_IF_LOADED not in json.loads(loads[k]["FROZEN_CANDIDATES"])
    assert {k for k, r in loads.items() if r["EFFECT"] == "KG_RETRACTED"} == RETRACTED
    assert sum(float(c["ORIGINAL_KG"]) for c in corrections) == pytest.approx(47.366667, abs=1e-5)


def test_s5_1_through_support_and_link_releases_untouched(loads):
    rel = [r for r in rows(S51 / "S5_1_DELTA_COMPONENTS.csv") if r["CHANGE_KIND"] == "QUANTITY_RELEASED"]
    spans = {r["OCCURRENCE_ID"] for r in rel}
    assert not spans & RETRACTED
    for r in rel:
        if r["OCCURRENCE_ID"].startswith("SOCC-"):          # strap beams: schedule-defined, no load clause
            assert r["OCCURRENCE_ID"] not in loads
            continue
        if r["PORTION"].startswith("THROUGH_SUPPORT"):
            assert loads[r["OCCURRENCE_ID"]]["EXTERIOR_AUTHORITY"] == "EXTERIOR_SOURCE_VERIFIED"
        assert loads[r["OCCURRENCE_ID"]]["EFFECT"] == "NONE"


def test_side_bars_classified_only_from_the_middle_reinf_field(errata):
    side = [e for e in errata if e["DECISION_ID"] == "AD-9"]
    assert len(side) == 7 and all(e["NEW_STATE"] == "CLASSIFIED_SIDE_SKIN_REINFORCEMENT" for e in side)
    assert all("MIDDLE REINT." in e["EVIDENCE"] and "kg stay blocked" in e["EVIDENCE"] for e in side)
    assert {e["TARGET_ID"].split("|")[0].split("-")[2] for e in side} == {"CB1", "CB3", "CB6", "CB7", "CB8", "CB11",
                                                                          "CB12"}


def test_compliance_register_covers_every_decision(summary):
    comp = rows(PKG / "03_COMPLIANCE_REGISTER.csv")
    assert {r["DECISION_ID"] for r in comp} == {f"AD-{i}" for i in range(1, 10)}
    kg = {r["CHECK"]: float(r["KG"]) for r in comp if r["RESULT"] == "KG_ERRATUM"}
    assert kg["kg on spans whose loaded case has no project detail"] == pytest.approx(47.366667, abs=1e-5)
    assert kg["sharp-corner link path that relied on the hooks"] == pytest.approx(1399.519606, abs=1e-5)
    assert summary["compliance"]["checks"] == len(comp)


def test_conservation_and_flags(summary):
    k = summary["kg_corrections"]
    assert k["conservation_s5"]["all_pass"] and k["conservation_s5_1"]["all_pass"]
    assert k["s5_corrected_kg"] == pytest.approx(k["s5_known_kg"] - k["kg"])
    assert k["s5_1_corrected_kg_before_d1_1"] == pytest.approx(k["s5_1_known_kg_d1"] - k["kg"])
    fl = summary["flags"]
    assert fl["frozen_outputs_changed"] is False and fl["new_steel_released"] is False
    assert fl["code_value_used_for_kg"] is False and fl["pre_s7_started"] is False and fl["references_read"] == []
