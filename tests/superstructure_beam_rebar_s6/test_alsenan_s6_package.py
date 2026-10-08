"""Alsenan S6 package (research/alsenan_superstructure_beam_rebar_s6).

Golden members are re-derived HERE from the frozen PRE-S6 registers (count, segments, D^2/162) - never from a
reference total. Everything else is checked for invariants: population, frozen scope (71 / 18, 7 / 6), no widening of
PRE-S6, blocked components kept with no kg, T/M excluded, conservation, provenance, freeze intact.
"""

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

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_superstructure_beam_rebar_s6"
P6 = ROOT / "research" / "pre_s6_superstructure_beam_readiness"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def kg(n, d, L):
    return n * L * d * d / 162


@pytest.fixture(scope="module")
def comps():
    return rows(PKG / "SUPERSTRUCTURE_BEAM_COMPONENTS.csv")


@pytest.fixture(scope="module")
def by_run(comps):
    return {c["bar_run_id"]: c for c in comps if c["bar_run_id"]}


@pytest.fixture(scope="module")
def occs():
    return {r["occurrence_id"]: r for r in rows(PKG / "SUPERSTRUCTURE_BEAM_OCCURRENCES.csv")}


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "SUPERSTRUCTURE_BEAM_RELEASE_SUMMARY.json")


@pytest.fixture(scope="module")
def prov():
    return {d["record_id"]: d for d in (json.loads(x) for x in open(PKG / "SUPERSTRUCTURE_BEAM_PROVENANCE.jsonl",
                                                                     encoding="utf-8"))}


@pytest.fixture(scope="module")
def pre06():
    return {r["BAR_RUN_ID"]: r for r in rows(P6 / "06_BEAM_BAR_RUN_READINESS.csv")}


# ----------------------------------------------------------------------------------------------------- freeze
def test_freeze_manifest_still_matches():
    m = J(PKG / "S6_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN_BEFORE_REFERENCE_COMPARISON" and m["references_read_before_freeze"] == []
    assert m["round"] == "S6" and m["baseline"] == "d39f5f6"
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)
    assert set(m["inputs"]) <= {f"research/pre_s6_superstructure_beam_readiness/{p.name}" for p in P6.iterdir()}


def test_builder_is_blind():
    src = (PKG / "build_superstructure_beam_rebar_s6.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "U-C4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze_comparison", "rebar_truth", "source_exhaustion_04", "rough_rebar", "kg/m3", "150 kg",
                "benchmark", "donor", "alsenan_rebar_v3", "alsenan_rebar_v4", ".dxf", "ezdxf", "by_sha256"):
        assert bad not in src, bad
    for line in src.splitlines():
        if line.startswith(("import ", "from ")):
            assert line.split()[1] in ("__future__", "csv", "hashlib", "io", "json", "math", "sys", "collections",
                                       "pathlib", "engine.source"), line


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S6_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_superstructure_beam_rebar_s6.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


# ------------------------------------------------------------------------------------------- population / scope
def test_population_and_frozen_scope(occs, summary):
    pop = Counter(o["subfamily"] for o in occs.values())
    assert pop == {"SIMPLE_BEAM": 89, "CONTINUOUS_BEAM": 13, "UNTAGGED_GEOMETRY": 38}
    for sub, want in (("SIMPLE_BEAM", {"LOWER_BOUND": 71, "BLOCKED": 18}),
                      ("CONTINUOUS_BEAM", {"LOWER_BOUND": 7, "BLOCKED": 6})):
        assert Counter(o["occurrence_state"] for o in occs.values() if o["subfamily"] == sub) == want
    for o in occs.values():
        if o["subfamily"] != "UNTAGGED_GEOMETRY":
            assert o["occurrence_state"] == o["pre_s6_occurrence_status"], o["occurrence_id"]
    cb_lb = sorted(o["mark"] for o in occs.values() if o["subfamily"] == "CONTINUOUS_BEAM"
                   and o["occurrence_state"] == "LOWER_BOUND")
    assert cb_lb == ["CB1", "CB11", "CB12", "CB13", "CB6", "CB7", "CB9"]
    assert summary["headline"] == "KNOWN SOURCE-DERIVED SUPERSTRUCTURE BEAM REBAR"
    assert summary["final_superstructure_beam_rebar"] == "FINAL SUPERSTRUCTURE BEAM REBAR NOT ESTABLISHED"
    for f in ("SIMPLE_BEAM", "CONTINUOUS_BEAM"):
        for k in ("VERIFIED_KG", "LOWER_BOUND_KNOWN_KG", "PROVISIONAL_KG", "BLOCKED_MODELLED_KG",
                  "BLOCKED_UNQUANTIFIED_COMPONENTS"):
            assert f"{f}_{k}" in summary
        assert summary[f"{f}_VERIFIED_KG"] == summary[f"{f}_PROVISIONAL_KG"] == \
            summary[f"{f}_BLOCKED_MODELLED_KG"] == 0
    for k in ("MID_KNOWN_KG", "STIRRUP_COUNT_KNOWN", "STIRRUP_MASS_KNOWN"):
        assert k in summary


