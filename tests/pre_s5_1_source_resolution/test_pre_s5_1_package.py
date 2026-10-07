"""PRE-S5.1 package (research/pre_s5_1_source_resolution).

* every output matches INDEX.json; the package rebuilds byte for byte from ST7757.dxf + P7757.dxf when present;
* the overlay covers all 59 spans; the 19 proxy-disagreement spans each get an architectural authority;
* FOLLOW ARCH: the outer ground is the sections' +-0.00; depth is bounded above only (no invented depth);
* the bar run is the support face-to-face run, never min(clear, c/c); conflicts never release;
* concentrated-load UNKNOWN never releases a 'without concentrated load' section;
* the 2.5 m stirrup is never inherited; SB2 releases only its candidate-invariant stirrups;
* free-end conservation: every pre-S5 FREE_END node is classified exactly once;
* readiness never publishes a kg; provenance is generic (no FOOTING_* on a beam); no donor token.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from engine.source import ground_system_provenance as GP

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "pre_s5_1_source_resolution"
PRE = ROOT / "research" / "pre_s5_ground_system_readiness"
ST = Path(os.environ.get("PRE_S5_ST7757_DXF") or
          ROOT / "data/inputs/by_sha256/9f9d1179a5d2a6635f9b412915a72184b7db1ff7729f4ab39a72dc3391738079.dxf")
ARCH = Path(os.environ.get("PRE_S5_P7757_DXF") or
            ROOT / "data/inputs/by_sha256/ab54dd554c31fe4a6a63ff773dc6d034159a736c7dd78158483b473a4ed31cc4.dxf")
LONG = ("TOP_MAIN", "BOTTOM_ROW_1", "BOTTOM_ROW_2")
RELEASED = ("READY", "READY_LOWER_BOUND")


def J(n, d=PKG):
    return json.loads((d / n).read_text(encoding="utf-8"))


def rows(n, d=PKG):
    return list(csv.DictReader(open(d / n, encoding="utf-8")))


def L(v):
    return json.loads(v) if v not in ("", None) else None


S = J("PRE_S5_1_SUMMARY.json")


def test_outputs_match_index():
    idx = J("INDEX.json")
    assert idx["outputs"]
    for n, h in idx["outputs"].items():
        assert hashlib.sha256((PKG / n).read_bytes()).hexdigest() == h, n
    for c, h in idx["code"].items():
        assert hashlib.sha256((ROOT / c).read_bytes()).hexdigest() == h, c
    for p, h in idx["inputs"].items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h, p


@pytest.mark.skipif(not (ST.exists() and ARCH.exists()), reason="ST7757.dxf / P7757.dxf not present")
def test_rebuild_is_byte_identical():
    idx = J("INDEX.json")
    before = {k: (PKG / k).read_bytes() for k in list(idx["outputs"]) + ["INDEX.json"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_pre_s5_1.py"), str(ST), str(ARCH)], check=True,
                   capture_output=True, cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


# ------------------------------------------------------------------------------------------------- overlay / authority
def test_overlay_covers_every_span_and_registration_is_complete():
    ov = rows("02_GROUND_BEAM_ARCH_WALL_OVERLAY.csv")
    pre = {r["OCCURRENCE_ID"] for r in rows("04_GROUND_BEAM_DETAIL_APPLICABILITY.csv", PRE)}
    assert {r["GB_SPAN_ID"] for r in ov} == pre and len(ov) == 59
    reg = S["registration"]
    assert reg["state"] == "REGISTERED" and reg["matched"] == reg["arch_outlines"] and reg["second_best"] <= 1
    for r in ov:
        assert 0.0 <= float(r["OVERLAP_PERCENT"]) <= 100.0 + 1e-6
        assert float(r["OVERLAP_LENGTH"]) <= float(r["SPAN_LENGTH_M"]) + 1e-3
        if r["WALL_CLASS"] in ("UNDER_EXTERIOR_WALL", "UNDER_INTERIOR_WALL"):
            assert L(r["ARCH_WALL_HANDLES"]), r["GB_SPAN_ID"]               # geometry, not nearest text


def test_the_19_proxy_disagreements_are_decided_by_architecture():
    ex = rows("03_EXTERIOR_AUTHORITY_REGISTER.csv")
    dis = [r for r in ex if r["PROXIES_DISAGREED"] == "True"]
    assert len(dis) == 19 == S["ambiguous_19"]["count"]
    res = [r for r in dis if r["EXTERIOR_AUTHORITY"] in ("EXTERIOR_SOURCE_VERIFIED", "INTERIOR_SOURCE_VERIFIED")]
    assert len(res) == S["ambiguous_19"]["resolved"] >= 10
    for r in ex:
        rel, a = r["ARCH_WALL_RELATION"], r["EXTERIOR_AUTHORITY"]
        if a == "EXTERIOR_SOURCE_VERIFIED":
            assert rel == "UNDER_EXTERIOR_WALL"
        if a == "INTERIOR_SOURCE_VERIFIED":
            assert rel in ("UNDER_INTERIOR_WALL", "NO_WALL_ABOVE")
        if a == "EXTERIOR_SOURCE_VERIFIED":
            assert L(r["DETAIL_CANDIDATES"]) == ["P13-GB-EXTERIOR"]


# ------------------------------------------------------------------------------------------------- FOLLOW ARCH
def test_follow_arch_depth_is_bounded_from_source_levels_only():
    fa = rows("04_FOLLOW_ARCH_DEPTH_REGISTER.csv")
    ext = {r["GB_SPAN_ID"] for r in rows("03_EXTERIOR_AUTHORITY_REGISTER.csv")
           if "P13-GB-EXTERIOR" in L(r["DETAIL_CANDIDATES"])}
    assert {r["GB_SPAN_ID"] for r in fa} == ext
    vert = {(v["id"], v["value_m"]) for v in S["vertical_evidence"]}
    assert ("VE-AA-01", 0.0) in vert and ("VE-BB-01", 0.0) in vert
    for r in fa:
        assert r["OUTCOME"] in ("BOUNDED", "UNRESOLVED")          # build-up not printed: never SOURCE_EXPLICIT
        assert r["DERIVED_DEPTH_MIN_M"] == ""                       # no lower bound is invented
        if r["OUTCOME"] == "BOUNDED":
            top, bot = float(r["TOP_LEVEL_FFL_M"]), L(r["BOTTOM_LEVEL_M"])
            assert top in (0.3, 1.0) and 0.0 in bot
            assert float(r["DERIVED_DEPTH_MAX_M"]) == pytest.approx(top - min(bot))
    side = [r for r in rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv") if r["COMPONENT"] == "SIDE_BARS"
            and "P13-GB-EXTERIOR" in L(r["REBAR_DETAIL_ID"])]
    assert side and all(r["S5_STATUS"] == "BLOCKED_COMPONENT" for r in side)


# ------------------------------------------------------------------------------------------------- bar run / basis
def test_bar_run_is_face_to_face_and_never_the_old_minimum():
    lb = rows("05_LENGTH_BASIS_ANALYSIS.csv")
    assert len(lb) == 59
    src = (PKG / "build_pre_s5_1.py").read_text(encoding="utf-8") + (PRE / "build_pre_s5.py").read_text(encoding="utf-8")
    assert "bar_run_lb_m" not in src and "min(v for v in (occ[\"clear_m\"]" not in src
    for r in lb:
        st, run = r["LENGTH_STATE"], r["BAR_STRAIGHT_RUN_LOWER_BOUND_M"]
        if st == "CONSISTENT":
            f2f = float(r["SUPPORT_FACE_TO_FACE_RUN_M"])
            assert run != "" and float(run) <= f2f + 1e-3
            if r["MEMBER_CENTERLINE_LENGTH_M"]:
                assert f2f <= float(r["MEMBER_CENTERLINE_LENGTH_M"]) + 1e-3
        else:
            assert run == "", r["GB_SPAN_ID"]                       # a conflict / unresolved run is never released
    mat = rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    for r in mat:
        if r["ELEMENT_FAMILY"] == "GROUND_BEAM" and r["COMPONENT"] in LONG and r["S5_STATUS"] in RELEASED:
            assert r["LENGTH_STATE"] == "CONSISTENT" and r["BAR_STRAIGHT_RUN_LOWER_BOUND_M"] != ""


def test_length_basis_releases_only_identical_details():
    lb = {r["GB_SPAN_ID"]: r for r in rows("05_LENGTH_BASIS_ANALYSIS.csv")}
    ex = {r["GB_SPAN_ID"]: r for r in rows("03_EXTERIOR_AUTHORITY_REGISTER.csv")}
    for k, r in lb.items():
        a, b = L(r["DETAIL_BY_CLEAR_LENGTH"]), L(r["DETAIL_BY_CENTRELINE_LENGTH"])
        assert (r["SAME_RESULT"] == "True") == (a == b and b is not None and not L(r["ON_THRESHOLD"]))
        if r["SAME_RESULT"] == "False" and ex[k]["EXTERIOR_AUTHORITY"] != "EXTERIOR_SOURCE_VERIFIED":
            assert ex[k]["PRE_S5_1_APPLICABILITY"] in ("CANDIDATE_DETAIL", "SOURCE_CONFLICT")


# ------------------------------------------------------------------------------------------------- loads / precedence
def test_concentrated_load_unknown_never_releases_a_titled_section():
    cl = {r["GB_SPAN_ID"]: r for r in rows("06_CONCENTRATED_LOAD_REGISTER.csv")}
    assert set(Counter(r["LOAD_STATE"] for r in cl.values())) <= {"NO_CONCENTRATED_LOAD_EVIDENCE", "UNKNOWN",
                                                                   "CONCENTRATED_LOAD_PRESENT", "SOURCE_CONFLICT"}
    for r in rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv"):
        if r["ELEMENT_FAMILY"] != "GROUND_BEAM" or r["COMPONENT"] not in LONG:
            continue
        cands = L(r["REBAR_DETAIL_ID"])
        if r["LOAD_STATE"] == "UNKNOWN" and cands and set(cands) <= {"P13-GB-GT5M", "P13-GB-LT5M",
                                                                      "NO_PROJECT_DETAIL_FOR_CONCENTRATED_LOAD"}:
            assert r["S5_STATUS"] not in RELEASED, r["OCCURRENCE_ID"]
    assert S["loads"]["planted_columns"] and all(p["planted_on"] != "GROUND_BEAM" for p in S["loads"]["planted_columns"])


def test_nested_conditions_preserve_both_and_never_inherit_the_stirrup():
    mat = rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    n = 0
    for r in mat:
        if r["ELEMENT_FAMILY"] == "GROUND_BEAM" and "P13-GB-LT2_5M" in (L(r["REBAR_DETAIL_ID"]) or []):
            if r["COMPONENT"] in ("STIRRUP_DIAMETER", "STIRRUP_RATE", "STIRRUP_COUNT"):
                assert r["S5_STATUS"] == "BLOCKED_COMPONENT", r["OCCURRENCE_ID"]
                n += 1
            if r["COMPONENT"] in LONG and "P13-GB-LT5M" in L(r["REBAR_DETAIL_ID"]):
                assert r["COMPONENT_VALUE"] in ("3Ø14", "") or "|" in r["COMPONENT_VALUE"]
    assert n > 0
    assert set(S["nested"]["precedence"]) == {"SPECIFICITY_CANDIDATE"}
    assert "SPECIFICITY_CANDIDATE" in (PKG / "07_DETAIL_PRECEDENCE_ANALYSIS.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------------------------- straps
def test_sb2_releases_only_candidate_invariant_stirrups():
    sb2 = {r["COMPONENT"]: r for r in rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv") if r["MARK"] == "SB2"}
    assert sb2["TOP_MAIN"]["S5_STATUS"] == sb2["BOTTOM_ROW_1"]["S5_STATUS"] == "BLOCKED_COMPONENT"
    assert sb2["TOP_MAIN"]["MAY_RELEASE"] == "False"
    for k in ("STIRRUP_DIAMETER", "STIRRUP_RATE"):
        assert sb2[k]["S5_STATUS"] == "READY" and sb2[k]["CANDIDATE_INVARIANT"] == "True" and \
            sb2[k]["MAY_RELEASE"] == "True"
    assert sb2["STIRRUP_CORE_PATH"]["S5_STATUS"] == "BLOCKED_COMPONENT"
    md = (PKG / "08_SB2_SOURCE_CONFLICT.md").read_text(encoding="utf-8")
    assert "does not adjudicate" in md and "SECTION_AUTHORITY" in md and "REBAR_AUTHORITY" in md
    for m in ("SB1", "SB3"):
        s = {r["COMPONENT"]: r for r in rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv") if r["MARK"] == m}
        assert s["TOP_MAIN"]["S5_STATUS"] == "READY_LOWER_BOUND"
        assert s["DEVELOPMENT_INTO_SUPPORT_1"]["S5_STATUS"] == "BLOCKED_COMPONENT"
        assert "BLOCKED_UNQUANTIFIED" in s["DEVELOPMENT_INTO_SUPPORT_1"]["WHY"]


# ------------------------------------------------------------------------------------------------- free ends
def test_free_end_conservation():
    pre = rows("04_GROUND_BEAM_DETAIL_APPLICABILITY.csv", PRE)
    pre_free = {(r["OCCURRENCE_ID"], e) for r in pre for e, k in (("start", "START_SUPPORT"), ("end", "END_SUPPORT"))
                if L(r[k])["kind"] == "FREE_END"}
    fe = rows("09_GROUND_BEAM_FREE_END_REGISTER.csv")
    got = [(r["GB_SPAN_ID"], r["END"]) for r in fe]
    assert len(got) == len(set(got)) and set(got) == pre_free and len(pre_free) == 7
    assert all(r["CLASSIFICATION"] in ("FOOTING", "COLUMN", "WALL_RETURN", "BOUNDARY", "ARCHITECTURAL_TERMINATION",
                                       "DRAWING_BREAK", "UNRESOLVED") for r in fe)
    lb = {r["GB_SPAN_ID"]: r for r in rows("05_LENGTH_BASIS_ANALYSIS.csv")}
    for r in fe:
        node = L(lb[r["GB_SPAN_ID"]][f"{r['END'].upper()}_NODE"])
        assert node["kind"] != "FREE_END" or r["CLASSIFICATION"] == "UNRESOLVED"


# ------------------------------------------------------------------------------------------------- readiness
def test_readiness_never_publishes_kg_and_gates_release():
    mat = rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")
    assert not [k for k in mat[0] if "KG" in k.upper()]
    for r in mat:
        if r["MAY_RELEASE"] == "True":
            assert r["S5_STATUS"] in RELEASED
            assert r["DETAIL_APPLICABILITY"] != "SOURCE_CONFLICT"
            if r["DETAIL_APPLICABILITY"] == "CANDIDATE_DETAIL":
                assert r["CANDIDATE_INVARIANT"] == "True"
    occ = {r["OCCURRENCE_ID"]: r["OCCURRENCE_S5_STATUS"] for r in mat}
    assert Counter(v for k, v in occ.items() if k.startswith("GSO-")) == Counter(S["readiness"]["ground_beams"])
    pre = {r["OCCURRENCE_ID"]: r["OCCURRENCE_S5_STATUS"] for r in rows("06_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv",
                                                                         PRE)}
    assert {r["OCCURRENCE_ID"]: r["PRE_S5_OCCURRENCE_STATUS"] for r in mat} == pre
    moved = {m["OCCURRENCE_ID"] for m in S["readiness"]["moved"]}
    assert moved == {k for k in occ if occ[k] != pre[k]}


def test_templates_are_generic_and_complete():
    t = J("S5_1_PROVENANCE_TEMPLATES.json")
    ids = {r["OCCURRENCE_ID"] for r in rows("10_GROUND_SYSTEM_REBAR_READINESS_MATRIX.csv")}
    assert {x["ELEMENT_OCCURRENCE_ID"] for x in t["templates"]} == ids
    assert all(GP.provenance_ready(x) for x in t["templates"])
    assert not any(k.startswith("FOOTING_") for x in t["templates"] for k in x)
    assert {x["ELEMENT_FAMILY"] for x in t["templates"]} == {"GROUND_BEAM", "STRAP_BEAM"}


DONOR_TOKENS = ("christiannp", "CHRISTIANNP", "S008", "freelancer", "FREELANCER", "UC4N", "U-C4N", "R9_1_CHRIS",
                "multi_engine", "benchmark_xlsx", "alsenan_demo", "Alsenan_Quotation", "alsenan_pricing")


def test_no_donor_or_benchmark_token_in_the_production_path():
    files = [PKG / "build_pre_s5_1.py", PKG / "write_docs.py", ROOT / "engine/source/ground_system_resolution.py",
             ROOT / "engine/source/rebar_provenance.py"] + [PKG / n for n in J("INDEX.json")["outputs"]]
    for f in files:
        txt = f.read_text(encoding="utf-8")
        hit = [t for t in DONOR_TOKENS if t in txt]
        assert not hit, (f.name, hit)
    for p in J("INDEX.json")["inputs"]:
        assert not any(t.lower() in p.lower() for t in ("donor", "benchmark", "christian", "r9_1"))
