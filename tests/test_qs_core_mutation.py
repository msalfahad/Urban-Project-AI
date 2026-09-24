"""Put each defect back, deliberately, and require the engine's own checks to catch it.

A quality check that has only ever seen correct output proves nothing.  Each test here implements the defective
behaviour the engine used to have - or could drift back into - runs the real invariant over it, and fails if the
invariant is content.
"""

from __future__ import annotations

import pytest

from engine.qs_core import geom, invariants, openings as op, spaces as sp, synthetic as syn
from engine.qs_core.entities import (ASSIGNED_TO_SPACE, HOST_ASSIGNED, KIND_WALL_BAND, Evidence)


# ------------------------------------------------------------------ defect 1: pro-rata allocation
def prorata_wall_rows(wall_bands, register, height):
    """The defect: pool the openings and share them out in proportion to wall length."""
    total = register["TOTAL_OPENING_AREA_M2"]
    length = sum(b.length for b in wall_bands) or 1.0
    rows = []
    for b in wall_bands:
        share = b.length / length
        rows.append({"COMPONENT_REF": b.component_ref, "FLOOR": b.floor, "THICKNESS_M": b.thickness,
                     "LENGTH_M": b.length, "HEIGHT_M": height, "GROSS_AREA_M2": b.length * height,
                     "OPENING_DEDUCTION_M2": total * share,
                     "NET_AREA_M2": b.length * height - total * share,
                     "DEDUCTION_SOURCE": "pro-rata by wall length", "STATUS": "FINAL_QUANTITY_AVAILABLE",
                     "BLOCKED_NOTE": None})
    return rows


def _two_bands_one_door():
    thin = syn.wall_band("W-150", (0.0, 0.0, 6.0, 0.15), 0.15, geom.AXIS_X)
    thick = syn.wall_band("W-200", (0.0, 3.0, 4.0, 3.20), 0.20, geom.AXIS_X)
    door = syn.opening("OP-1", (1.0, 0.0, 1.9, 0.15), geom.AXIS_X, 0.90, 2.10)
    return thin, thick, door


def test_pro_rata_allocation_puts_material_against_the_wrong_wall_and_is_caught():
    thin, thick, door = _two_bands_one_door()
    reg = op.build_opening_register([door], [thin, thick], syn.TOL)
    honest = {r["COMPONENT_REF"]: r for r in op.wall_band_quantities([thin, thick], reg, 3.0, True)}
    defective = {r["COMPONENT_REF"]: r for r in prorata_wall_rows([thin, thick], reg, 3.0)}

    assert honest["W-200"]["OPENING_DEDUCTION_M2"] == 0.0
    assert defective["W-200"]["OPENING_DEDUCTION_M2"] > 0.0, "the defect must actually misallocate"

    # the giveaway: the TOTAL still reconciles, which is why a check on the total alone cannot see this defect
    assert invariants.deductions_reconcile(reg, list(defective.values()), 1e-9)["PASS"]
    check = invariants.deductions_match_band_by_band(reg, list(defective.values()), 1e-9)
    assert not check["PASS"], "an invariant that accepts pro-rata allocation is not an invariant"
    assert {o["COMPONENT_REF"] for o in check["RESULT"]["OFFENDERS"]} == {"W-150", "W-200"}
    assert invariants.deductions_match_band_by_band(reg, list(honest.values()), 1e-9)["PASS"]


def test_pro_rata_allocation_of_an_unresolved_opening_is_caught():
    left = syn.wall_band("W-A", (0.0, 0.0, 3.0, 0.15), 0.15, geom.AXIS_X)
    right = syn.wall_band("W-B", (3.0, 0.0, 6.0, 0.20), 0.20, geom.AXIS_X)
    straddling = syn.opening("OP-1", (2.55, 0.0, 3.45, 0.15), geom.AXIS_X, 0.90, 2.10)
    reg = op.build_opening_register([straddling], [left, right], syn.TOL)
    assert reg["UNRESOLVED_COUNT"] == 1
    defective = prorata_wall_rows([left, right], reg, 3.0)
    check = invariants.unresolved_never_allocated(reg, defective, 1e-9)
    assert not check["PASS"], "an unresolved opening was spread across the walls and nothing objected"


