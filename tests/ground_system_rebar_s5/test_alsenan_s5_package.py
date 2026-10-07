"""Alsenan S5 package (research/alsenan_ground_system_rebar_s5).

Golden members (SB1, SB3, one explicit <5 m span) are re-derived HERE from the frozen schedule / detail claims and
the frozen PRE-S5.1 bar run with kg/m = D^2/162 - never from a reference total. Everything else is checked for
invariants: population, frozen scope (31 / 28), no widening of PRE-S5.1, blocked components kept, freeze intact.
"""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_ground_system_rebar_s5"
P51 = ROOT / "research" / "pre_s5_1_source_resolution"


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


@pytest.fixture(scope="module")
def comps():
    out = defaultdict(dict)
    for r in rows(PKG / "GROUND_SYSTEM_REBAR_COMPONENTS.csv"):
        out[r["occurrence_id"]][r["component"]] = r
    return out


@pytest.fixture(scope="module")
def occs():
    return {r["occurrence_id"]: r for r in rows(PKG / "GROUND_SYSTEM_REBAR_OCCURRENCES.csv")}


@pytest.fixture(scope="module")
def summary():
    return J(PKG / "GROUND_SYSTEM_REBAR_RELEASE_SUMMARY.json")


def kg(n, d, L):
    return n * L * d * d / 162


def test_freeze_manifest_still_matches():
    m = J(PKG / "S5_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN_BEFORE_REFERENCE_COMPARISON" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)


