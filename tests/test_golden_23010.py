"""Project 23010 — the permanent golden regression.

Twelve traps, each one a mistake this project actually made. Any change to A1,
A2, E23, E25, E27, E28, E30, E32, E33 or the quantity assembler re-runs these.

The geometry assertions carry exact numbers on purpose: a semantic change that
moves a deterministic area is a bug in the separation, not a better answer.
"""

from __future__ import annotations

import json
from decimal import Decimal as D
from pathlib import Path

import pytest

from agents.a1_extractor.semantic import (SemanticError, SemanticInput,
                                          SemanticOutput, SpaceSemantics)
from agents.a2_reviewer.agent import BlindIsolationError, run_blind
from agents.a2_reviewer.challenge import ChallengeError, ChallengeOutput
from engine.geometry import (GeometryCandidate, calibrate, choose_geometry,
                             snap_to_wall_faces)
from engine.quantities import AUTO_VALIDATED, SpaceInputs, assemble, total
from engine.release import apply, route
from engine.semantic_compare import (AGREE_HIGH_CONFIDENCE, AGREE_LOW_CONFIDENCE,
                                     CRITICAL, SOURCE_CONFLICT, compare_space)
from engine.trade_rules import TradeRuleSet

CERAMIC = TradeRuleSet.load("data/trade_rules/23010_ceramic.json")
PLASTER = TradeRuleSet.load("data/trade_rules/23010_plaster.json")


def sem(**kw) -> SpaceSemantics:
    base = dict(space_id="X", semantic_label="BEDROOM", label_source="PDF_TEXT",
                label_confidence="HIGH", confidence_basis="text + polygon + schedule",
                scope_status="IN_SCOPE")
    base.update(kw)
    return SpaceSemantics(**base)


# 1 ── the IRON_ROOM trap
def test_1_the_drawing_label_wins_over_the_historical_takeoff_name():
    """AR-00 says كوي IRON; the old MEASURER calls the same space مطبخ."""
    from engine.trades import normalize_label
    assert normalize_label("كوي") == "IRON_ROOM"
    a1 = sem(space_id="IRN-01", semantic_label="IRON_ROOM",
             original_drawing_label="كوي IRON",
             semantic_conflicts=["historical takeoff labels this مطبخ"])
    assert a1.semantic_label == "IRON_ROOM"
    assert a1.original_drawing_label == "كوي IRON"     # raw label never destroyed
    # and the unresolved conflict keeps it out of auto-pass
    assert compare_space(a1, sem(space_id="IRN-01", semantic_label="IRON_ROOM")
                         ).verdict == AGREE_LOW_CONFIDENCE


# 2 ── washroom versus the shaft beside it
def test_2_a_shaft_called_a_washroom_is_critical():
    c = compare_space(sem(space_id="WSH-01", semantic_label="WASHROOM"),
                      sem(space_id="WSH-01", semantic_label="SHAFT"))
    assert c.materiality == CRITICAL
    assert "not usable floor" in c.diffs[0].note


# 3 ── the wash room is irregular and must stay irregular
def test_3_an_irregular_room_is_not_snapped_to_a_rectangle():
    v = [(0.0, 0.0, 300.0)]                     # only one bounding face known
    h = [(0.0, 0.0, 300.0), (200.0, 0.0, 300.0)]
    _, complete = snap_to_wall_faces(5, 195, 5, 195, v, h)
    assert not complete, "a partly-bounded region must not be reported as snapped"


# 4 ── master bath: design split, site combined
def test_4_design_and_site_topology_do_not_overwrite_each_other():
    from engine.reconcile import DESIGN_VS_SITE, Quantities, Reconciliation
    r = Reconciliation(
        space_id="BTH-M",
        design=Quantities(D("15.15"), D("16.10"), "AR-00 split: 3450x3000 + 1600x3000",
                          basis="PRINTED_DIMENSION_REFERENCE"),
        site=Quantities(D("15.34"), D("16.30"), "MEASURER: one combined bathroom",
                        basis="SITE_MEASURED_FACE"),
        classification=DESIGN_VS_SITE)
    assert r.design.area_m2 != r.site.area_m2
    assert not r.design.comparable_with(r.site)      # different bases, not an error


# 5 ── the wrong apartment
def test_5_a_cross_apartment_disagreement_is_critical():
    c = compare_space(sem(apartment_id="RIGHT"), sem(apartment_id="LEFT"))
    assert c.materiality == CRITICAL and not c.is_pass_candidate


# 6 ── open plan
def test_6_open_plan_is_one_space_and_needs_no_invented_boundaries():
    out = SemanticOutput.from_dict({"spaces": [{
        "space_id": "OPEN-01", "semantic_label": "OPEN_PLAN_LIVING",
        "label_source": "PDF_TEXT", "label_confidence": "MEDIUM",
        "confidence_basis": "geometry shows one continuous region",
        "scope_status": "IN_SCOPE",
        "drawing_notes": "dining, east salon and the 12400 corridor are continuous"}]})
    assert out.spaces[0].semantic_label == "OPEN_PLAN_LIVING"
    assert not out.spaces[0].geometry_challenge


