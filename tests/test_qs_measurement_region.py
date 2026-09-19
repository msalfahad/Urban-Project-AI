"""Synthetic known-answer fixtures for the measurement-region builder.

No P7757 geometry. Every fixture is a small closed or broken cell whose
correct outcome is known by construction, so the invariants are tested
against answers that cannot have been tuned.
"""

from __future__ import annotations

import pytest

from engine import qs_measurement_region as M

PL = "NORMAL_INTERNAL_PLASTER"
B = "WALL_FACE_PLASTER"


def wall(eid, a, b, L, kind="PHYSICAL_WALL_FACE"):
    return {"EDGE_ID": eid, "KIND": kind, "a": a, "b": b, "length_m": L,
            "length_source": "DRAWING_PRINTED_DIMENSION",
            "trace_ids": [f"SEG-{eid}"]}


def site(sid, a, b, span, kind="CONFIRMED_DOOR_OPENING"):
    return {"SITE_ID": sid, "SITE_TYPE": kind, "termination_a": a,
            "termination_b": b, "span_m": span, "evidence": ["door leaf"],
            "trace_ids": [f"D-{sid}"]}


# A: a 4 x 3 room with one door in the south wall
def fixture_a():
    walls = [wall("N", (0, 3), (4, 3), 4.0),
             wall("E", (4, 3), (4, 0), 3.0),
             wall("S1", (4, 0), (2.5, 0), 1.5),
             wall("S2", (1.5, 0), (0, 0), 1.5),
             wall("W", (0, 0), (0, 3), 3.0)]
    sites = [site("S-DOOR", (2.5, 0), (1.5, 0), 1.0)]
    openings = [{"OPENING_ID": "D-01", "TYPE": "DOOR", "HOSTED_IN": "S",
                 "width_m": 1.0, "width_source": "DRAWING_PRINTED_DIMENSION",
                 "height_m": None, "height_source": None, "trace_ids": ["D-01"]}]
    return walls, sites, openings


def test_a_closes_through_a_door_and_the_door_contributes_nothing():
    walls, sites, openings = fixture_a()
    r = M.build_region(region_id="A", physical_edges=walls, sites=sites,
                       openings=openings, trade=PL, basis=B)
    assert r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED"
    # 4 + 3 + 1.5 + 1.5 + 3 = 13.0 lm, and NOT the 14.0 perimeter
    assert r["GROSS_BASIS"]["VALUE"] == 13.0
    assert r["GROSS_BASIS"]["IS_A_POLYGON_PERIMETER"] is False
    assert len(r["SYNTHETIC_CLOSURES"]) == 1
    c = r["SYNTHETIC_CLOSURES"][0]
    assert c["material_present"] is False
    assert c["quantity_length_contribution"] == 0.0
    assert c["TRADE_CONTRIBUTION"]["LENGTH_CONTRIBUTES"] is False
    assert r["INVARIANTS"]["REVERSIBLE"] is True
    assert r["INVARIANTS"]["ZERO_MATERIAL_CONTRIBUTION"] is True
    assert r["NO_QUANTITY_WAS_COMPUTED_HERE"] is True


def test_a_opening_height_is_left_to_the_parameter_layer():
    walls, sites, openings = fixture_a()
    r = M.build_region(region_id="A", physical_edges=walls, sites=sites,
                       openings=openings, trade=PL, basis=B)
    assert r["OPENINGS"][0]["DEDUCTION_STATUS"] == "AWAITING_PARAMETER_OR_SOURCE"
    assert r["DEDUCTIONS"]["HEIGHT_IS_A_PARAMETER_NOT_RESOLVED_HERE"] is True


# B: the same room, but the gap is UNRESOLVED - must NOT close
def test_b_unresolved_gap_is_never_bridged():
    walls, _, openings = fixture_a()
    sites = [site("S-GAP", (2.5, 0), (1.5, 0), 1.0, kind="UNRESOLVED_GAP")]
    r = M.build_region(region_id="B", physical_edges=walls, sites=sites,
                       openings=[], trade=PL, basis=B)
    assert r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_NOT_ESTABLISHED"
    reasons = {x["REASON"] for x in r["NOT_ESTABLISHED_BECAUSE"]}
    assert "THE_BOUNDARY_DOES_NOT_MEET_ITSELF" in reasons
    assert "A_SITE_THIS_BASIS_MAY_NOT_CLOSE_LIES_ON_THE_BOUNDARY" in reasons
    assert r["SYNTHETIC_CLOSURES"] == []
    assert r["GROSS_BASIS"]["VALUE"] is None


