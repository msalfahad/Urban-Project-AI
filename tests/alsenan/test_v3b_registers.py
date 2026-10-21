"""V3b frozen registers (built twice from the recorded commit, byte-identical) - invariants of the two-layer release,
waste, rebar bases, supersession, blinding, freeze order and the Qortuba shadow."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from engine.source import release_model as RM

R = Path(__file__).parent / "registers_v3b"
E = Path(__file__).parent / "registers_v3b_eval"


def jl(name, d=R):
    return json.loads((d / f"{name}.json").read_text())


@pytest.fixture(scope="module")
def boq():
    return jl("BOQ_LINES_V3B")["lines"]


def _digest(o):
    return hashlib.sha256(json.dumps(o, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def test_freeze_digests_match_the_frozen_registers():
    fz = jl("FINAL_FREEZE_V3B")
    for name, dg in fz["register_digests"].items():
        assert _digest(jl(name)) == dg, name
    assert fz["release_label"].startswith("V3b FULL-BOQ CANDIDATE") and fz["code_commit"]


def test_engine_qa_passes_and_every_check_is_true():
    q = jl("FINAL_QA_V3B")
    assert q["state"] == "PASS" and all(q["checks"].values())


def test_no_provisional_value_ever_sits_in_the_technical_view(boq):
    for x in boq:
        t = x["release"]["technical"]
        assert t["class"] not in RM.PROVISIONAL + (RM.BUDGET,)
        if t["qty"] is not None:
            assert t["class"] in RM.TECH_IN_TOTAL


def test_every_provisional_carries_class_method_assumption_confidence_and_range(boq):
    pv = [x for x in boq if x["release"]["commercial"]["provisional"]]
    assert pv
    for x in pv:
        c = x["release"]["commercial"]
        for k in ("class", "method", "assumption", "confidence", "low", "high"):
            assert c.get(k) is not None, (x["code"], k)
        assert c["low"] - 1e-6 <= c["qty"] <= c["high"] + 1e-6
        assert c["procurement_eligible"] == (c["class"] in RM.PROVISIONAL and c["confidence"] == "H"
                                             or c["class"] == "OWNER_APPROVED_PROVISIONAL")


def test_budget_estimates_are_beside_never_inside_the_commercial_total(boq):
    for x in boq:
        c = x["release"]["commercial"]
        if c["class"] == RM.BUDGET:
            assert not c["in_commercial_total"] and c["budget"] and not c["procurement_eligible"]


def test_waste_is_pending_blank_never_zero_except_the_computed_rebar_cut(boq):
    for x in boq:
        w = x["waste"]
        if w["STATE"] == "PENDING":
            assert w["WASTE_PCT"] is None and w["WASTE_QTY"] is None and w["PROCUREMENT"] is None
        if w["STATE"] == "COMPUTED":
            assert x["code"].startswith("R-BBS") and w["WASTE_METHOD"] == "CUTTING_OPTIMISATION"
    assert any(x["waste"]["STATE"] == "COMPUTED" for x in boq)


def test_rebar_net_and_purchased_are_separate_rows_never_summed():
    m = jl("MASTER_MATRIX_V3B")["rows"]
    items = {r["item"] for r in m if r["trade"] == "REBAR"}
    assert {"Rebar - net design weight (straight + hooks)", "Rebar - purchased from 12 m stock (commercial population)",
            "Rebar - purchased from 12 m stock (technical population)"} <= items
    assert all(r["unit"] == "kg" for r in m if r["trade"] == "REBAR")


def test_blinding_owner_full_footprint_in_total_and_local_detail_alternative(boq):
    by = {x["code"]: x for x in boq}
    full = by["C-BLD-FULL"]
    assert full["release"]["technical"]["class"] == "OWNER_PROJECT_FACT" and full["release"]["technical"]["in_total"]
    for c in ("C-BLD-F", "C-BLD-GB"):
        assert by[c]["no_total"] == "ALTERNATIVE" and not by[c]["release"]["technical"]["in_total"]
    st = jl("STRUCTURE_V3B_REGISTER")["blinding"]
    o = st["OWNER_FULL_FOOTPRINT_BLINDING"]
    assert abs(o["volume_m3"] - o["area_m2"] * 0.10) < 1e-3 and len(o["footprints"]) == 2


def test_concrete_lines_record_strength_cement_soil_and_source(boq):
    for x in boq:
        if x["trade"] == "CONCRETE":
            c = x["concrete"]
            assert set(c) == {"CONCRETE_STRENGTH", "CEMENT_TYPE", "SOIL_CONTACT", "SULFATE_REQUIREMENT", "SOURCE"}
            assert "350" not in c["CONCRETE_STRENGTH"]


def test_every_v3a_line_is_carried_or_superseded():
    rows = jl("SUPERSESSION_REGISTER")["rows"]
    assert rows and all(r["fate"] in ("CARRIED", "SUPERSEDED") for r in rows)


def test_f_f10_is_a_source_conflict_with_a_labelled_selected_range(boq):
    x = next(x for x in boq if x["code"] == "C-FTG-FF10")
    assert x["release"]["technical"]["class"] == "BLOCKED_SOURCE_CONFLICT"
    c = x["release"]["commercial"]
    assert c["class"] == "PROVISIONAL_SOURCE_RANGE" and "SELECTED COMMERCIAL BASIS" in c["assumption"]
    assert c["low"] < c["high"] and c["qty"] == c["high"]


def test_wet_faces_carry_no_general_plaster_and_dry_faces_the_three_layers(boq):
    codes = {x["code"] for x in boq}
    fin = jl("FINISH_V3B_REGISTER")["rooms"]
    for r in fin:
        if r["wet"]:
            assert f"P-RP-{r['room']}" not in codes and r["sequence"]["GENERAL_PLASTER"] == 0.0
        elif r["net"].get("PLASTER"):
            assert {f"P-SD-{r['room']}", f"P-RP-{r['room']}", f"P-SP-{r['room']}"} <= codes


def test_beads_only_on_plastered_faces():
    f = jl("FINISH_V3B_REGISTER")
    assert all(s["finish_population"] in ("PLASTER", None) for s in f["beads"] if s["status"] == "MEASURED")
    assert f["bead_total"]["measured_lm"] > 15.7


def test_domes_three_with_two_route_spans():
    d = jl("STRUCTURE_V3B_REGISTER")["domes"]
    assert d["count"] == 3 and d["count_route_c"]["value"] == 3
    for x in d["rows"]:
        assert abs(x["span_m"] - x["span_route_c_m"]) <= 0.02


def test_owner_methods_are_never_globalised():
    om = jl("OWNER_METHOD_REGISTER")["rows"]
    assert om and not any(x["globalised"] for x in om)
    assert {x["promotion_class"] for x in om} <= {"URBAN_STANDARD_CANDIDATE", "PROJECT_ONLY"}


def test_evaluation_ran_after_the_freeze_and_changed_nothing():
    ev = jl("BENCHMARK_EVALUATION_V3B", E)
    assert ev["run"] == "AFTER_FREEZE" and ev["evaluation_only"]
    assert ev["v3b_freeze_sha256"] == hashlib.sha256((R / "FINAL_FREEZE_V3B.json").read_bytes()).hexdigest()
    mm = jl("MISMATCH_REGISTER", E)
    assert all(c["classification"] and c["inspect_next"] for c in mm["cases"])


def test_qortuba_shadow_unchanged():
    q = jl("QORTUBA_V3B_SHADOW", E)
    assert q["state"] == "UNCHANGED" and q["frozen_sites"] == q["v3_sites"] == 72


def test_mutation_a_provisional_class_in_the_technical_column_is_refused():
    with pytest.raises(RM.ReleaseError):
        RM.release("PROVISIONAL_GEOMETRIC_INFERENCE", 10.0)
    with pytest.raises(RM.ReleaseError):
        RM.release("BLOCKED", None, {"class": "BUDGET_ESTIMATE", "qty": 3.0, "method": "m", "assumption": "a",
                                     "confidence": "L", "low": 4.0, "high": 5.0})


def test_mutation_matrix_detects_a_changed_line():
    boq = jl("BOQ_LINES_V3B")["lines"]
    m = jl("MASTER_MATRIX_V3B")["rows"]
    x = next(x for x in boq if x["code"] == "C-BLD-FULL")
    row = next(r for r in m if r["item"] == x["sumrow"] and r["trade"] == "CONCRETE")
    tot = sum(y["release"]["technical"]["qty"] for y in boq if y["trade"] == "CONCRETE" and y.get("sumrow") == row["item"]
              and y["release"]["technical"]["in_total"] and not y.get("no_total"))
    assert abs(tot - row["technical"]["total"]) < 1e-4
    assert abs(tot + 1.0 - row["technical"]["total"]) > 0.5          # a mutated line would no longer match