def test_never_wider_than_pre_s6(comps, pre06):
    pre10 = {(r["OCCURRENCE_ID"], int(r["SPAN_INDEX"] or 1)): r["STATUS"]
             for r in rows(P6 / "10_SUPERSTRUCTURE_BEAM_REBAR_READINESS.csv") if r["COMPONENT_FAMILY"] ==
             "STIRRUP_COUNT"}
    rel = Counter()
    for c in comps:
        if c["state"] not in ("VERIFIED", "LOWER_BOUND"):
            continue
        rel[(c["subfamily"], c["component"])] += 1
        if c["bar_run_id"]:
            assert pre06[c["bar_run_id"]]["STATUS"] in ("READY", "READY_LOWER_BOUND"), c["record_id"]
        else:
            assert c["component"] == "STIRRUP_COUNT", c["record_id"]
            assert pre10[(c["occurrence_id"], int(c["span_index"]))] == "READY_LOWER_BOUND", c["record_id"]
    assert rel == {("SIMPLE_BEAM", "TOP_MAIN"): 71, ("SIMPLE_BEAM", "BOTTOM_MAIN"): 71,
                   ("SIMPLE_BEAM", "STIRRUP_COUNT"): 71, ("CONTINUOUS_BEAM", "BOTTOM_MAIN"): 14,
                   ("CONTINUOUS_BEAM", "MID_TOP"): 9, ("CONTINUOUS_BEAM", "STIRRUP_COUNT"): 12}
    ready = [k for k, r in pre06.items() if r["STATUS"] in ("READY", "READY_LOWER_BOUND")]
    assert sorted(ready) == sorted(c["bar_run_id"] for c in comps if c["bar_run_id"] and c["state"] == "LOWER_BOUND")


# ----------------------------------------------------------------------------------------------------- golden
def test_golden_simple_b1_from_pre_s6(by_run, comps):
    b = by_run["BM-1F_ROOF-B1-BL014-6D0:BOTTOM_MAIN"]
    t = by_run["BM-1F_ROOF-B1-BL014-6D0:TOP_MAIN"]
    assert float(b["kg"]) == pytest.approx(kg(2, 14, 1.62), abs=1e-5)
    assert float(t["kg"]) == pytest.approx(kg(2, 12, 1.62), abs=1e-5)
    s = next(c for c in comps if c["occurrence_id"] == "BM-1F_ROOF-B1-BL014-6D0" and c["component"] ==
             "STIRRUP_COUNT")
    assert int(s["count"]) == math.ceil(6 * 1.62) == 10 and s["kg"] == ""


def test_golden_cb11_bottom_and_mid(by_run):
    b = by_run["CBO-FFRS-CB11-BL024:BOTTOM:264F"]
    assert float(b["kg"]) == pytest.approx(kg(6, 18, 6.708 + 0.8 + 0.075), abs=1e-5)
    m = by_run["CBO-FFRS-CB11-BL024:SUPPORT_TOP:2666"]
    assert float(m["kg"]) == pytest.approx(kg(8, 18, 0.22 * 7.458 + 0.8 + 0.22 * 3.35), abs=1e-3)
    assert m["mid_straight_run_state"] == "SOURCE_VERIFIED" and m["complete_bar_state"] == "NOT_ESTABLISHED"
    i = by_run["CBO-FFRS-CB11-BL024:BOTTOM:2664"]           # interior span: 0.15L extension not bound
    assert float(i["kg"]) == pytest.approx(kg(4, 16, 2.65 + 0.8 + 0.6), abs=1e-5)
    assert "no bound rule" in i["missing"]