# C: an open-plan passage: closable only under the open-plan basis
def test_c_open_passage_depends_on_the_measurement_basis():
    walls, _, _ = fixture_a()
    sites = [site("S-OPEN", (2.5, 0), (1.5, 0), 1.0,
                  kind="CONFIRMED_OPEN_PASSAGE")]
    strict = M.build_region(region_id="C", physical_edges=walls, sites=sites,
                            openings=[], trade=PL, basis=B)
    assert strict["MEASUREMENT_REGION_STATUS"] == \
        "MEASUREMENT_REGION_NOT_ESTABLISHED"
    cell = M.build_region(region_id="C", physical_edges=walls, sites=sites,
                          openings=[], trade=PL,
                          basis="WALL_FACE_PLASTER_OPEN_PLAN_CELL")
    assert cell["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED"
    # and the closure still contributes nothing under either basis
    assert cell["SYNTHETIC_CLOSURES"][0]["quantity_length_contribution"] == 0.0
    assert cell["GROSS_BASIS"]["VALUE"] == 13.0


# D: an UNRESOLVED_EDGE on the boundary blocks the region even if it rings
def test_d_unresolved_edge_blocks_even_a_closed_ring():
    walls, sites, _ = fixture_a()
    walls[0] = wall("N", (0, 3), (4, 3), 4.0, kind="UNRESOLVED_EDGE")
    r = M.build_region(region_id="D", physical_edges=walls, sites=sites,
                       openings=[], trade=PL, basis=B)
    assert r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_NOT_ESTABLISHED"
    assert any(x["REASON"] == "AN_UNRESOLVED_GAP_LIES_ON_THE_BOUNDARY"
               for x in r["NOT_ESTABLISHED_BECAUSE"])


# E: glazing is a boundary for floor area but carries no plaster length
def test_e_glazing_contributes_to_floor_boundary_not_plaster():
    walls, sites, _ = fixture_a()
    walls[1] = wall("E", (4, 3), (4, 0), 3.0, kind="GLAZING_BOUNDARY")
    plaster = M.build_region(region_id="E", physical_edges=walls, sites=sites,
                             openings=[], trade=PL, basis=B)
    assert plaster["GROSS_BASIS"]["VALUE"] == 10.0          # 13 - 3
    assert any(x["EDGE_ID"] == "E"
               for x in plaster["GROSS_BASIS"]["NON_CONTRIBUTING_EDGES"])
    floor = M.build_region(region_id="E", physical_edges=walls, sites=sites,
                           openings=[], trade="FLOOR_AREA_BOUNDARY",
                           basis="FLOOR_AREA")
    assert any(x["EDGE_ID"] == "E"
               for x in floor["GROSS_BASIS"]["CONTRIBUTING_EDGES"])


# F: a synthetic closure can never be smuggled in as physical geometry
def test_f_closure_cannot_be_passed_as_physical():
    walls, sites, _ = fixture_a()
    walls.append({"EDGE_ID": "FAKE", "KIND": M.SYNTHETIC_KIND,
                  "a": (2.5, 0), "b": (1.5, 0), "length_m": 1.0})
    with pytest.raises(ValueError):
        M.build_region(region_id="F", physical_edges=walls, sites=sites,
                       openings=[], trade=PL, basis=B)


# G: a contributing edge with no established length -> gross not established
def test_g_missing_length_on_a_contributing_edge():
    walls, sites, _ = fixture_a()
    walls[0]["length_m"] = None
    walls[0]["length_source"] = None
    r = M.build_region(region_id="G", physical_edges=walls, sites=sites,
                       openings=[], trade=PL, basis=B)
    assert r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_CLOSED"
    assert r["GROSS_BASIS"]["STATUS"] == "NOT_ESTABLISHED"
    assert r["GROSS_BASIS"]["VALUE"] is None


# H: reversibility is checked by hash on every build
def test_h_physical_hash_survives_closure():
    walls, sites, _ = fixture_a()
    before = M.canon_hash(walls)
    r = M.build_region(region_id="H", physical_edges=walls, sites=sites,
                       openings=[], trade=PL, basis=B)
    assert r["INVARIANTS"]["PHYSICAL_HASH_BEFORE"] == before
    assert r["INVARIANTS"]["PHYSICAL_HASH_AFTER_CLOSURE_REMOVAL"] == before
    assert M.canon_hash(walls) == before


# I: a parapet is a run, not a cell - no ring, closures irrelevant, gross
# is still the contributing sum and an unresolved edge still blocks it
def test_i_linear_run_needs_no_ring_but_still_refuses_unresolved():
    run = [wall("P1", (0, 0), (5, 0), 5.0), wall("P2", (5, 0), (5, 2), 2.0)]
    r = M.build_region(region_id="I", physical_edges=run, sites=[],
                       openings=[], trade="EXTERNAL_PLASTER", basis=M.LINEAR_RUN)
    assert r["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_RUN_ESTABLISHED"
    assert r["REGION_SHAPE"] == "LINEAR_RUN" and r["RING_REQUIRED"] is False
    assert r["GROSS_BASIS"]["VALUE"] == 7.0
    run[1] = wall("P2", (5, 0), (5, 2), 2.0, kind="UNRESOLVED_EDGE")
    r2 = M.build_region(region_id="I", physical_edges=run, sites=[],
                        openings=[], trade="EXTERNAL_PLASTER", basis=M.LINEAR_RUN)
    assert r2["MEASUREMENT_REGION_STATUS"] == "MEASUREMENT_REGION_NOT_ESTABLISHED"


def test_i_linear_run_never_closes_a_site():
    run = [wall("P1", (0, 0), (5, 0), 5.0)]
    r = M.build_region(region_id="I", physical_edges=run,
                       sites=[site("S", (5, 0), (7, 0), 2.0)], openings=[],
                       trade="EXTERNAL_PLASTER", basis=M.LINEAR_RUN)
    assert r["SYNTHETIC_CLOSURES"] == []
    assert r["GROSS_BASIS"]["VALUE"] == 5.0
