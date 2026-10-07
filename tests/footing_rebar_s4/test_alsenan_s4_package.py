"""Alsenan S4 package (research/alsenan_footing_rebar_s4).

Golden examples (one simple single-layer, one elongated, one two-layer, one conflict) are checked against values
re-derived HERE from the frozen S1 schedule definition (printed count, diameter, schedule size) and the 70 mm
soil-contact cover - never against a reference total. The remaining occurrences are checked blind for
invariants only. The freeze manifest must still match: no output may change after the freeze.
"""

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

from engine.source import accurate_boq_rebar as AR
from engine.source import footing_rebar_guard as FG

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "research" / "alsenan_footing_rebar_s4"
S1 = ROOT / "research" / "alsenan_structural_census_s1"
COVER = 70.0


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows(n):
    return list(csv.DictReader(open(PKG / n, encoding="utf-8")))


@pytest.fixture(scope="module")
def comps():
    return rows("FOOTING_REBAR_COMPONENTS.csv")


@pytest.fixture(scope="module")
def defs():
    return {d["footing_type"]: d for d in J(S1 / "FOOTING_DEFINITION_REGISTER.json")["rows"]}


def c_of(comps, oid, name):
    return next(r for r in comps if r["occurrence_id"] == oid and r["component"] == name)


def explicit_kg(n, dia, span_cm):
    return n * (span_cm * 10 - 2 * COVER) / 1000 * dia * dia / 162


def test_freeze_manifest_still_matches():
    m = J(PKG / "S4_FREEZE_MANIFEST.json")
    assert m["state"] == "FROZEN_BEFORE_ANY_REFERENCE_COMPARISON" and m["references_read_before_freeze"] == []
    for group, base in (("code", ROOT), ("inputs", ROOT), ("outputs", PKG)):
        for k, h in m[group].items():
            assert hashlib.sha256((base / k).read_bytes()).hexdigest() == h, (group, k)


def test_builder_is_blind():
    src = (PKG / "build_footing_rebar_s4.py").read_text(encoding="utf-8")
    for bad in ("christiannp", "CHRISTIANNP", "UC4N", "U-C4N", "FREELANCER", "freelancer", "multi_engine",
                "post_freeze_comparison", "rebar_truth", "REBAR_REGISTER_V3", "rough_rebar", "kg/m3"):
        assert bad not in src, bad


def test_rebuild_is_byte_identical():
    before = {k: (PKG / k).read_bytes() for k in J(PKG / "S4_FREEZE_MANIFEST.json")["outputs"]}
    subprocess.run([sys.executable, "-I", str(PKG / "build_footing_rebar_s4.py")], check=True, capture_output=True,
                   cwd=ROOT)
    for k, v in before.items():
        assert (PKG / k).read_bytes() == v, k


def test_f3_authority_decision_is_recorded_and_applied(comps):
    d = J(PKG / "F3_AUTHORITY_DECISION.json")
    assert not any(d[k] for k in ("is_owner_instruction", "is_consultant_instruction", "is_project_claim",
                                  "is_source_conflict_in_project_documents"))
    occ = [r for r in rows("FOOTING_REBAR_OCCURRENCES.csv") if r["mark"] == "F3"]
    assert len(occ) == 2 and {r["occurrence_state"] for r in occ} == {"ESTABLISHED"}
    assert all("OQ-11" in r["flags"] for r in occ)
    assert {c_of(comps, r["occurrence_id"], "BOTTOM_SHORT")["state"] for r in occ} == {"VERIFIED"}


# ------------------------------------------------------------------ golden examples (source facts)
def test_golden_simple_single_layer_F(comps, defs):
    raw = defs["F"]["source_row"]["raw_attributes"]
    s, l = c_of(comps, "FOCC-1669", "BOTTOM_SHORT"), c_of(comps, "FOCC-1669", "BOTTOM_LONG")
    assert float(s["kg"]) == pytest.approx(explicit_kg(int(raw["SH-B"]), int(raw["SH-D"]), float(raw["H"])), rel=1e-6)
    assert float(l["kg"]) == pytest.approx(explicit_kg(int(raw["LO-B"]), int(raw["LO-D"]), float(raw["W"])), rel=1e-6)
    assert s["state"] == l["state"] == "VERIFIED"
    assert c_of(comps, "FOCC-1669", "BOXED")["state"] == "BLOCKED_UNQUANTIFIED"


def test_golden_elongated_F11(comps, defs):
    raw = defs["F11"]["source_row"]["raw_attributes"]            # 350 x 150: short bars span W = 150
    s, l = c_of(comps, "FOCC-1B07", "BOTTOM_SHORT"), c_of(comps, "FOCC-1B07", "BOTTOM_LONG")
    assert float(s["raw_span_mm"]) == float(raw["H"]) * 10 and float(l["raw_span_mm"]) == float(raw["W"]) * 10
    assert int(s["count"]) == int(raw["SH-B"]) and int(l["count"]) == int(raw["LO-B"])
    assert float(s["kg"]) == pytest.approx(explicit_kg(int(raw["SH-B"]), int(raw["SH-D"]), float(raw["H"])), rel=1e-6)