def test_cb9_reversed_cb7_invariant_cb13_different(by_run, comps):
    assert by_run["CBO-FFRS-CB9-BL023:SUPPORT_TOP:25C1"]["state"] == "LOWER_BOUND"
    assert float(by_run["CBO-FFRS-CB9-BL023:SUPPORT_TOP:25C1"]["kg"]) == pytest.approx(
        kg(4, 18, 0.22 * 4.05 + 0.5 + 0.22 * 3.9), abs=1e-3)
    for r in ("CBO-GFRS-CB7-BL003:BOTTOM:2049", "CBO-GFRS-CB7-BL003:BOTTOM:2092", "CBO-GFRS-CB7-BL003:SUPPORT_TOP:20A4",
              "CBO-FFRS-CB13-BL004:SUPPORT_TOP:24AC"):
        assert by_run[r]["state"] == "LOWER_BOUND" and by_run[r]["release_basis"] == "CANDIDATE_INVARIANT", r
    for r in ("CBO-FFRS-CB13-BL004:BOTTOM:2489", "CBO-FFRS-CB13-BL004:BOTTOM:24A8"):
        assert by_run[r]["state"] == "BLOCKED_UNQUANTIFIED" and by_run[r]["kg"] == "" and "disagree" in by_run[r]["why"]
    cb7 = [c for c in comps if c["occurrence_id"] == "CBO-GFRS-CB7-BL003" and c["component"] == "STIRRUP_COUNT"]
    assert all(c["state"] == "BLOCKED_UNQUANTIFIED" and "FROZEN PRE-S6 SCOPE" in c["why"] for c in cb7)
    s61 = rows(PKG / "S6_1_RELEASE_CANDIDATES.csv")
    assert {(r["occurrence_id"], r["span_index"]) for r in s61} == {("CBO-GFRS-CB7-BL003", "1"),
                                                                    ("CBO-GFRS-CB7-BL003", "2")}


def test_totals_equal_an_independent_sum_over_pre_s6_ready_runs(summary, pre06):
    tot = defaultdict(float)
    for r in pre06.values():
        if r["STATUS"] in ("READY", "READY_LOWER_BOUND"):
            tot[r["SUBFAMILY"]] += kg(int(r["COUNT"]), int(r["DIA_MM"]), float(r["STRAIGHT_RUN_M"]))
    assert summary["SIMPLE_BEAM_LOWER_BOUND_KNOWN_KG"] == pytest.approx(tot["SIMPLE_BEAM"], abs=1e-6)
    assert summary["CONTINUOUS_BEAM_LOWER_BOUND_KNOWN_KG"] == pytest.approx(tot["CONTINUOUS_BEAM"], abs=1e-6)
    mid = sum(kg(int(r["COUNT"]), int(r["DIA_MM"]), float(r["STRAIGHT_RUN_M"])) for r in pre06.values()
              if r["ROLE"] == "MID_SUPPORT_TOP" and r["STATUS"] == "READY")
    assert summary["MID_KNOWN_KG"] == pytest.approx(mid, abs=1e-6)
    assert summary["known_source_derived_superstructure_beam_rebar_kg"] == pytest.approx(sum(tot.values()), abs=1e-6)


# ------------------------------------------------------------------------------------- blocked / exclusions
def test_tm_tokens_are_excluded_from_steel(prov):
    tt = rows(PKG / "SUPERSTRUCTURE_BEAM_TOKEN_TERMINALS.csv")
    tm = [t for t in tt if t["field_family"] == "T/M"]
    assert len(tm) == 30 and all(t["s6_terminal"] == "EXCLUDED_DESIGN_LOAD" and t["s6_components"] == "0"
                                 for t in tm)
    assert len(tt) == 415 and not [t for t in tt if t["s6_terminal"] == ""]
    assert not [t for t in tt if t["s6_terminal"].startswith("EXCLUDED") and t["s6_components"] != "0"]
    ids = {t["token_id"] for t in tm}
    for d in prov.values():
        assert not ids & set(json.dumps(d["provenance"]["INPUTS"]).split('"'))