# ------------------------------------------------------------------ defect 2: scan-order identity
def scan_order_assign(entities, revision):
    """The defect: number the entities in the order they happen to arrive."""
    for i, e in enumerate(entities):
        e.uid = f"{revision}-{i:03d}"
        e.persistent_id = e.uid


def test_scan_order_identity_is_caught_by_the_order_independence_check():
    plan = syn.small_plan("R1")
    defective = invariants.identity_is_order_independent(plan["COMPONENTS"], "R1", assign=scan_order_assign)
    assert not defective["PASS"], "identity that depends on input order must be caught"
    assert defective["RESULT"]["COMPONENTS_WHOSE_UID_MOVED"]
    honest = invariants.identity_is_order_independent(plan["COMPONENTS"], "R1")
    assert honest["PASS"]


# ------------------------------------------------------------------ defect 3: label only on its own fragment
def label_only_where_the_text_sits(components, labels, tolerance):
    """The defect: every component is its own room, and a label names only the fragment it sits in."""
    membership = []
    for c in sorted(components, key=lambda x: x.component_ref):
        text = next((lb.text for lb in labels
                     if any(r.contains_point(lb.x, lb.y, tolerance) for r in c.rects)), None)
        membership.append({"COMPONENT_REF": c.component_ref, "ROOM_ID": f"ROOM::{c.component_ref}",
                           "FLOOR": c.floor, "KIND": c.kind, "AREA_M2": c.area,
                           "STATUS": ASSIGNED_TO_SPACE, "LABEL": text, "LABEL_STATUS": None, "EVIDENCE": []})
    return membership


def test_a_label_confined_to_its_own_fragment_is_caught():
    comps, barriers, openings, labels = syn.one_room_in_two_fragments()
    honest = sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")
    defective = label_only_where_the_text_sits(comps, labels, syn.TOL)

    assert invariants.continuous_floor_is_one_space(honest["SEAMS"], honest["MEMBERSHIP"])["PASS"]
    check = invariants.continuous_floor_is_one_space(honest["SEAMS"], defective)
    assert not check["PASS"], "floor that continues without a boundary was split into two rooms"
    assert check["RESULT"]["OFFENDERS"][0]["ROOM_A"] != check["RESULT"]["OFFENDERS"][0]["ROOM_B"]


# ------------------------------------------------------------------ defect 4: agreement mistaken for proof
def test_a_check_that_cites_a_known_total_is_rejected():
    forbidden = ["931.016", "734.638"]
    honest = [{"INVARIANT": "INV-X", "PASS": True, "INPUTS": {"COMPONENTS": 3},
               "RESULT": {"SUM_M2": 12.0}, "METHOD": "re-summed from the components"}]
    defective = [{"INVARIANT": "INV-Y", "PASS": True, "INPUTS": {"EXPECTED_TOTAL_M2": "931.016"},
                  "RESULT": {"AGREES": True}, "METHOD": "compared with the accepted total"}]
    assert invariants.checks_are_evidence_based(honest, forbidden)["PASS"]
    bad = invariants.checks_are_evidence_based(defective, forbidden)
    assert not bad["PASS"]
    assert "comparison value" in bad["RESULT"]["OFFENDERS"][0]["WHY"]


def test_a_check_with_no_method_is_rejected():
    assert not invariants.checks_are_evidence_based(
        [{"INVARIANT": "INV-Z", "PASS": True, "INPUTS": {}, "RESULT": {}, "METHOD": ""}], [])["PASS"]