# 7 ── BTH-07 stays fixed
def test_7_bth_07_geometry_is_pinned_at_its_printed_area():
    """3.56 m2 was the fixture-closure defect; 4.80 is the printed design."""
    printed = D("1600") * D("3000") / D("1000000")
    assert printed == D("4.80")
    ch = choose_geometry([GeometryCandidate("RASTER_TRACE", D("4.08")),
                          GeometryCandidate("PRINTED_DIMENSION", printed)])
    assert ch.value == D("4.80")


# 8 ── BTH-04's raster perimeter stays rejected
def test_8_the_bad_raster_perimeter_is_still_rejected_and_named():
    ch = choose_geometry([GeometryCandidate("RASTER_TRACE", D("14.29")),
                          GeometryCandidate("PRINTED_DIMENSION", D("8.70"))])
    assert ch.value == D("8.70") and ch.status == "CHALLENGE"
    assert ch.rejected and "rejected" in ch.rejected[0][1]


# 9 ── source hierarchy
def test_9_raster_never_outranks_vector_or_printed():
    ch = choose_geometry([GeometryCandidate("RASTER_TRACE", D("9.9")),
                          GeometryCandidate("VECTOR_PDF", D("10.0")),
                          GeometryCandidate("PRINTED_DIMENSION", D("10.1"))])
    assert ch.chosen.source == "VECTOR_PDF"


# 10 ── the blind pass is blind
def test_10_the_blind_pass_cannot_see_a1():
    payload = SemanticInput(project_id="23010", drawing_id="AR-00",
                            drawing_revision="MAR.2023", floor_id="2F",
                            geometry={"S1": {"area_m2": "4.53"}})
    with pytest.raises(BlindIsolationError):
        run_blind(payload, model=lambda s, u: "{}", a1_output={"S1": "BATHROOM"})


# 11 ── a challenge cannot mutate a quantity
def test_11_a_challenge_cannot_change_a_number():
    with pytest.raises(ChallengeError, match="never proposes a number"):
        ChallengeOutput.from_dict({"challenges": [
            {"challenge_id": "C1", "should_be": 4.53}]})
    sp = SpaceInputs("BTH-03", "2F", "BATHROOM", "A1+A2", "VALIDATED",
                     D("4.53"), D("8.60"), "E23", "CLEAR_INTERNAL_FINISH_FACE",
                     "AR-00", "MAR.2023")
    qs = assemble("23010", [sp], [CERAMIC])
    stamped = apply(qs, route(qs, comparisons={"BTH-03": None}))
    assert [q.value for q in stamped] == [q.value for q in qs]


# 12 ── the unresolved dry row stays unresolved
def test_12_an_unmatched_benchmark_row_is_not_forced_onto_a_room():
    from engine.reconcile import UNRESOLVED, BenchmarkReport, Quantities, Reconciliation
    rep = BenchmarkReport(rows=[Reconciliation(
        space_id="DRY-ROW-04",
        site=Quantities(D("61.55"), None, "MEASURER row 4", basis="SITE_MEASURED_FACE"),
        classification=UNRESOLVED,
        explanation="61.55 m2 has no single design counterpart; largest is 52.14")])
    assert not rep.ready_for_agents          # unresolved blocks, as designed
    assert rep.unresolved[0].space_id == "DRY-ROW-04"


# ── geometry immutability: semantics must not move a deterministic number
def test_semantic_work_leaves_the_scale_calibration_untouched():
    c = calibrate(887.82, 40000, 554.94, 25000)
    assert round(c.mm_per_pt, 4) == D("45.0542")


def test_trade_heights_stay_independent_per_trade():
    assert CERAMIC.height_m == D("3.00") and PLASTER.height_m == D("3.20")


def test_a_bathroom_releases_only_when_every_condition_is_met():
    sp = SpaceInputs("BTH-03", "2F", "BATHROOM", "A1+A2", "VALIDATED",
                     D("4.53"), D("8.60"), "E23", "CLEAR_INTERNAL_FINISH_FACE",
                     "AR-00", "MAR.2023")
    qs = assemble("23010", [sp], [CERAMIC])
    good = compare_space(sem(space_id="BTH-03", semantic_label="BATHROOM"),
                         sem(space_id="BTH-03", semantic_label="BATHROOM"))
    assert good.verdict == AGREE_HIGH_CONFIDENCE
    q = route(qs, comparisons={"BTH-03": good}, approved_revision="MAR.2023")
    assert len(q.auto_validated) == 2
    assert total(apply(qs, q)) == D("4.53") + D("8.60") * D("3.00")


def test_two_agents_agreeing_against_a_schedule_still_blocks_release():
    sp = SpaceInputs("S9", "2F", "BATHROOM", "A1+A2", "VALIDATED",
                     D("4.0"), D("8.0"), "E23", "CLEAR_INTERNAL_FINISH_FACE",
                     "AR-00", "MAR.2023")
    qs = assemble("23010", [sp], [CERAMIC])
    conflicted = compare_space(sem(space_id="S9", semantic_label="BATHROOM"),
                               sem(space_id="S9", semantic_label="BATHROOM"),
                               schedule_label="STORE")
    assert conflicted.verdict == SOURCE_CONFLICT
    assert total(apply(qs, route(qs, comparisons={"S9": conflicted}))) == D(0)