def test_blocked_components_kept_with_no_kg(comps, summary):
    for c in comps:
        if c["state"] in ("BLOCKED_UNQUANTIFIED", "NOT_APPLICABLE"):
            assert c["kg"] == "", c["record_id"]
    per = defaultdict(set)
    for c in comps:
        per[c["occurrence_id"]].add(c["component"])
    comps_all = {"TOP_MAIN", "BOTTOM_MAIN", "TOP_SUPPORT", "BOTTOM_SUPPORT", "MID_TOP", "MID_BOTTOM", "HANGER",
                 "SIDE_REBAR", "STIRRUP_COUNT", "STIRRUP_CORE_PATH", "HOOK_1", "HOOK_2", "DEVELOPMENT_1",
                 "DEVELOPMENT_2", "OPENING_EXTRA_TOP", "OPENING_EXTRA_BOTTOM", "OPENING_EXTRA_SIDE",
                 "OPENING_EXTRA_STIRRUP", "OTHER_EXPLICIT_EXTRA"}
    assert len(per) == 102 and all(v == comps_all for v in per.values())
    for c in comps:
        if c["component"] in ("HOOK_1", "HOOK_2", "DEVELOPMENT_1", "DEVELOPMENT_2", "STIRRUP_CORE_PATH"):
            assert c["state"] == "BLOCKED_UNQUANTIFIED"
        if c["component"].startswith("OPENING_EXTRA"):
            assert c["state"] == "NOT_APPLICABLE"
        if c["component"] == "HANGER" and c["subfamily"] == "CONTINUOUS_BEAM":
            assert c["state"] == "BLOCKED_UNQUANTIFIED"
    assert not [c for c in comps if c["state"] == "VERIFIED"]


def test_width_conflicts_stay_blocked_geometry_and_marks_unchanged(occs, comps):
    wc = {"BM-1F_ROOF-B6-BL014-6C5": "B6", "BM-GF_ROOF-B21-BL001-468": "B21", "BM-GF_ROOF-B29-BL039-465": "B29",
          "CBO-GFRS-CB2-BL038": "CB2", "CBO-FFRS-CB10-BL001": "CB10"}
    for oid, mark in wc.items():
        o = occs[oid]
        assert o["occurrence_state"] == "BLOCKED" and o["mark"] == mark and "SOURCE_CONFLICT" in o["width_match_state"]
        assert o["drawn_width_mm"] and o["schedule_width_mm"]
        sched = ("TOP_MAIN", "BOTTOM_MAIN", "STIRRUP_COUNT") + (("MID_TOP",) if mark.startswith("CB") else ())
        for c in comps:
            if c["occurrence_id"] == oid and c["component"] in sched:
                assert c["state"] == "BLOCKED_UNQUANTIFIED" and c["kg"] == ""
                assert c["question_id"] == "R2", c["record_id"]


def test_cb3_edited_and_empty_mid_cells_and_cb8_empty_mid(comps):
    cb3 = {c["bar_run_id"]: c for c in comps if c["occurrence_id"] == "CBO-GFRS-CB3-BL022" and
           c["component"] == "MID_TOP"}
    assert "EMPTY_SCHEDULE_CELL" in cb3["CBO-GFRS-CB3-BL022:SUPPORT_TOP:203E"]["why"]
    assert "asymmetric" in cb3["CBO-GFRS-CB3-BL022:SUPPORT_TOP:219C"]["why"]
    cb8 = [c for c in comps if c["occurrence_id"] == "CBO-GFRS-CB8-BL024" and c["component"] == "MID_TOP"]
    assert len(cb8) == 1 and "MID schedule cell empty" in cb8[0]["why"] and cb8[0]["kg"] == ""