# ------------------------------------------------------------------ defect 5: resolving the unresolvable
def greedy_assign(opening, bands, tol):
    """The defect: always take the best-scoring candidate, however close the runner-up."""
    scored = sorted(((op.score_host(opening, b, tol), b) for b in bands), key=lambda t: -t[0]["SCORE"])
    s, b = scored[0]
    opening.host_status = HOST_ASSIGNED
    opening.host_component_ref = b.component_ref
    opening.host_thickness = b.thickness
    opening.host_candidates = [{"COMPONENT_REF": bb.component_ref, "THICKNESS_M": bb.thickness,
                                "SCORE": round(ss["SCORE"], 6), "EVIDENCE": ss} for ss, bb in scored]
    opening.host_evidence = [Evidence("BEST_SCORING_CANDIDATE", {})]
    return opening


def test_resolving_an_ambiguous_host_by_picking_the_leader_is_caught():
    a = syn.wall_band("W-A", (0.0, 0.0, 6.0, 0.16), 0.16, geom.AXIS_X)
    b = syn.wall_band("W-B", (0.0, 0.0, 6.0, 0.17), 0.17, geom.AXIS_X)
    o = syn.opening("OP-1", (1.0, 0.0, 1.9, 0.165), geom.AXIS_X, 0.90, 2.10)
    greedy_assign(o, [a, b], syn.TOL)
    register = {"REGISTER": [o.as_dict()], "OPENING_COUNT": 1}
    check = invariants.ambiguous_hosts_are_surfaced(register, op.DECISIVE_MARGIN)
    assert not check["PASS"], "a tie was resolved silently and nothing objected"
    assert check["RESULT"]["ASSIGNED_DESPITE_A_TIE"][0]["OPENING_REF"] == "OP-1"


def test_the_production_assigner_leaves_the_same_case_unresolved():
    a = syn.wall_band("W-A", (0.0, 0.0, 6.0, 0.16), 0.16, geom.AXIS_X)
    b = syn.wall_band("W-B", (0.0, 0.0, 6.0, 0.17), 0.17, geom.AXIS_X)
    o = syn.opening("OP-1", (1.0, 0.0, 1.9, 0.165), geom.AXIS_X, 0.90, 2.10)
    reg = op.build_opening_register([o], [a, b], syn.TOL)
    assert reg["UNRESOLVED_COUNT"] == 1
    assert invariants.ambiguous_hosts_are_surfaced(reg, op.DECISIVE_MARGIN)["PASS"]


# ------------------------------------------------------------------ defect 6: wall material as floor
def test_wall_material_counted_as_floor_finish_is_caught():
    comps, barriers, openings, labels = syn.two_rooms_with_a_thick_wall()
    honest = sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")
    assert invariants.no_wall_material_as_floor(honest["MEMBERSHIP"])["PASS"]
    defective = [dict(m) for m in honest["MEMBERSHIP"]]
    for m in defective:
        if m["KIND"] == KIND_WALL_BAND:
            m["ROOM_ID"] = "ROOM::SOMETHING"
            m["STATUS"] = ASSIGNED_TO_SPACE
    check = invariants.no_wall_material_as_floor(defective)
    assert not check["PASS"] and check["RESULT"]["OFFENDERS"] == ["W-1"]


def test_a_component_left_in_no_state_at_all_is_caught():
    comps, barriers, openings, labels = syn.two_rooms_with_a_thick_wall()
    honest = sp.assemble_semantic_spaces(comps, barriers, openings, labels, syn.TOL, syn.SLIVER_MIN, "R1")
    defective = [dict(m) for m in honest["MEMBERSHIP"]]
    defective[0]["STATUS"] = "SOMETHING_ELSE"
    assert not invariants.every_component_resolved_once(defective)["PASS"]
    defective = [dict(m) for m in honest["MEMBERSHIP"]] + [dict(honest["MEMBERSHIP"][0])]
    assert not invariants.every_component_resolved_once(defective)["PASS"]