def test_golden_two_layer_F12(comps, defs):
    raw = defs["F12"]["source_row"]["raw_attributes"]            # per-metre rates, both layers
    L, W = float(raw["W"]) * 10, float(raw["H"]) * 10
    for name, b, d, run, dist in (("BOTTOM_SHORT", "SH-B-B", "SH-B-D", W, L), ("BOTTOM_LONG", "LO-B-B", "LO-B-D", L, W),
                                  ("TOP_SHORT", "SH-T-B", "SH-T-D", W, L), ("TOP_LONG", "LO-T-B", "LO-T-D", L, W)):
        c = c_of(comps, "FOCC-1ABF", name)
        rate, dia = int(raw[b]), int(raw[d].split("/")[0])
        n = math.ceil(rate * (dist - 2 * COVER) / 1000 - 1e-9)
        assert c["state"] == "LOWER_BOUND" and c["count_mode"] == "BARS_PER_METRE" and int(c["count"]) == n
        assert float(c["kg"]) == pytest.approx(n * (run - 2 * COVER) / 1000 * dia * dia / 162, rel=1e-6)
    assert "END_TREATMENT" in c_of(comps, "FOCC-1ABF", "TOP_SHORT")["missing"]
    assert "END_TREATMENT" not in c_of(comps, "FOCC-1ABF", "BOTTOM_SHORT")["missing"]


def test_golden_conflict_F_F10(comps):
    o = next(r for r in rows("FOOTING_REBAR_OCCURRENCES.csv") if r["occurrence_id"] == "FOCC-1B1B")
    assert o["release_state"] == FG.REBAR_BLOCKED and float(o["known_kg"]) == 0
    assert json.loads(o["candidate_marks"]) == ["F", "F10"]
    for n in ("BOTTOM_SHORT", "BOTTOM_LONG", "BOXED"):
        c = c_of(comps, "FOCC-1B1B", n)
        assert c["state"] == "BLOCKED_UNQUANTIFIED" and c["kg"] == ""


# ------------------------------------------------------------------ blind remainder: invariants only
def test_blind_remainder_invariants(comps, defs):
    occ = rows("FOOTING_REBAR_OCCURRENCES.csv")
    assert len(occ) == 26 and Counter(r["release_state"] for r in occ) == {"REBAR_LOWER_BOUND": 25,
                                                                          "REBAR_BLOCKED": 1}
    for c in comps:
        if c["state"] in ("VERIFIED", "LOWER_BOUND"):
            d = defs[c["mark"]]
            assert float(c["net_straight_mm"]) == float(c["raw_span_mm"]) - 2 * COVER
            assert float(c["raw_span_mm"]) in (d["L_cm"] * 10, d["W_cm"] * 10)
            assert float(c["kg_per_m"]) == pytest.approx(int(c["dia_mm"]) ** 2 / 162)
            assert float(c["kg"]) == pytest.approx(int(c["count"]) * float(c["bar_length_m"]) * float(c["kg_per_m"]))
            if d["element"] == "FOOTING":
                assert c["state"] == "VERIFIED" and c["count_mode"] == "EXPLICIT_COUNT"
                printed = {x["component"]: x["count"] for x in d["components"]}
                assert int(c["count"]) == printed[c["component"]]
            else:
                assert c["state"] == "LOWER_BOUND" and c["count_mode"] == "BARS_PER_METRE"
    boxed = [c for c in comps if c["component"] == "BOXED" and c["state"] == "BLOCKED_UNQUANTIFIED"]
    assert len(boxed) == 21 and all(c["kg"] == "" for c in boxed)
    assert {c["question_id"] for c in boxed if c["occurrence_id"] != "FOCC-1B1B"} == {"Q-R3-6"}
    fn = [c for c in boxed if c["mark"] == "FN"]
    assert len(fn) == 4 and all(c["raw_value"] == "" for c in fn)


def test_summary_headline_and_conservation():
    s = J(PKG / "FOOTING_REBAR_RELEASE_SUMMARY.json")
    assert s["headline"] == "KNOWN SOURCE-DERIVED FOOTING REBAR"
    assert s["final_footing_rebar"] == "FINAL FOOTING REBAR NOT ESTABLISHED"
    assert s["conservation"]["all_pass"] and all(s["conservation"]["checks"].values())
    assert "total_footing_rebar" not in json.dumps(s).lower()
    known = s["verified_kg"] + s["lower_bound_known_kg"] + s["provisional_kg"] + s["blocked_modelled_kg"]
    assert known == pytest.approx(s["conservation"]["project_known_kg"])
    assert sum(v["kg"] for v in s["diameter_distribution"].values()) == pytest.approx(known)
    bbs = sum(float(r["net_bbs_kg"]) for r in rows("FOOTING_BBS_NET.csv"))
    assert bbs == pytest.approx(known)
    assert {r["used_kg"] for r in rows("FOOTING_BBS_NET.csv")} == {""}


def test_every_part_in_the_provenance_log_validates():
    n = 0
    for line in (PKG / "FOOTING_REBAR_PROVENANCE.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        AR.validate_s4_part({"part_id": r["part_id"], "category": "FOUNDATIONS",
                             "component": r["provenance"]["COMPONENT"], "state": r["state"], "kg": r["kg"],
                             "basis": ["SCHEDULE"], "provenance": r["provenance"]})
        assert r["provenance"]["DRAWING_SHA"].startswith("9f9d1179")
        assert re.match(r"^[0-9a-f]{7}\+code:[0-9a-f]{16}$", r["provenance"]["ENGINE_COMMIT"])
        n += 1
    s = J(PKG / "FOOTING_REBAR_RELEASE_SUMMARY.json")
    assert n == s["provenance"]["parts"] == sum(v for k, v in s["components_by_state"].items()
                                               if k in AR.STATES)
