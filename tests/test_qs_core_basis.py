"""Whether a wall's drawn material runs through its openings is measured per wall line, not asserted per source.

The previous build took one Boolean for a whole drawing revision.  A source in which one facade is drawn as a
single polyline and the partitions are drawn segment by segment makes that Boolean wrong for half the walls, and
the error is a full opening area on every wall it is wrong about - deducted twice, or not at all.
"""

from __future__ import annotations

from engine.qs_core import evidence as EV, invariants, openings as OP, synthetic as S

TOL, SPAN = S.TOL, S.MAX_OPENING_SPAN
HEIGHT = EV.resolve("wall height", [EV.Claim(3.0, EV.OWNER_PROJECT_INPUT, "TEST")], TOL)


def build(bands, ops):
    lines, _gaps = OP.build_wall_lines(bands, TOL, SPAN, openings=ops)
    register = OP.build_opening_register(ops, lines, TOL)
    basis = OP.evaluate_opening_basis(lines, ops, TOL)
    return lines, register, basis


def test_one_drawing_can_carry_two_different_bases_and_both_are_measured():
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    lines, _register, basis = build(bands, ops)
    found = {b["BASIS"] for b in basis.values()}
    assert OP.MATERIAL_SPANS in found and OP.MATERIAL_STOPS in found, found


def test_the_spanning_wall_is_not_given_back_a_length_it_already_has():
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    lines, register, basis = build(bands, ops)
    rows = {r["COMPONENT_REF"]: r for r in
            OP.wall_band_quantities(lines, register, HEIGHT, basis, {})}
    spanning = next(r for r in rows.values() if r["OPENING_BASIS"] == OP.MATERIAL_SPANS)
    assert spanning["GROSS_LENGTH_M"] == spanning["MATERIAL_LENGTH_M"] == 6.0


def test_the_stopping_wall_gets_the_wall_over_its_door_back_before_deducting_it():
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    lines, register, basis = build(bands, ops)
    rows = {r["COMPONENT_REF"]: r for r in
            OP.wall_band_quantities(lines, register, HEIGHT, basis, {})}
    stopping = next(r for r in rows.values() if r["OPENING_BASIS"] == OP.MATERIAL_STOPS)
    assert round(stopping["MATERIAL_LENGTH_M"], 6) == 5.1
    assert round(stopping["GROSS_LENGTH_M"], 6) == 6.0


def test_both_walls_reach_the_same_net_area_because_they_are_the_same_wall():
    """Same building, two drawing conventions.  A correct engine measures them the same."""
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    lines, register, basis = build(bands, ops)
    rows = OP.wall_band_quantities(lines, register, HEIGHT, basis, {})
    nets = sorted(round(r["NET_AREA_M2"], 6) for r in rows if r["NET_AREA_M2"] is not None)
    assert len(nets) == 2 and nets[0] == nets[1], nets


def test_a_line_with_no_opening_needs_no_basis_and_is_not_blocked_for_want_of_one():
    bands = [S.wall_band("W-PLAIN", (0.0, 0.0, 4.0, 0.20), 0.20, "X")]
    lines, register, basis = build(bands, [])
    assert basis[lines[0].component_ref]["BASIS"] == OP.BASIS_NOT_TESTABLE
    row = OP.wall_band_quantities(lines, register, HEIGHT, basis, {})[0]
    assert row["GROSS_LENGTH_M"] == 4.0


def test_a_line_whose_openings_disagree_is_unresolved_and_carries_no_quantity():
    wall = S.wall_band("W-MIXED", (0.0, 0.0, 6.0, 0.20), 0.20, "X")
    covered = S.opening("OP-IN", (1.0, 0.0, 1.9, 0.20), "X", 0.90, 2.10)
    half = S.opening("OP-HALF", (4.0, 0.10, 4.9, 0.30), "X", 0.90, 2.10)
    lines, register, basis = build([wall], [covered, half])
    rec = basis[lines[0].component_ref]
    assert rec["BASIS"] == OP.BASIS_UNRESOLVED
    row = OP.wall_band_quantities(lines, register, HEIGHT, basis, {})[0]
    assert row["NET_AREA_M2"] is None
    assert row["DIAGNOSTIC_ONLY_NET_AREA_M2_IF_MATERIAL_SPANS"] is not None
    assert row["DIAGNOSTIC_ONLY_NET_AREA_M2_IF_MATERIAL_STOPS_AT_JAMBS"] is not None


def test_the_basis_record_says_how_it_was_detected_and_on_which_openings():
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    _lines, _register, basis = build(bands, ops)
    for rec in basis.values():
        assert rec["DETECTED_BY"] and "MATERIAL_SPANS_THE_OPENING" in rec
        assert isinstance(rec["OPENINGS_TESTED"], list)


def test_the_invariant_catches_a_basis_stated_without_testing_anything():
    bands, ops = S.one_wall_spans_its_door_and_another_stops_at_the_jambs()
    lines, _register, basis = build(bands, ops)
    assert invariants.opening_basis_is_decided_per_wall_line(basis, lines)["PASS"]
    asserted = {ref: dict(rec, BASIS=OP.MATERIAL_SPANS, OPENINGS_TESTED=[]) for ref, rec in basis.items()}
    check = invariants.opening_basis_is_decided_per_wall_line(asserted, lines)
    assert not check["PASS"] and check["RESULT"]["OFFENDERS"]