def test_builder_is_blind():
    src = (PKG / "build_ground_system_rebar_s5.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "U-C4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze_comparison", "rebar_truth", "rough_rebar", "kg/m3", "benchmark", "donor"):
        assert bad not in src, bad


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S5_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_ground_system_rebar_s5.py")], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_population_and_frozen_scope(occs, summary):
    fam = Counter(o["family"] for o in occs.values())
    assert fam == {"GROUND_BEAM": 59, "STRAP_BEAM": 3}
    gb = Counter(o["occurrence_state"] for o in occs.values() if o["family"] == "GROUND_BEAM")
    assert gb == {"LOWER_BOUND": 31, "BLOCKED": 28}
    sb = {o["mark"]: o["occurrence_state"] for o in occs.values() if o["family"] == "STRAP_BEAM"}
    assert sb == {"SB1": "LOWER_BOUND", "SB2": "BLOCKED", "SB3": "LOWER_BOUND"}
    assert summary["final_ground_system_rebar"] == "FINAL GROUND-SYSTEM REBAR NOT ESTABLISHED"
    assert summary["headline"] == "KNOWN SOURCE-DERIVED GROUND-SYSTEM REBAR"
    for f in ("GROUND_BEAM", "STRAP_BEAM"):
        s = summary["families"][f]
        for k in ("VERIFIED_KG", "LOWER_BOUND_KNOWN_KG", "PROVISIONAL_KG", "BLOCKED_MODELLED_KG",
                  "BLOCKED_UNQUANTIFIED_COMPONENTS"):
            assert k in s
        assert s["VERIFIED_KG"] == 0 and s["PROVISIONAL_KG"] == 0 and s["BLOCKED_MODELLED_KG"] == 0


def test_never_wider_than_pre_s5_1(comps):
    matrix = defaultdict(dict)
    for r in rows(P51 / "10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv"):
        matrix[r["OCCURRENCE_ID"]][r["COMPONENT"]] = r["S5_STATUS"]
    of = {"TOP_MAIN": "TOP_MAIN", "BOTTOM_ROW_1": "BOTTOM_ROW_1", "BOTTOM_ROW_2": "BOTTOM_ROW_2",
          "BOTTOM_MAIN": "BOTTOM_ROW_1", "STIRRUP_COUNT": "STIRRUP_COUNT", "STIRRUP_DIAMETER": "STIRRUP_DIAMETER",
          "STIRRUP_SPACING": "STIRRUP_RATE"}
    for oid, cs in comps.items():
        for c, r in cs.items():
            if r["state"] in ("VERIFIED", "LOWER_BOUND"):
                assert c in of and matrix[oid][of[c]] in ("READY", "READY_LOWER_BOUND"), (oid, c)
    counts = sum(1 for cs in comps.values() for c, r in cs.items()
                 if c == "STIRRUP_COUNT" and r["state"] == "LOWER_BOUND")
    gb_counts = sum(1 for oid, cs in comps.items() if oid.startswith("GSO")
                    and cs["STIRRUP_COUNT"]["state"] == "LOWER_BOUND")
    assert (counts, gb_counts) == (28, 25)


def test_sb1_golden_and_footing_conflict_preserved(comps):
    c = comps["SOCC-1689-1B1C"]
    assert float(c["TOP_MAIN"]["kg"]) == pytest.approx(kg(13, 18, 4.55), abs=1e-5)
    assert float(c["BOTTOM_MAIN"]["kg"]) == pytest.approx(kg(7, 16, 4.55), abs=1e-5)
    assert c["STIRRUP_COUNT"]["count"] == "37" and c["STIRRUP_CORE_PATH"]["state"] == "BLOCKED_UNQUANTIFIED"
    for k in ("DEVELOPMENT_FOOTING_1", "DEVELOPMENT_FOOTING_2", "HOOK_1", "HOOK_2", "STIRRUP_HOOK_1"):
        assert c[k]["state"] == "BLOCKED_UNQUANTIFIED" and c[k]["kg"] == ""
    prov = [json.loads(line) for line in open(PKG / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", encoding="utf-8")]
    sb1 = next(p for p in prov if p["record_id"] == "SOCC-1689-1B1C:TOP_MAIN")["provenance"]
    assert any("F|F10" in f for f in sb1["OCCURRENCE_FLAGS"])


def test_sb2_conflict_and_invariant_stirrup(comps, occs):
    c = comps["SOCC-1B08-1B09"]
    assert c["TOP_MAIN"]["state"] == c["BOTTOM_MAIN"]["state"] == "BLOCKED_UNQUANTIFIED"
    assert c["STIRRUP_COUNT"]["state"] == "LOWER_BOUND" and c["STIRRUP_COUNT"]["count"] == "19"
    assert c["STIRRUP_COUNT"]["candidate_invariant"] == "True"
    assert "WIDTH CANDIDATE_CONFLICT" in c["STIRRUP_CORE_PATH"]["why"]
    o = occs["SOCC-1B08-1B09"]
    assert o["width_mm"] == "" and "SB2_SECTION_CONFLICT" in o["flags"] and "987" in o["flags"]


def test_sb3_golden(comps):
    c = comps["SOCC-1B26-1B27"]
    assert float(c["TOP_MAIN"]["kg"]) + float(c["BOTTOM_MAIN"]["kg"]) == pytest.approx(
        kg(5, 18, 2.838) + kg(5, 16, 2.838), abs=1e-5)
    assert c["STIRRUP_COUNT"]["count"] == "20"


def test_explicit_lt5m_span_golden(comps):
    c = comps["GSO-184-7CF-2"]
    for k in ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2"):
        assert float(c[k]["kg"]) == pytest.approx(kg(3, 14, 3.05), abs=1e-5)
    assert c["STIRRUP_COUNT"]["count"] == "21" and c["SIDE_REBAR"]["state"] == "NOT_APPLICABLE"


def test_exterior_depth_never_a_value(occs, comps):
    for oid, o in occs.items():
        if "P13-GB-EXTERIOR" in o["detail_ids"]:
            assert o["depth_mm"] == "" and o["depth_state"] != "SOURCE_EXPLICIT", oid
        if "ANNEX_DEPTH_SOURCE_CONFLICT" in o["flags"]:
            assert o["depth_state"] == "SOURCE_CONFLICT"
    for oid, cs in comps.items():
        if "SIDE_REBAR" in cs and cs["SIDE_REBAR"]["state"] != "NOT_APPLICABLE":
            assert cs["SIDE_REBAR"]["state"] == "BLOCKED_UNQUANTIFIED" and cs["SIDE_REBAR"]["kg"] == ""


def test_lt2_5m_candidates_inherit_no_stirrup(comps, occs):
    n = 0
    for oid, o in occs.items():
        if "P13-GB-LT2_5M" in o["detail_ids"]:
            n += 1
            assert comps[oid]["STIRRUP_COUNT"]["state"] != "LOWER_BOUND", oid
    assert n > 0


def test_concentrated_load_unknown_interior_detail_blocked(comps, occs):
    for oid, o in occs.items():
        if "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD" in o["detail_ids"]:
            assert comps[oid]["TOP_MAIN"]["state"] == "BLOCKED_UNQUANTIFIED"
            assert "Q1" in comps[oid]["TOP_MAIN"]["question_id"]


def test_boundary_end_unresolved_other_free_ends_classified(comps, occs):
    c = comps["GSO-1811-1812-1"]
    assert "unresolved" in c["DEVELOPMENT_SUPPORT_2"]["why"] and c["DEVELOPMENT_SUPPORT_2"]["question_id"] == "Q10"
    classified = [f for o in occs.values() for f in json.loads(o["flags"]) if f.startswith("FREE_END_CLASSIFIED")]
    assert len(classified) == 6


def test_development_hooks_blocked_everywhere(comps):
    for oid, cs in comps.items():
        for k, r in cs.items():
            if k.startswith(("DEVELOPMENT_", "HOOK_", "STIRRUP_HOOK_")) or k == "STIRRUP_CORE_PATH":
                assert r["state"] == "BLOCKED_UNQUANTIFIED" and r["kg"] == "", (oid, k)
    for oid, cs in comps.items():
        for k in [k for k in cs if k.startswith("DEVELOPMENT_")]:
            assert "not generalised" in cs[k]["why"]


def test_conservation_and_provenance(summary, comps):
    assert summary["conservation"]["all_pass"]
    total = sum(float(r["kg"]) for cs in comps.values() for r in cs.values() if r["kg"])
    fam = summary["families"]
    assert total == pytest.approx(fam["GROUND_BEAM"]["LOWER_BOUND_KNOWN_KG"] + fam["STRAP_BEAM"]["LOWER_BOUND_KNOWN_KG"])
    assert total == pytest.approx(summary["known_source_derived_ground_system_rebar_kg"])
    bbs = sum(float(r["net_bbs_kg"]) for r in rows(PKG / "GROUND_SYSTEM_BBS_NET.csv"))
    assert bbs == pytest.approx(total)
    prov = [json.loads(line) for line in open(PKG / "GROUND_SYSTEM_REBAR_PROVENANCE.jsonl", encoding="utf-8")]
    assert len(prov) == sum(len(cs) for cs in comps.values())
    for p in prov:
        pv = p["provenance"]
        assert pv["ELEMENT_FAMILY"] in ("GROUND_BEAM", "STRAP_BEAM")
        assert not any(k.startswith("FOOTING_") for k in pv)
        for f in ("DRAWING_SHA", "SOURCE_HANDLES", "SOURCE_TEXT", "START_NODE", "END_NODE", "GEOMETRY_HANDLES",
                  "DETAIL_ID", "DETAIL_APPLICABILITY_STATE", "RULE_ID", "CONVENTION_ID", "MEASUREMENT_STATE",
                  "AUTHORITY_STATE", "RELEASE_STATE", "FORMULA", "INPUTS", "ENGINE_COMMIT", "REGISTER_VERSION",
                  "CALCULATION_ROUND"):
            assert f in pv, (p["record_id"], f)


def test_split_views_match(occs):
    gb = rows(PKG / "GROUND_BEAM_REBAR_SUMMARY.csv")
    sb = rows(PKG / "STRAP_BEAM_REBAR_SUMMARY.csv")
    assert len(gb) == 59 and len(sb) == 3
    assert sum(float(r["known_kg"]) for r in gb + sb) == pytest.approx(sum(float(o["known_kg"]) for o in occs.values()))