def test_stirrup_counts_83_no_plus_one():
    st = rows(PKG / "SUPERSTRUCTURE_BEAM_STIRRUP_COUNTS.csv")
    rel = [s for s in st if s["state"] == "LOWER_BOUND"]
    assert len(rel) == 83 and Counter(s["subfamily"] for s in rel) == {"SIMPLE_BEAM": 71, "CONTINUOUS_BEAM": 12}
    for s in rel:
        rate = json.loads(s["RATE_OR_SPACING"])
        assert rate["mode"] == "BARS_PER_METRE"
        n = math.ceil(rate["value"] * float(s["distribution_m"]) - 1e-9)
        assert int(s["count_lower_bound"]) == n and int(s["count_convention_not_adopted"]) == n + 1
        assert s["STIRRUP_KG"] == "" and s["CORE_PATH_STATE"] == "BLOCKED_UNQUANTIFIED"
    assert len(st) == 89 + 29


def test_side_rebar_39_text_kept_kg_blocked(comps):
    side = [c for c in comps if c["component"] == "SIDE_REBAR" and c["state"] == "BLOCKED_UNQUANTIFIED"]
    assert len(side) == 39 and Counter(c["subfamily"] for c in side) == {"SIMPLE_BEAM": 32, "CONTINUOUS_BEAM": 7}
    src = {(r["ELEMENT"], r["TYPE"]): r for r in rows(P6 / "07_BEAM_SIDE_REBAR_READINESS.csv")}
    for c in side:
        s = src[(c["subfamily"], c["mark"])]
        assert c["raw_text"] == s["TOKEN_RAW"] and c["bar_count"] == s["COUNT"] and c["dia_mm"] == s["DIA_MM"]
        assert c["spacing_cm"] and c["kg"] == "" and "not source-quantified" in c["why"]
    assert Counter(c["raw_text"] for c in side) == {"2%%C12/30cm": 28, "2%%C12 | 30cm": 7, "2%%C16/20cm": 3,
                                                    "2%%C14/20cm": 1}


def test_untagged_and_object_conservation(summary):
    obj = rows(PKG / "SUPERSTRUCTURE_BEAM_OBJECT_CONSERVATION.csv")
    assert len(obj) == 286 and len({o["object_id"] for o in obj}) == 286
    t = Counter(o["s6_terminal"].split(" (")[0] for o in obj)
    assert t == {"IN_S6_OCCURRENCE": 237, "GEOMETRY_WITHOUT_TAG": 38, "NOT_REBAR_APPLICABLE": 9,
                 "OUT_OF_SCOPE_FAMILY": 2}
    tags = [o for o in obj if o["object_kind"] == "TAG"]
    assert len(tags) == 119 and all(o["s6_occurrence_id"] for o in tags)
    assert summary["untagged_geometry"] == 38
    assert all(summary["conservation"]["checks"].values())


def test_provenance_on_every_mass_component(prov):
    need = ("PROJECT_ID", "DRAWING_ID", "DRAWING_SHA", "REVISION", "ELEMENT_OCCURRENCE_ID", "ELEMENT_MARK",
            "ELEMENT_FAMILY", "ELEMENT_SUBFAMILY", "SOURCE_HANDLES", "SCHEDULE_HANDLES", "GEOMETRY_HANDLES",
            "SOURCE_TEXT", "DETAIL_ID", "RULE_ID", "CONVENTION_ID", "MEASUREMENT_STATE", "AUTHORITY_STATE",
            "RELEASE_STATE", "FORMULA", "INPUTS", "ENGINE_COMMIT", "REGISTER_VERSION", "CALCULATION_ROUND")
    n_kg = 0
    for d in prov.values():
        pv = d["provenance"]
        assert all(pv.get(k) not in (None, "") for k in need), d["record_id"]
        assert pv["CALCULATION_ROUND"] == "S6" and pv["ELEMENT_FAMILY"] == "BEAM"
        if pv["ELEMENT_SUBFAMILY"] == "CONTINUOUS_BEAM":
            assert pv["CB_GROUP_ID"] and pv["READING_DIRECTION_STATE"]
        if d["kg"] is not None:
            n_kg += 1
            assert pv["BAR_RUN_ID"] and pv["RELEASE_STATE"] == "LOWER_BOUND" and pv["LOW"] == pv["BEST"] == d["kg"]
            assert pv["COMPLETE_BAR_STATE"] == "NOT_ESTABLISHED"
    assert n_kg == 165
