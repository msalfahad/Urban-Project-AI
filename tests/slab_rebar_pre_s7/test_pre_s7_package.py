"""PRE-S7 package (research/alsenan_slab_rebar_pre_s7): elevated slab rebar readiness, no kg.

Counts and extents are re-derived here from the package's own census and the frozen S1 registers - never against a
reference total."""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import cover_authority as CA
from engine.source import slab_rebar_readiness as SR

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_slab_rebar_pre_s7"
R = ROOT / "research"
S1 = R / "alsenan_structural_census_s1"
BUILDER = "research/alsenan_slab_rebar_pre_s7/build_pre_s7.py"
FROZEN = {"S4": R / "alsenan_footing_rebar_s4" / "S4_FREEZE_MANIFEST.json",
          "S4.1": R / "alsenan_footing_rebar_s4_1" / "S4_1_FREEZE_MANIFEST.json",
          "S5": R / "alsenan_ground_system_rebar_s5" / "S5_FREEZE_MANIFEST.json",
          "S6": R / "alsenan_superstructure_beam_rebar_s6" / "S6_FREEZE_MANIFEST.json",
          "S6.1": R / "alsenan_superstructure_beam_rebar_s6_1" / "S6_1_FREEZE_MANIFEST.json",
          "S5.1": R / "alsenan_ground_system_rebar_s5_1" / "S5_1_FREEZE_MANIFEST.json",
          "AD1": R / "ad1_authority_decisions" / "AD1_FREEZE_MANIFEST.json",
          "D1.1": R / "d1_1_stirrup_authority_audit" / "D1_1_FREEZE_MANIFEST.json",
          "D1.2": R / "d1_2_footing_cover_audit" / "D1_2_FREEZE_MANIFEST.json"}
SHEETS = ("GFRS", "FFRS", "SFRS")
DECISION = {"COUNT_BASIS_UNRESOLVED", "EDGE_BAR_UNRESOLVED", "TOP_EXTENT_SOURCE_CONFLICT",
            "TOP_OVERRIDE_RULE_UNRESOLVED", "WHICH_50_PERCENT_UNRESOLVED", "CONTINUOUS_BAR_SPEC_MISMATCH",
            "TABLE_NO_EXACT_ROW", "TEMPERATURE_REGION_DEPENDS_ON_TOP_EXTENT", "COUNT_NOTATION_AMBIGUOUS_NO_PER_METRE"}


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(name):
    with open(PKG / name, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def js(v):
    return json.loads(v) if v not in ("", None) else None


def f(v):
    return float(v) if v not in ("", None) else None


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "PRE_S7_SUMMARY.json")


@pytest.fixture(scope="module")
def census():
    return rows("01_SLAB_PANEL_CENSUS.csv")


@pytest.fixture(scope="module")
def comps():
    return rows("04_COMPONENT_READINESS.csv")


@pytest.fixture(scope="module")
def supports():
    return rows("05_SUPPORT_REGISTER.csv")


@pytest.fixture(scope="module")
def tokens():
    return rows("03_SLAB_REBAR_TOKENS.csv")


@pytest.fixture(scope="module")
def s1_panels():
    return [r for r in J(S1 / "SLAB_PANEL_REGISTER.json")["rows"] if r["sheet"] in SHEETS]


# ------------------------------------------------------------------ package / freeze
def test_deliverables_exist():
    for n in ("00_README.md", "01_SLAB_PANEL_CENSUS.csv", "02_THICKNESS_REGISTER.csv", "03_SLAB_REBAR_TOKENS.csv",
              "04_COMPONENT_READINESS.csv", "05_SUPPORT_REGISTER.csv", "06_SUPPORT_RULES.csv",
              "07_BAR_RUN_REGISTER.csv", "08_OPENING_REGISTER.csv", "09_TEMPERATURE_REBAR_REGISTER.csv",
              "10_COUNT_RULE_REGISTER.csv", "11_SOURCE_CONFLICTS.csv", "12_SOURCE_EXPECTED_NOT_LOCATED.csv",
              "13_PROVENANCE.jsonl", "14_S7_RELEASE_CANDIDATES.csv", "15_ENGINEER_QUESTIONS.csv",
              "PRE_S7_SUMMARY.json", "TEST_RUN.md", "PRE_S7_FREEZE_MANIFEST.json",
              "source_search_inputs/PRE_S7_VISUAL_READING.json"):
        assert (PKG / n).is_file(), n


