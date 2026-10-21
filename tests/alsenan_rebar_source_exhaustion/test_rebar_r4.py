"""ALSENAN ROUND 4 - source exhaustion + carried rebar re-audit.

1. VISUAL_SOURCE_CLAIM_V1 on synthetic claims: the state is derived from corroborations, an AI reading alone is
   never VERIFIED, a hand-edited state or a missing crop hash is rejected.
2. PROJECT_REBAR_STATUS / KNOWN_COMPONENTS BBS on synthetic populations: never procurement-ready below 100 %.
3. GATES G32-G42 (G15 / G23 strict XFAIL) and the §21 assertions on the frozen Round-4 registers.
4. MUTATIONS on copies of the frozen registers: each must trip a named check.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
LAB = ROOT / "research" / "external_engine_lab"
R4DIR = ROOT / "research" / "alsenan_rebar_source_exhaustion_04"
REGS = R4DIR / "registers"
for p in (str(LAB), str(ROOT)):
    if p not in sys.path:
        sys.path.insert(0, p)

from engine.source import rebar_model as RM  # noqa: E402
from engine.source import visual_source_claim as VS  # noqa: E402

PDF = ROOT / "data/inputs/by_sha256/74da1523f05eb3c6a4fe3ddebaef2c3d841891f003efc03bc32a3fb4553337e3.pdf"
H64 = "a" * 64


def _reg(n):
    return json.loads((REGS / f"{n}.json").read_text())


def _claims():
    return {c["claim_id"]: c for c in _reg("VISUAL_SOURCE_CLAIM_REGISTER")["claims"]}


def _pops():
    return _reg("REBAR_POPULATION_REGISTER_V4")


# =============================================================================================== 1. visual claims
def _mk(corr=(), facets=("count", "dia"), **kw):
    base = dict(claim_id="T-1", drawing_sha256=H64, drawing="X.pdf", page=13, crop_bbox=[0, 0, 10, 10], crop_hash=H64,
                raw_visual_transcription="3Ø16", normalised_interpretation={"count": 3, "dia": 16},
                discipline="STRUCTURAL", element_type="GROUND_BEAM", value=[3, 16], unit="bars", consumer="TEST",
                facets=facets, corroborations=list(corr), applicability="APPLICABLE")
    base.update(kw)
    return VS.claim(**base)


OCR = VS.corroboration("OCR_TEXT", "crop ocr", True, ["count", "dia"])
GEO = VS.corroboration("PDF_VECTOR_GEOMETRY", "dots", True, ["count"])
REV = VS.corroboration("INDEPENDENT_REVIEW", "review", True, ["count", "dia"])


def test_ai_only_claim_is_never_verified():
    c = _mk()
    assert c["source_state"] == VS.AI_VISUAL and c["quantity_authority"] == VS.PROVISIONAL_AUTHORITY
    assert VS.quantity_authority(c) == VS.PROVISIONAL_AUTHORITY


def test_one_channel_is_not_enough():
    assert _mk([OCR])["source_state"] == VS.AI_VISUAL
    assert _mk([REV])["source_state"] == VS.AI_VISUAL                      # review alone: no deterministic channel


def test_two_channels_without_deterministic_is_not_enough():
    doc = VS.corroboration("INDEPENDENT_DOCUMENT", "note", True, ["count", "dia"])
    assert _mk([REV, doc])["source_state"] == VS.AI_VISUAL


def test_cross_verified_needs_every_facet_covered():
    assert _mk([GEO, VS.corroboration("DXF_TEXT", "t", True, ["count"])])["source_state"] == VS.AI_VISUAL
    c = _mk([OCR, GEO])
    assert c["source_state"] == VS.CROSS_VERIFIED and c["quantity_authority"] == VS.VERIFIED_AUTHORITY


def test_channel_off_facet_does_not_count():
    off = VS.corroboration("DXF_GEOMETRY", "pit", True, ["unrelated"])
    assert _mk([OCR, off])["source_state"] == VS.AI_VISUAL


def test_disagreement_is_source_conflict_with_no_authority():
    bad = VS.corroboration("PDF_VECTOR_GEOMETRY", "dots", False, ["count"])
    c = _mk([OCR, REV, bad])
    assert c["source_state"] == VS.SOURCE_CONFLICT and c["quantity_authority"] == VS.NO_AUTHORITY


def test_applicability_gates_quantity_authority():
    c = _mk([OCR, GEO], applicability="APPLICABILITY_BLOCKED")
    assert c["source_state"] == VS.CROSS_VERIFIED and VS.quantity_authority(c) == VS.NO_AUTHORITY


def test_human_verification_needs_a_full_record():
    with pytest.raises(ValueError):
        _mk(human_verification={"verified_by": "QS"})
    c = _mk(human_verification={"verified_by": "QS", "date": "2026-10-05", "statement": "checked crop"})
    assert c["source_state"] == VS.HUMAN_VERIFIED


def test_mut_ai_claim_promoted_by_hand_is_rejected():
    c = _mk([OCR])
    c["source_state"], c["quantity_authority"] = VS.CROSS_VERIFIED, VS.VERIFIED_AUTHORITY
    kinds = {v[0] for v in VS.validate(c)}
    assert {"STATE_NOT_DERIVED", "AUTHORITY_NOT_DERIVED"} <= kinds


def test_mut_crop_hash_and_reference_required():
    for k, bad in (("crop_hash", None), ("crop_hash", "abc"), ("crop_bbox", None), ("page", None)):
        c = _mk([OCR, GEO])
        c[k] = bad
        assert VS.validate(c), k


def test_ocr_tolerant_glyph_and_digit_bounded():
    assert VS.ocr_count("3Ø16", "3%%c16 and 39 16 and 3016") == 2       # %%c is not a glyph; 39 16 / 3016 are
    assert VS.ocr_count("3Ø16", "13Ø16") == 0
    assert VS.ocr_count("Y10", "Y10 Y10") == 2


# =============================================================================================== 2. project status
def _pop(pid, state, ver=0.0, lb=0.0, prov=0.0):
    return {"pop_id": pid, "release_state": state, "verified_complete_kg": ver, "lower_bound_kg": lb,
            "provisional_kg": prov, "budget_kg": 0.0, "audit_kg": 0.0}


def _bbs():
    return {"total": {"net_kg": 10.0, "used_kg": 10.2, "purchased_kg": 10.5, "waste_kg": 0.3, "waste_pct": 2.9}}


def test_bbs_never_procurement_ready_below_100pct():
    pops = [_pop("A", RM.VC, ver=5.0), _pop("B", RM.LB, lb=5.0)]
    st = RM.project_status(pops, [], checks_pass=True)
    k = RM.known_components_bbs(_bbs(), st)
    assert st["PROJECT_REBAR_STATUS"] == "LOWER_BOUND_ONLY" and not st["single_total_allowed"]
    assert k["PROJECT_REBAR_PROCUREMENT_READY"] is False and k["is_project_procurement_quantity"] is False
    assert set(k) >= {"KNOWN_COMPONENTS_NET_KG", "KNOWN_COMPONENTS_BBS_USED_KG", "KNOWN_COMPONENTS_BBS_PURCHASED_KG",
                      "KNOWN_COMPONENTS_BBS_WASTE_KG"}


def test_final_only_when_everything_complete_and_clean():
    pops = [_pop("A", RM.VC, ver=5.0), _pop("B", RM.NIS)]
    assert RM.project_status(pops, [], checks_pass=True)["PROJECT_REBAR_FINAL_ESTABLISHED"] is True
    assert RM.project_status(pops, [], checks_pass=True, source_conflicts=1)["PROJECT_REBAR_FINAL_ESTABLISHED"] is False
    assert RM.project_status(pops, [], checks_pass=False)["PROJECT_REBAR_FINAL_ESTABLISHED"] is False
    comps = [{"comp_id": "A|X", "population_id": "A", "required": True, "state": RM.BLOCKED}]
    assert RM.project_status(pops, comps, checks_pass=True)["PROJECT_REBAR_FINAL_ESTABLISHED"] is False
    assert RM.project_status([_pop("A", RM.PROV, prov=1.0)], [], checks_pass=True)["PROJECT_REBAR_STATUS"] == \
        "PROVISIONAL"


def test_frozen_project_status_and_bbs_flags():
    st = _reg("PROJECT_REBAR_STATUS")
    assert st["PROJECT_REBAR_FINAL_ESTABLISHED"] is False and st["PROJECT_REBAR_PROCUREMENT_READY"] is False
    assert st["single_total_allowed"] is False and st["checks_pass"] is True and st["invariants_pass"] is True
    assert st["trade_totals"]["project_final_rebar_total"] == "NOT YET ESTABLISHED"
    k = _reg("KNOWN_COMPONENTS_BBS_REGISTER")
    assert k["PROJECT_REBAR_PROCUREMENT_READY"] is False and "NOT the villa" in k["label"]
    assert not any(re.search(r"(?<!KNOWN_COMPONENTS_)BBS_PURCHASED_KG|^NET_KG$", key) for key in k)


# =============================================================================================== 3. gates
def test_G32_ground_beam_lower_rows_not_deduplicated():
    g = _reg("GROUND_BEAM_REBAR_V4")
    assert g["q_r3_14"].startswith("RESOLVED")
    for d in g["GROUND_BEAM_DETAIL_REGISTER"]:
        assert d["lower_layer_1"][0] == 3 and d["lower_layer_2"][0] == 3
    comps = [c for c in _pops()["components"] if c["element_type"] == "GROUND_BEAM"]
    for occ in {c["occurrence_id"] for c in comps}:
        roles = {c["bar_role"]: c for c in comps if c["occurrence_id"] == occ}
        assert {"TOP", "LOWER_1", "LOWER_2"} <= set(roles), occ
        assert roles["LOWER_1"]["count"]["value"] == roles["LOWER_2"]["count"]["value"] == 3
        assert roles["LOWER_2"]["verified_kg"] + roles["LOWER_2"]["provisional_kg"] == pytest.approx(
            roles["LOWER_1"]["verified_kg"] + roles["LOWER_1"]["provisional_kg"])
    c = _claims()["P13-GB-GT5M"]
    geo = [x for x in c["corroborations"] if x["kind"] == "PDF_VECTOR_GEOMETRY"][0]
    assert c["source_state"] == VS.CROSS_VERIFIED and geo["agrees"]


def test_G33_temperature_schedule_accounted_exactly():
    c = _claims()["P15-TEMPERATURE-SCHEDULE"]
    assert c["source_state"] == VS.CROSS_VERIFIED
    t = _reg("TEMPERATURE_REBAR_RULE_REGISTER")
    assert [tuple(r) for r in t["table"]] == [(100, 10, 200), (125, 10, 200), (150, 10, 200), (175, 12, 200),
                                               (200, 12, 200), (250, 12, 200), (300, 12, 200)]
    assert t["lap_rule"].startswith("40") and "PDF:p15:TEMPERATURE_REINFORCEMENT" in \
        _reg("REBAR_ACCURACY_SCORECARD_V2")["pdf_regions_accounted"]


def test_G34_160_and_180_never_mapped_to_another_row():
    t = _reg("TEMPERATURE_REBAR_RULE_REGISTER")
    rows = {r[0] for r in t["table"]}
    for f in t["floors"]:
        assert f["thickness_mm"] in (160, 180) and f["thickness_mm"] not in rows
        assert f["state"] == "SOURCE_RULE_NOT_EXACT_MATCH" and f["exact_row"] is False
        assert f["quantity"].startswith("BLOCKED")
    temp = [p for p in _pops()["populations"] if p["element_type"] == "TEMPERATURE_REINFORCEMENT"]
    assert len(temp) == 3 and all(p["release_state"] == RM.BLK and p["lower_bound_kg"] + p["provisional_kg"] == 0
                                  for p in temp)


def test_G35_stair_read_but_blocked():
    c = _claims()["P16-STAIR-TYPICAL"]
    assert c["applicability"] == "APPLICABILITY_BLOCKED" and VS.quantity_authority(c) == VS.NO_AUTHORITY
    st = [p for p in _pops()["populations"] if p["element_type"] == "STAIR"]
    assert st and all(p["release_state"] == RM.BLK and p["lower_bound_kg"] + p["provisional_kg"] == 0 for p in st)


@pytest.mark.xfail(strict=True, reason="p.16 stair detail READ, applicability to the villa stairs not proved")
def test_G23_stair_rebar_bound_to_typical_layout():
    assert any(p["element_type"] == "STAIR" and p["release_state"] != RM.BLK for p in _pops()["populations"])


@pytest.mark.xfail(strict=True, reason="Q-S4 ground-slab scope unresolved after the second pass")
def test_G15_ground_slab_scope_resolved():
    assert _reg("GROUND_SLAB_SCOPE_REGISTER_V2")["g15"] == "PASS_CANDIDATE"


def test_G36_bbs_not_procurement_ready_in_frozen_build():
    st = _reg("PROJECT_REBAR_STATUS")
    assert st["population_completeness_pct"] < 100 and st["known_components_bbs"]["PROJECT_REBAR_PROCUREMENT_READY"] \
        is False


def test_G37_no_verified_kg_on_ai_only_claim():
    cl = _claims()
    for c in cl.values():
        if c["source_state"] == VS.AI_VISUAL:
            assert c["quantity_authority"] != VS.VERIFIED_AUTHORITY
    for comp in _pops()["components"]:
        cid = (comp["source"] or {}).get("claim_id")
        if cid and comp["verified_kg"] > 0:
            assert VS.quantity_authority(cl[cid]) == VS.VERIFIED_AUTHORITY, (comp["comp_id"], cid)
    assert _pops()["checks"]["claim_authority"]["pass"]


def test_G38_every_claim_has_crop_reference_and_hash():
    cap = json.loads((R4DIR / "evidence/VISUAL_EVIDENCE_CAPTURE.json").read_text())["crops"]
    for c in _claims().values():
        assert VS.validate(c) == [], c["claim_id"]
        assert c["crop_id"] in cap and cap[c["crop_id"]]["crop_hash"] == c["crop_hash"]


@pytest.mark.skipif(not PDF.exists(), reason="client drawing not present (kept out of git)")
def test_G38_crop_hash_reproduces_from_the_drawing():
    from engine import pdf_vector_evidence as PV
    assert hashlib.sha256(PDF.read_bytes()).hexdigest() == PDF.name[:-4]
    cap = json.loads((R4DIR / "evidence/VISUAL_EVIDENCE_CAPTURE.json").read_text())["crops"]
    for cid in ("P08_NOTE_22_COVER", "P15_TEMPERATURE_TABLE", "P13_GB_GT5M", "P14_LIFT_FOOTING"):
        e = cap[cid]
        assert PV.render_crop(PDF, e["page"], e["bbox_pt"], dpi=e["dpi"])["crop_hash"] == e["crop_hash"], cid


def test_G39_cb_nts_extensions_stay_provisional():
    n = 0
    for c in _pops()["components"]:
        if c["element_type"] != "CONTINUOUS_BEAM":
            continue
        for part in c["parts"] or []:
            if part["kind"] == "EXTENSION":
                n += 1
                assert part["state"] == "PROVISIONAL", c["comp_id"]
    assert n > 0
    assert "PROVISIONAL_NTS_GEOMETRY" in _reg("CB_OCCURRENCE_CANDIDATE_REGISTER")["nts_cutoffs"]


def test_cb_weak_match_never_auto_accepted():
    for r in _reg("CB_OCCURRENCE_CANDIDATE_REGISTER")["rows"]:
        if r["decision"] == "ACCEPTED_STRONG":
            assert not r["contradictions"]
        if r["contradictions"]:
            assert r["decision"] != "ACCEPTED_STRONG"


def test_G40_d5_candidate_never_reenters_totals():
    d5 = _reg("D5_COLUMN_SOURCE_RECONCILIATION")
    assert len(d5["rows"]) == 26
    for r in d5["rows"]:
        if r["classification"] in ("UNRESOLVED", "OFF_STOREY_COLUMN"):
            assert not r["kg_restored"] and r.get("r4_verified_kg", 0) + r.get("r4_provisional_kg", 0) == 0, \
                r["occurrence"]
    assert _pops()["checks"]["d5_no_candidate_restore"]["pass"]


def test_mut_d5_candidate_restored_is_caught():
    import alsenan_rebar_v4 as R4
    row = {"occurrence": "COLUMN:GF:C4:H4199", "classification": "UNRESOLVED", "kg_restored": False}
    pop = {"occurrence_id": row["occurrence"], "lower_bound_kg": 12.0, "verified_complete_kg": 0.0,
           "provisional_kg": 0.0}
    assert R4.check_d5_no_candidate_restore(SimpleNamespace(d5=[row], pops=[pop]))
    pop["lower_bound_kg"] = 0.0
    assert not R4.check_d5_no_candidate_restore(SimpleNamespace(d5=[row], pops=[pop]))


def test_G41_no_min_max_ground_slab_guessing():
    g = _reg("GROUND_SLAB_SCOPE_REGISTER_V2")
    assert "min -> max never used" in g["rule"]
    for f in g["footprints"]:
        assert f["decision"].startswith("UNRESOLVED")
        assert all(c["contradiction"] for c in f["candidates"])
    gs = [p for p in _pops()["populations"] if p["element_type"] == "GROUND_SLAB"]
    assert len(gs) == 2                                                    # no candidate cell became a population
    assert all(p["lower_bound_kg"] + p["verified_complete_kg"] == 0 for p in gs)   # nothing verified from a guess
    z1 = [c for c in _pops()["components"] if c["occurrence_id"] == "GROUND_SLAB:ZONE-1"]
    assert any(c["comp_id"].endswith("|SCOPE_REMAINDER") and c["state"] == RM.BLOCKED for c in z1)


def test_G42_no_carried_population_remains():
    assert _reg("CARRIED_POPULATION_REAUDIT")["carried_populations_remaining"] == 0
    assert not any(p["occurrence_id"].startswith("CARRIED:") for p in _pops()["populations"])
    assert _pops()["trade_totals"]["budget_kg"] == 0.0
    for r in _reg("CARRIED_POPULATION_REAUDIT")["rows"]:
        for k in ("old_source", "old_formula", "old_kg", "new_component_model", "new_kg", "reason"):
            assert r.get(k) not in (None, ""), (r["population"], k)


def test_boxed_stays_blocked_semantics_and_cover_rules_are_source():
    rules = {r["rule_id"]: r for r in _reg("PROJECT_REBAR_RULE_REGISTER")["rules"]}
    assert rules["COVER_GENERAL_25MM"]["value"] == 25 and rules["COVER_GENERAL_25MM"]["quantity_authority"] == "VERIFIED"
    soil = [r for r in rules.values() if r["value"] == 70 and "SOIL" in r["rule_id"]]
    assert soil and soil[0]["quantity_authority"] == "VERIFIED"
    boxed = [c for c in _pops()["components"] if "BOXED" in (c["bar_role"] or "")]
    assert any(c["state"] == RM.BLOCKED for c in boxed)
    for c in boxed:
        assert c["verified_kg"] + c["provisional_kg"] == 0, c["comp_id"]
        assert c["state"] == RM.BLOCKED or (c["state"] == "NOT_REQUIRED" and "empty" in c["why"]), c["comp_id"]


def test_note9_70d_is_starter_development_not_hooks():
    c = _claims()["P8-N09-STARTER-DEVELOPMENT"]
    assert "70" in json.dumps(c["value"]) and c["source_state"] != VS.CROSS_VERIFIED
    k = _reg("KNOWN_COMPONENTS_BBS_REGISTER")
    assert "assumption" in k["lap_rule_note"]


def test_count_method_difference_quantified():
    p = _reg("PROJECT_REBAR_RULE_REGISTER")["count_method_proposal"]
    assert p["difference_bars"] > 0 and p["difference_kg"] > 0 and "PROPOSAL" in p["id"]


def test_triage_categories_and_scorecard_separate_metrics():
    t = _reg("ENGINEERING_QUESTION_TRIAGE_REGISTER")
    cats = {"SOURCE_RESOLVABLE", "METHOD_DECISION", "STRUCTURAL_ENGINEER_REQUIRED", "OWNER_OR_MANUFACTURER_REQUIRED"}
    assert {r["category"] for r in t["rows"]} <= cats
    ids = {r["id"]: r for r in t["rows"]}
    assert ids["Q-R3-13a"]["status"] == ids["Q-R3-14"]["status"] == "RESOLVED_FROM_SOURCE"
    m = _reg("REBAR_ACCURACY_SCORECARD_V2")["metrics"]
    for k in ("source_accounting_pct", "source_interpretation_pct", "occurrence_binding_pct",
              "required_component_completeness_pct", "population_completeness_pct", "verified_kg_share_pct",
              "provisional_kg_share_pct", "blocked_population_count", "mass_conservation", "provenance",
              "human_claim_dependency_pct"):
        assert k in m
    assert "accuracy" not in " ".join(m).replace("accuracy_pct", "")


def test_slab_detail_rules_compared_not_silently_applied():
    s = _reg("SLAB_DETAIL_RULE_REGISTER")
    assert {r["rule"] for r in s["rules"]} >= {"TOP_ANCHOR_NON_CONTINUOUS"}
    assert set(s["summary"]["by_classification"]) <= {"MATCH_SOURCE", "UNDERCOUNT", "OVERCOUNT", "BLOCKED",
                                                       "UNCHANGED"}
    assert s["summary"]["r4_verified_kg"] <= s["summary"]["r3_verified_kg"]


# =============================================================================================== 4. integrity
def test_all_invariants_clean_in_frozen_build():
    for k, v in _pops()["checks"].items():
        assert v["pass"], k


def test_index_hashes_hold_and_twice_identical():
    idx = json.loads((REGS / "INDEX.json").read_text())
    assert idx["built_twice_identical"] is True and idx["frozen_before_benchmark"] is True
    for n, h in idx["files"].items():
        assert hashlib.sha256((REGS / f"{n}.json").read_bytes()).hexdigest() == h, n
    cap = (R4DIR / "evidence/VISUAL_EVIDENCE_CAPTURE.json").read_bytes()
    assert hashlib.sha256(cap).hexdigest() == idx["evidence_capture_sha256"]


def test_post_freeze_comparison_after_the_freeze():
    out = json.loads((R4DIR / "POST_FREEZE_REBAR_COMPARISON.json").read_text())
    assert out["frozen_index_sha256"] == hashlib.sha256((REGS / "INDEX.json").read_bytes()).hexdigest()
    assert out["benchmark"]["use"].startswith("FINDING_ONLY") and out["PROJECT_REBAR_FINAL_ESTABLISHED"] is False


@pytest.mark.parametrize("path", ["research/external_engine_lab/alsenan_rebar_v4.py",
                                  "research/external_engine_lab/alsenan_rebar_v4_sources.py",
                                  "research/alsenan_rebar_source_exhaustion_04/build_rebar_v4.py",
                                  "research/alsenan_rebar_source_exhaustion_04/capture_visual_evidence.py",
                                  "engine/source/visual_source_claim.py", "engine/pdf_vector_evidence.py",
                                  "engine/source/rebar_model.py"])
def test_benchmark_firewall(path):
    src = (ROOT / path).read_text()
    for banned in ("registers_v3b_eval", "BENCHMARK_EVALUATION", "44.19", "benchmark_qty", "registers_b1", ".xlsx",
                   "alsenan_v3b_evaluation", "freelancer"):
        assert banned not in src, (path, banned)


def test_mut_register_claim_state_edit_is_caught():
    c = copy.deepcopy(_claims()["P13-STARTER-FOOT-MIN30"])
    assert c["source_state"] == VS.AI_VISUAL
    c["source_state"], c["quantity_authority"] = VS.CROSS_VERIFIED, VS.VERIFIED_AUTHORITY
    assert any(v[0] == "STATE_NOT_DERIVED" for v in VS.validate(c))
    c = copy.deepcopy(_claims()["P13-GB-GT5M"])
    c["crop_hash"] = ""
    assert any(v[0] == "BAD_CROP_HASH" for v in VS.validate(c))
