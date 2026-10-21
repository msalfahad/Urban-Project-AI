"""Alsenan S3 column reinforcement (project data through the generic engine).

Checks the frozen S3 outputs against the brief: S1 frozen and consumed by hash, claims PROJECT_ONLY, 95 in = 95
terminal records, mass conservation, conflicts kept open, no verified tie or hidden hook, core runs not cut at the
soffit, and the C7 claim not leaking."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
S1 = ROOT / "research" / "alsenan_structural_census_s1"
S2 = ROOT / "research" / "alsenan_structural_s2"
S3 = ROOT / "research" / "alsenan_column_rebar_s3"
sys.path.insert(0, str(S3))

from engine.source import column_rebar as CR  # noqa: E402
from engine.source import engineering_flags as EF  # noqa: E402


def J(name):
    return json.loads((S3 / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def built():
    import build_column_rebar_s3 as A
    R, files, s = A.build()
    return {"A": A, "R": R, "files": files, "s": s}


def test_frozen_inputs_consumed_by_hash_and_unchanged():
    idx = J("INDEX.json")
    s1 = json.loads((S1 / "INDEX.json").read_text())
    for k, h in idx["s1_registers_consumed"].items():
        assert s1["registers"][k]["sha256"] == h
        assert hashlib.sha256((S1 / s1["registers"][k]["file"]).read_bytes()).hexdigest() == h
    s2 = json.loads((S2 / "INDEX.json").read_text())
    for k, h in idx["s2_outputs_consumed"].items():
        assert s2["outputs"][k] == h == hashlib.sha256((S2 / k).read_bytes()).hexdigest()
    assert idx["s1_census_modified"] is False and idx["s2_outputs_modified"] is False
    assert idx["frozen_before_benchmark"] is True and idx["benchmark_read"] is False


def test_outputs_reproduce_and_are_indexed(built):
    idx = J("INDEX.json")
    for k, v in built["files"].items():
        b = built["A"].dumps(v).encode()
        assert hashlib.sha256(b).hexdigest() == idx["outputs"][k] == hashlib.sha256((S3 / k).read_bytes()).hexdigest()


def test_s1_counts_unchanged_and_occurrence_conservation():
    occ = json.loads((S1 / "COLUMN_OCCURRENCE_REGISTER.json").read_text())["rows"]
    rr = J("COLUMN_REBAR_REGISTER.json")["rows"]
    assert len(occ) == 95 and len(rr) == 95
    assert sorted(o["column_id"] for o in occ) == sorted(r["occurrence_id"] for r in rr)
    assert Counter(r["floor"] for r in rr) == Counter(o["floor"] for o in occ)
    for r in rr:
        assert r["occurrence_state"] in ("REBAR_COMPLETE", "REBAR_LOWER_BOUND", "REBAR_PROVISIONAL",
                                         "REBAR_BLOCKED", "NOT_REQUIRED")
        for c in CR.REQUIRED_COMPONENTS:
            assert r["components"][c] in (CR.VERIFIED, CR.LOWER_BOUND, CR.PROVISIONAL, CR.BLOCKED, CR.NOT_REQUIRED)
        assert r["join_matches_census"] is True and r["schedule_join"] in ("DEFINED", "DUPLICATE_ROW")


def test_mass_conservation():
    mc = J("COLUMN_MASS_CONSERVATION.json")
    assert all(mc["checks"].values()), mc["checks"]
    rel = J("COLUMN_RELEASE_REGISTER.json")["rows"]
    tot = sum(p["kg"] for p in rel if p["kg"] is not None)
    assert abs(tot - mc["project"]["total"]) < 0.05
    assert len({p["part_id"] for p in rel}) == len(rel)
    for f, d in mc["floors"].items():
        assert abs(sum(d[k] for k in ("verified", "lower_bound", "provisional", "blocked") if k in d) - d["total"]) < 0.01


def test_claims_project_only_and_flags_lifecycle():
    c = J("ALSENAN_COLUMN_PROJECT_CLAIMS.json")
    assert {x["fact"] for x in c["claims"]} == {"TIE_RATE_SEMANTICS", "TIE_TOPOLOGY_BAND"}
    assert all(x["promotion_state"] == "PROJECT_ONLY" and x["project_id"] == "ALSENAN-ST7757" for x in c["claims"])
    ev = {e["evidence_id"]: e for e in c["project_evidence"]}
    cn = ev["ALS-S3-EV-002"]
    assert cn["agrees_with_census"] and cn["census_check"]["CN_on_axis_plan"] == 5
    assert cn["census_check"]["CN_on_foundation_plan"] == 6 and cn["census_check"]["CN_continuing_above"] == 0
    assert cn["engine_logic"] is False
    flags = {f["flag_id"]: f for f in J("COLUMN_ENGINEERING_FLAGS.json")["flags"]}
    assert flags["STR-COL-002"]["status"] == EF.RESOLVED and flags["STR-COL-008"]["status"] == EF.RESOLVED
    assert [h["to"] for h in flags["STR-COL-008"]["history"]][-1] == EF.RESOLVED
    assert flags["STR-COL-007"]["status"] == EF.SUPERSEDED
    assert EF.is_open(flags["STR-COL-009"]) and EF.is_open(flags["STR-COL-010"])      # conflicts stay open
    kinds = {f["s3_kind"] for f in flags.values() if EF.is_open(f)}
    assert {"SOURCE_CONFLICT", "TIE_ZONE_METHOD_REQUIRED", "END_LEVEL_COUNT_METHOD_REQUIRED",
            "HOOK_METHOD_REQUIRED", "LAP_METHOD_REQUIRED"} <= kinds
    for f in flags.values():
        if f["s3_kind"] in ("TIE_ZONE_METHOD_REQUIRED", "END_LEVEL_COUNT_METHOD_REQUIRED", "HOOK_METHOD_REQUIRED",
                            "LAP_METHOD_REQUIRED") and EF.is_open(f):
            q = f["s3_quantification_kg"]
            assert q["quantity_affected_kg"] is not None and q["current_kg"] is not None and f["question_for_engineer"]
            assert f["where_to_check"]
    assert (S2 / "ALSENAN_PROJECT_CLAIMS.json").read_text().count('"claims": []') == 1   # S2 store untouched


def test_tie_topology_and_rate_semantics():
    t = J("COLUMN_TIE_REGISTER.json")["rows"]
    assert Counter(x["links_per_level"] for x in t) == {1: 63, 2: 13, 3: 19}
    for x in t:
        assert x["per_metre_semantics_used"] == CR.SETS_PER_M
        assert x["links_per_m"] == 6 * x["links_per_level"]                                   # 6 / 12 / 18
        assert x["equivalent_spacing_mm"] == 1000 / 6
        assert (x["levels_rate_count"] or {}).get("links") == ((x["levels_rate_count"] or {}).get("levels", 0) *
                                                              x["links_per_level"] if x["levels_rate_count"] else None)
    c7 = [x for x in t if "C7-X07" in x["occurrence_id"]]
    assert len(c7) == 3 and all(x["band_state"] == CR.RESOLVED_BY_CLAIM and x["links_per_level"] == 3 for x in c7)


def test_claim_does_not_leak_to_another_project(built):
    R = built["R"]
    P = R["P"]
    gap_claim = next(c for c in R["claims"] if c["fact"] == "TIE_TOPOLOGY_BAND")
    other = dict(P["context"], project_id="ANOTHER-VILLA")
    sel = CR.select_band(800, P["topology_bands"], context=other, claims=R["claims"],
                         flag_keys=gap_claim["flag_keys"])
    assert sel["state"] == CR.RULE_GAP
    sel = CR.select_band(800, P["topology_bands"], context=P["context"], claims=R["claims"],
                         flag_keys=gap_claim["flag_keys"])
    assert sel["state"] == CR.RESOLVED_BY_CLAIM


def test_core_run_is_the_storey_interval_not_the_clear_height():
    lv = json.loads((S1 / "STRUCTURAL_LEVEL_REGISTER.json").read_text())
    ftf = {i["storey"]: i["floor_to_floor_m"] for i in lv["intervals"]}
    t = {x["occurrence_id"]: x for x in J("COLUMN_TIE_REGISTER.json")["rows"]}
    for m in J("COLUMN_MAIN_BAR_REGISTER.json")["rows"]:
        if m["length_kind"] == CR.CORE and m["floor"] != "FOUNDATION":
            assert m["length_per_piece_mm"] == ftf[m["floor"]] * 1000
            z = t[m["occurrence_id"]]["zones"]["CLEAR_COLUMN_ZONE"]["length_mm"]
            assert z is None or z < m["length_per_piece_mm"]
        if m["length_kind"] == CR.CORE and m["floor"] == "FOUNDATION":
            assert m["release_state"] != CR.VERIFIED                     # founding level not printed


def test_no_verified_tie_and_hooks_separate():
    rel = J("COLUMN_RELEASE_REGISTER.json")["rows"]
    for p in rel:
        if p["component"] == CR.C_TIES:
            assert p["release_state"] != CR.VERIFIED
        if p["length_kind"] in (CR.HOOK_1, CR.HOOK_2):
            assert p["release_state"] in (CR.PROVISIONAL, CR.LOWER_BOUND, CR.BLOCKED)
    g = J("COLUMN_LINK_GEOMETRY_REGISTER.json")["rows"]
    for x in g:
        assert abs(x["core_path_mm"] - 2 * (x["across_mm"] + x["along_mm"])) < 0.01   # no hook inside the core
        assert x["cover_rule_id"] and x["cover_mm"] and x["cover_source_ref"]


def test_type_conflicts_component_release():
    rel = J("COLUMN_RELEASE_REGISTER.json")["rows"]
    x04 = [p for p in rel if "X04-Y01" in p["occurrence_id"]]
    assert all(p["release_state"] == CR.LOWER_BOUND for p in x04 if p["conflict_shared"] and p["kg"])
    assert any(p["release_state"] == CR.BLOCKED and not p["conflict_shared"] for p in x04)       # GF ties differ
    x12 = [p for p in rel if "X12-Y02" in p["occurrence_id"]]
    assert all(p["likely_type"] == "C7" for p in x12)
    assert not any(p["release_state"] == CR.VERIFIED for p in x12)
    m1f = next(p for p in x12 if p["occurrence_id"].endswith("-1F") and p["length_kind"] == CR.CORE)
    assert m1f["release_state"] == CR.PROVISIONAL and m1f["candidate_type"] == "C7"
    assert set(m1f["alternatives_kg"]) == {"C7", "C8"}


def test_adapter_raises_no_flag_itself_and_reads_no_benchmark():
    src = (S3 / "build_column_rebar_s3.py").read_text(encoding="utf-8")
    assert "make_flag(" not in src
    for bad in ("44.19", "freelancer", "benchmark_total", "kg/m3", "ALRASHED", "alsenan_pricing", "Quotation"):
        assert bad not in src.replace("no kg/m3 allowance", "")
    assert not re.search(r"\b4\.5\b|\b800\b", src)                    # storey height / L value read, not written