def test_freeze_manifest_still_matches():
    m = J(PKG / "PRE_S7_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN" and m["round"] == "PRE-S7" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        assert m[group]
        for k, h in m[group].items():
            assert sha(base / k) == h, (group, k)
    assert BUILDER in m["code"] and "engine/source/slab_rebar_readiness.py" in m["code"]


def test_frozen_stages_are_immutable(summary):
    man = J(PKG / "PRE_S7_FREEZE_MANIFEST.json")
    for name, p in FROZEN.items():
        m = J(p)
        for group, b in (("code", ROOT), ("inputs", ROOT), ("outputs", p.parent)):
            for k, h in m.get(group, {}).items():
                assert sha(b / k) == h, (name, group, k)
        assert summary["frozen"][name]["manifest_sha256"] == sha(p) == man["frozen_baselines"][name], name
    idx = J(S1 / "INDEX.json")["registers"]
    for n in ("SLAB_PANEL_REGISTER", "SLAB_REBAR_SOURCE_REGISTER", "SLAB_RULE_APPLICATION_MAP",
              "STRUCTURAL_PROJECT_RULE_REGISTER", "BEAM_OCCURRENCE_REGISTER"):
        assert sha(S1 / f"{n}.json") == idx[n]["sha256"], n


def test_rebuild_is_byte_identical():
    man = J(PKG / "PRE_S7_FREEZE_MANIFEST.json")
    before = {k: (PKG / k).read_bytes() for k in man["outputs"]}
    before["PRE_S7_FREEZE_MANIFEST.json"] = (PKG / "PRE_S7_FREEZE_MANIFEST.json").read_bytes()
    subprocess.run([sys.executable, "-I", str(ROOT / BUILDER)], check=True, capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_builder_is_blind_and_registered():
    src = (ROOT / BUILDER).read_text(encoding="utf-8")
    for bad in ("christiannp", "UC4N", "U-C4N", "freelancer", "FREELANCER", "Chris", "post_freeze", "multi_engine",
                "rebar_truth", "rough_rebar", "fitz", "pymupdf", "pdf_vector_evidence", "kg/m", "BS 8666",
                "Eurocode", "EN 1992"):
        assert bad not in src, bad
    assert not re.search(r"\bACI\b", src)
    sys.path.insert(0, str(ROOT / "tests" / "structural_comparison_engine"))
    import rebar_product_registry as RP
    assert BUILDER in RP.ACCURATE_BUILDERS
    assert "engine/source/slab_rebar_readiness.py" in RP.ACCURATE_MODULES


# ------------------------------------------------------------------ population
def test_every_slab_geometry_terminates_once(census, s1_panels):
    ids = [c["SLAB_PANEL_ID"] for c in census]
    assert len(ids) == len(set(ids))
    faces = {r["panel_id"] for r in s1_panels}
    assert faces <= set(ids)                                         # every S1 face of the three slab sheets
    extra = set(ids) - faces
    assert all(i.startswith("HZ-") for i in extra) and len(extra) == 8     # the dense-hatch strips
    assert all(c["SCOPE"] in SR.SCOPES for c in census)
    assert not any(c["FLOOR"] == "GROUND_SLAB_SOG" for c in census)          # slab on grade is out of scope


def test_scope_population(census, summary):
    k = Counter((c["S1_CLASS"], c["SCOPE"]) for c in census)
    assert k[("SLAB_PANEL", SR.IN_SCOPE)] == 47 and summary["panels_in_scope"] == 47
    assert k[("DOME_ZONE", SR.EXCLUDED_SPECIAL)] == 8
    assert k[("STAIR_FLIGHT_ZONE", SR.EXCLUDED_SPECIAL)] == 3
    assert k[("STAIR_IN_VOID_ZONE", SR.CLASSIFICATION_BLOCKED)] == 1
    assert k[("OPEN_TO_BELOW", SR.VOID_OR_OPENING)] == 3 and k[("OUTSIDE_BUILDING_OR_COURT", SR.NOT_SLAB)] == 4
    tank = [c for c in census if c["PANEL_CLASS"] == "WATER_TANK_PLACE_SLAB"]
    assert {c["SLAB_PANEL_ID"] for c in tank} == {"SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02"}
    assert all(c["SCOPE"] == SR.CLASSIFICATION_BLOCKED for c in tank)
    area = sum(f(c["GEOMETRIC_AREA_M2"]) for c in census if c["SCOPE"] == SR.IN_SCOPE)
    assert abs(area - summary["slab_area_in_scope_m2"]) < 1e-6
    sunk = [c for c in census if c["PANEL_CLASS"] == "SUNKEN_SLAB"]
    assert len(sunk) == 6 and all(c["SCOPE"] == SR.IN_SCOPE for c in sunk)


def test_gf_void_with_t16_tag_is_a_source_conflict(census, tokens):
    c = [x for x in census if x["SLAB_PANEL_ID"] == "SP-GF_ROOF_SLAB-21"][0]
    assert c["SCOPE"] == SR.CLASSIFICATION_BLOCKED and c["CONFLICT"] == SR.SOURCE_CONFLICT
    conf = [x for x in rows("11_SOURCE_CONFLICTS.csv") if x["KIND"] == "PANEL_VOID_CONFLICT"][0]
    ev = js(conf["EVIDENCE"])
    assert ev["state"] == SR.SOURCE_CONFLICT and ev["void_marks"] and ev["slab_marks"]
    assert set(js(conf["CANDIDATES"])) == {"SLAB", "VOID", "OPENING_EXTRA", "MISBOUND_TEXT"}
    t = [x for x in tokens if x["TOKEN_ID"] == "5BC"][0]                 # the 8Ø16/m bar inside the void face
    assert t["TERMINAL_STATE"] == SR.SOURCE_CONFLICT and not js(t["BAR_FAMILIES"])


def test_special_structures_never_reach_s7(census, comps, tokens):
    excluded = {c["SLAB_PANEL_ID"] for c in census if c["SCOPE"] != SR.IN_SCOPE}
    assert not [c for c in comps if c["OWNER"] in excluded and c["READINESS"] == SR.S7_RELEASE_CANDIDATE]
    assert not [c for c in comps if c["SCOPE"] == SR.EXCLUDED_SPECIAL]
    for t in tokens:
        if t["TERMINAL_STATE"] == SR.EXCLUDED_SPECIAL_TOKEN:
            assert not js(t["BAR_FAMILIES"])
    cands = rows("14_S7_RELEASE_CANDIDATES.csv")
    assert not [c for c in cands if c["OWNER"] in excluded]


# ------------------------------------------------------------------ thickness / temperature / cover
def test_thickness_precedence(summary):
    th = {r["SLAB_PANEL_ID"]: r for r in rows("02_THICKNESS_REGISTER.csv")}
    for pid in ("SP-2F_ROOF_SLAB-01", "SP-2F_ROOF_SLAB-02"):
        assert th[pid]["AUTHORITY"] == SR.LOCAL_PANEL and f(th[pid]["EFFECTIVE_THICKNESS_MM"]) == 180
        assert js(th[pid]["OVERRIDDEN"]) and "R4" in th[pid]["PRIOR_REGISTER_NOTE"]
    for pid in summary["local_marks_confirming_default"]:
        assert f(th[pid]["EFFECTIVE_THICKNESS_MM"]) == 160 and js(th[pid]["CONFIRMS"]) == [SR.PROJECT_DEFAULT]
    ins = [r for r in th.values() if r["SCOPE"] == SR.IN_SCOPE]
    assert all(r["STATE"] == "RESOLVED" and f(r["EFFECTIVE_THICKNESS_MM"]) == 160 for r in ins)
    assert summary["thickness_distribution"] == {"160 mm (PROJECT_DEFAULT)": 44, "160 mm (LOCAL_PANEL)": 3}
    assert all(r["FLOOR_RULE"] == "NONE_FOUND" for r in th.values())
    assert not [r for r in th.values() if r["SCOPE"] == SR.EXCLUDED_SPECIAL and r["EFFECTIVE_THICKNESS_MM"]]


def test_temperature_table_has_no_160_or_180_row():
    rule = [r for r in J(S1 / "STRUCTURAL_PROJECT_RULE_REGISTER.json")["rows"] if r["rule_id"] == "P15-TEMP-TABLE"][0]
    table = {int(k): v for k, v in rule["values"]["rows"].items()}
    assert 160 not in table and 180 not in table
    for r in rows("09_TEMPERATURE_REBAR_REGISTER.csv"):
        t = f(r["THICKNESS_MM"])
        assert SR.temperature_row(t, table)["state"] == r["TABLE_STATE"] == SR.TABLE_NO_EXACT_ROW
        assert r["TABLE_VALUE"] == "" and r["INTERPOLATED"] == "False"
    assert all("TABLE_NO_EXACT_ROW" in js(c["BLOCKERS"]) for c in rows("04_COMPONENT_READINESS.csv")
               if c["COMPONENT"].startswith("TEMPERATURE"))


def test_cover_is_a_minimum_and_no_length_is_exact(summary, comps):
    assert summary["cover_basis"]["basis"] == CA.MINIMUM_PROJECT_COVER
    assert summary["cover_basis"]["label"] == "MINIMUM_PROJECT_COVER_25"
    assert {c["COVER_BASIS"] for c in comps if c["COVER_BASIS"]} == {"MINIMUM_PROJECT_COVER_25"}
    assert not [c for c in comps if c["LENGTH_STATE"] in (SR.EXACT_PROJECT_LENGTH, SR.LOWER_BOUND)]


# ------------------------------------------------------------------ rules
def test_support_rules_gates():
    rr = {r["RULE_ID"]: r for r in rows("06_SUPPORT_RULES.csv")}
    for rid in ("P15-TOP-NONCONT-0.25L1", "P15-TOP-CONT-0.30Lmax", "P15-BOT-STOP-0.125L"):
        r = rr[rid]
        assert r["SPAN_DEFINITION"] == SR.CLEAR_SPAN and r["MEASUREMENT_ORIGIN"] == SR.FACE_OF_SUPPORT
        assert r["GATE"] == SR.RELEASABLE and r["STATE"] == "PROVEN_PROJECT_RULE"
    assert rr["P15-BOT-STOP-0.125L"]["WHICH_50_PERCENT"] == "NOT_STATED"
    note2 = rr["P4-6-NOTE-2-TOP-OVER-BEAMS"]
    assert note2["SPAN_DEFINITION"] == SR.L_UNDEFINED and note2["GATE"] == SR.RULE_BLOCKED
    assert "ثلث البحر" in note2["WORDING"] and "5Ø10/m" in note2["WORDING"]
    assert rr["P15-TOP-EXTEND-50PCT"]["STATE"] == "RECORDED_NOT_RELEASABLE"
    kinds = {r["KIND"] for r in rows("11_SOURCE_CONFLICTS.csv")}
    assert "UNSUPPORTED_SUPPORT_RULE_APPLICABILITY" in kinds


def test_support_extents_rederived(census, supports):
    cs = {c["SLAB_PANEL_ID"]: c for c in census}

    def L(pid, ori):
        c = cs[pid]
        return f(c["CLEAR_SPAN_X_MM"] if ori == "V" else c["CLEAR_SPAN_Y_MM"])
    n = 0
    for s in supports:
        if s["EXTENT_STATE"] != "CANDIDATE_ONLY_SOURCE_CONFLICT":
            assert s["EXTENT_LEFT_MM"] == s["EXTENT_RIGHT_MM"] == ""
            continue
        n += 1
        sides = [p for p in (s["LEFT_PANEL"], s["RIGHT_PANEL"]) if p and cs.get(p, {}).get("SCOPE") in
                 (SR.IN_SCOPE, SR.CLASSIFICATION_BLOCKED)]
        if s["SUPPORT_TYPE"] == SR.CONTINUOUS:
            v = 0.30 * max(L(p, s["ORIENTATION"]) for p in sides)
            assert abs(f(s["EXTENT_LEFT_MM"]) - v) < 0.1 and abs(f(s["EXTENT_RIGHT_MM"]) - v) < 0.1
        else:
            assert s["SUPPORT_TYPE"] == SR.NON_CONTINUOUS and len(sides) == 1
            v = 0.25 * L(sides[0], s["ORIENTATION"])
            got = f(s["EXTENT_LEFT_MM"]) if s["EXTENT_LEFT_MM"] else f(s["EXTENT_RIGHT_MM"])
            assert abs(got - v) < 0.1
        assert s["RULE_CONFLICT"]                                        # never released: note 2 disagrees
    assert n > 0


# ------------------------------------------------------------------ supports, tokens, runs
def test_supports_terminate_and_are_counted_once(supports, comps):
    views = Counter(v for s in supports for v in js(s["VIEWS"]))
    assert all(k == 1 for k in views.values())
    assert len({s["SUPPORT_ID"] for s in supports}) == len(supports)
    assert all(s["SUPPORT_TYPE"] in SR.SUPPORT_TYPES for s in supports)
    tops = Counter(c["OWNER"] for c in comps if c["COMPONENT"].startswith("TOP_SUPPORT"))
    beam = {s["SUPPORT_ID"] for s in supports if s["SUPPORT_KIND"] == "BEAM"}
    assert set(tops) == beam and all(v == 1 for v in tops.values())   # once per support, not per panel
    assert all(s["OWNERSHIP"].startswith("SUPPORT") for s in supports)


def test_token_conservation(tokens):
    recs = [{"token_id": t["TOKEN_ID"], "state": t["TERMINAL_STATE"], "bar_families": js(t["BAR_FAMILIES"]) or []}
            for t in tokens]
    cons = SR.token_conservation([t["TOKEN_ID"] for t in tokens], recs)
    assert cons["all_pass"]
    s1 = [t for t in J(S1 / "SLAB_REBAR_SOURCE_REGISTER.json")["rows"] if t["sheet"] in SHEETS]
    assert {t["source_row_id"] for t in s1} <= {t["S1_SOURCE_ROW"] for t in tokens if t["S1_SOURCE_ROW"]}
    k = Counter(t["TERMINAL_STATE"] for t in tokens)
    assert set(k) <= set(SR.TOKEN_STATES) and k[SR.UNBOUND] == 0
    assert k[SR.DESIGN_NOTE] == 3                                       # plan note 2 on each slab sheet
    q = [t for t in tokens if t["KIND"] == "QUALIFIER"]
    assert len(q) == 4 and all(t["TERMINAL_STATE"] == SR.BOUND_TO_PANEL and not js(t["BAR_FAMILIES"]) for t in q)
    top = {t["TOKEN_ID"]: t["TERMINAL_STATE"] for t in tokens if t["KIND"] == "SUPPORT_TOP_BAR"}
    assert top == {"1824": SR.BOUND_TO_SUPPORT, "79F": SR.SOURCE_CONFLICT, "7A2": SR.SOURCE_CONFLICT}


def test_bar_runs_count_each_bar_once(comps, census):
    runs = rows("07_BAR_RUN_REGISTER.csv")
    bottom = [r for r in runs if r["KIND"].startswith("BOTTOM")]
    fams = Counter((p, r["DIRECTION"]) for r in bottom for p in js(r["PANELS_CROSSED"]))
    assert all(v == 1 for v in fams.values())                           # a family is in exactly one run
    ins = {c["SLAB_PANEL_ID"] for c in census if c["SCOPE"] == SR.IN_SCOPE}
    assert {p for p, _ in fams} <= ins
    cs = {c["SLAB_PANEL_ID"]: c for c in census}
    sup = {s["SUPPORT_ID"]: s for s in rows("05_SUPPORT_REGISTER.csv")}
    for r in bottom:
        for sid in js(r["SUPPORTS_CROSSED"]):
            assert sup[sid]["SUPPORT_TYPE"] == SR.CONTINUOUS
        if r["KNOWN_STRAIGHT_EXTENT_MM"]:
            bbs = [js(cs[p]["BBOX_MM"]) for p in js(r["PANELS_CROSSED"])]
            i0, i1 = (0, 2) if r["DIRECTION"] == "X" else (1, 3)
            assert abs(f(r["KNOWN_STRAIGHT_EXTENT_MM"]) - (max(b[i1] for b in bbs) - min(b[i0] for b in bbs))) <= 1
            assert r["ALIGNMENT"] == "FULL_CHAIN"
    cont = [c for c in comps if c["COMPONENT"] == "CONTINUOUS_BAR_RUN"]
    assert all(c["OWNER"] == c["BAR_RUN_ID"] for c in cont)             # the run owns the continuous half
    assert all(r["COUNTED_ONCE"] == "True" for r in runs)


# ------------------------------------------------------------------ components / counts / candidates
def test_no_kg_anywhere(comps, summary):
    assert all(c["KG"] == "" for c in comps)
    assert all(c["KG"] == "" for c in rows("14_S7_RELEASE_CANDIDATES.csv"))
    assert summary["no_kg"] is True and summary["flags"]["kg_calculated"] is False
    assert summary["flags"]["s7_started"] is False and summary["flags"]["interpolated_temperature"] is False


def test_readiness_states(comps, summary):
    assert all(c["READINESS"] in (SR.S7_RELEASE_CANDIDATE, SR.BLOCKED_FROM_S7) for c in comps)
    for c in comps:
        b = js(c["BLOCKERS"])
        assert (c["READINESS"] == SR.S7_RELEASE_CANDIDATE) == (not b)
        assert (c["DECISION_ONLY"] == "True") == (bool(b) and set(b) <= DECISION)
    cands = rows("14_S7_RELEASE_CANDIDATES.csv")
    by = {c["COMPONENT_ID"]: c for c in comps}
    for c in cands:
        assert c["STATE"] in ("S7_RELEASE_CANDIDATE", "CONDITIONAL_ON_OWNER_DECISIONS")
        assert by[c["COMPONENT_ID"]]["DECISION_ONLY"] == "True" or c["STATE"] == "S7_RELEASE_CANDIDATE"
    assert summary["s7_release_candidates"] == sum(c["STATE"] == "S7_RELEASE_CANDIDATE" for c in cands)
    assert summary["conditional_candidates"] == sum(c["STATE"] == "CONDITIONAL_ON_OWNER_DECISIONS" for c in cands)
    rate = [c for c in comps if c["COUNT_MODE"] == "BARS_PER_METRE"]
    assert rate and all("COUNT_BASIS_UNRESOLVED" in js(c["BLOCKERS"]) for c in rate)


def test_only_project_supported_component_types(summary, comps):
    inst = summary["component_type_instantiation"]
    assert set(inst) == set(SR.COMPONENT_TYPES)
    for t in ("MID_STRIP_TOP", "COLUMN_STRIP_TOP", "OPENING_TRIM", "OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM",
              "EDGE_BAR", "HOOK", "DEVELOPMENT"):
        assert inst[t]["state"] == "NOT_INSTANTIATED" and inst[t]["why"], t
    assert set(Counter(c["COMPONENT"] for c in comps)) == {t for t, v in inst.items() if v["state"] == "INSTANTIATED"}
    assert all(c["PROJECT_SUPPORT"] for c in comps)


def test_count_rules_keep_rate_width_and_rule_apart():
    for r in rows("10_COUNT_RULE_REGISTER.csv"):
        if r["COUNT_MODE"] == "BARS_PER_METRE":
            assert r["COUNT_RULE"] == "UNRESOLVED" and r["STATE"] == SR.COUNT_BASIS_UNRESOLVED
            assert r["EDGE_BAR"] == SR.EDGE_BAR_UNRESOLVED and r["PRINTED_COUNT"] == ""
            if r["DISTRIBUTION_WIDTH_MM"]:
                w, s = f(r["DISTRIBUTION_WIDTH_MM"]), 1000.0 / f(r["RATE_PER_M"])
                assert abs(f(r["SPACING_MM"]) - s) <= 5e-4                  # printed to 3 dp
                assert js(r["CANDIDATES"]) == {"CEIL": math.ceil(w / s - 1e-9),
                                               "CEIL_PLUS_1": math.ceil(w / s - 1e-9) + 1,
                                               "FLOOR_PLUS_1": math.floor(w / s + 1e-9) + 1}
        else:
            assert r["STATE"] == SR.COUNT_EXPLICIT and r["PRINTED_COUNT"]


def test_openings(census):
    ops = rows("08_OPENING_REGISTER.csv")
    handles = Counter(h for o in ops if o["GEOMETRY"].count("S-OPENING lines") for part in o["GEOMETRY"].split(";")
                      for h in part.split("lines ")[-1].split(","))
    assert all(v == 1 for v in handles.values())                       # each opening line in one row
    voids = {c["SLAB_PANEL_ID"] for c in census if c["SCOPE"] == SR.VOID_OR_OPENING}
    face_rows = {o["OPENING_ID"][3:] for o in ops if o["TYPE"] in ("OPEN_TO_BELOW_FACE",
                                                                    "VOID_WITH_STAIR_AND_SLAB_EVIDENCE")}
    assert voids | {"SP-GF_ROOF_SLAB-21"} == face_rows
    for o in ops:
        if o["TYPE"] == "OPEN_TO_BELOW_FACE":
            assert o["REBAR_DEDUCTION_RULE"].startswith("NONE_REQUIRED") and o["STATE"] == "VOID"
    assert not [o for o in ops if o["STATE"] == "UNRESOLVED" and o["TYPE"] != "OPENING_STRIP"]


# ------------------------------------------------------------------ registers / gates / provenance
def test_conflicts_senl_questions(summary):
    c = rows("11_SOURCE_CONFLICTS.csv")
    s = rows("12_SOURCE_EXPECTED_NOT_LOCATED.csv")
    q = rows("15_ENGINEER_QUESTIONS.csv")
    assert len({x["CONFLICT_ID"] for x in c}) == len(c) == summary["source_conflicts"]
    assert len({x["SENL_ID"] for x in s}) == len(s) == summary["senl"]
    assert len({x["QUESTION_ID"] for x in q}) == len(q) == summary["questions"]
    assert {"TEMPERATURE_ROW_160_180", "COUNT_RULE", "SLAB_SCHEDULE"} <= {x["TOPIC"] for x in s}
    assert {"Q-COUNT", "Q-TOPEXT", "Q-TEMP", "Q-GFVOID", "Q-TANK", "Q-LAYER"} <= {x["QUESTION_ID"] for x in q}
    assert not [x for x in c if x["STATE"] == SR.SOURCE_CONFLICT and not x["RESOLUTION"].startswith("NONE")]


def test_conservation_gates_and_provenance(summary, census, comps, supports, tokens):
    assert summary["gates"] and all(summary["gates"].values())
    lines = [json.loads(x) for x in (PKG / "13_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines()]
    k = Counter(x["kind"] for x in lines)
    assert k["PANEL"] == len(census) and k["COMPONENT"] == len(comps) and k["SUPPORT"] == len(supports)
    assert k["TOKEN"] == len(tokens) and k["BAR_RUN"] == len(rows("07_BAR_RUN_REGISTER.csv"))
    assert summary["round"] == "PRE-S7" and summary["baseline_head"] == "44f693e"
    assert summary["flags"]["references_read"] == [] and summary["flags"]["donor_or_code_used"] is False
