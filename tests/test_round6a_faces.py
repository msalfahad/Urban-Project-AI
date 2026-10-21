"""Round 6A: which face a room stops at, and what a missing site means.

The kitchen measured 2.20 x 2.55 m because the flood stopped at the front
of a worktop. Nothing about that is a tolerance. These tests hold the two
statements that fix it — a wall is where the spaces stop, and a line with
floor on both sides bounds nothing — and the two that keep it honest: a
polygon names the basis it was measured on, and a drawing with no site
boundary still knows what is outside its building.
"""

from __future__ import annotations

import io
import tokenize

import pytest

from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_profile as cp
from engine import cad_space_role as srole
from engine import freeze_manifest as fman
from engine import interior_exterior as iexr
from engine import physical_wall as pwall
from engine import round6a_fixtures as fx
from engine import round6a_selftest as r6a
from engine import semantic_seed as seeds_mod
from engine import wall_face_ownership as wface


def _code(module):
    """Source with docstrings, comments and string literals removed."""
    out = []
    for tok in tokenize.generate_tokens(
            io.StringIO(open(module.__file__, encoding="utf-8").read())
            .readline):
        if tok.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        out.append(tok.string)
    return " ".join(out)


def _measured(name):
    case = next(c for c in fx.cases() if c.name.startswith(name))
    nd = ad.normalize(case.decode, source_file=name, source_hash="FIXTURE")
    sem = seeds_mod.classify(nd.texts)
    return cm.measure(nd, cp.build(nd), semantic=sem)


# ---------------------------------------------------- §10 the nine cases

@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_every_round_6a_case_holds(case):
    res = r6a.check(case)
    assert res.passed, f"{case.name}: {res.failures} observed={res.observed}"


def test_the_round_6a_requirements_are_frozen():
    rep = r6a.assert_frozen()
    assert rep["cases"] == 9
    assert rep["passed"] == 9


# --------------------------- §2 a wall is where the spaces stop

def test_a_pair_with_a_room_between_its_faces_is_not_a_wall():
    rep = _measured("A_TWO_ROOMS_SHARE_ONE_WALL")
    arr = wface.arrangement(
        [c for wr in () for c in wr], region_id="DR-001")  # empty is safe
    assert arr.at(0.0, 0.0) == wface.SIDE_OPEN
    assert pwall.EV_SPACES_STOP_AT_BOTH_FACES in pwall.PRIORITY
    assert rep.rows


def test_the_pair_test_reads_coordinates_not_polygons():
    """A two-millimetre drafting gap must not turn a wall into a room."""
    src = _code(wface)
    assert "widths_between" in src
    assert "width_beyond" in src
    assert wface.MAX_WALL_MM == wface.cprofile.MAX_WALL_THICKNESS_MM


def test_the_evidence_order_puts_a_hosted_opening_first():
    assert pwall.PRIORITY[0] == pwall.EV_HOSTS_AN_OPENING
    assert pwall.PRIORITY.index(pwall.EV_SPACES_STOP_AT_BOTH_FACES) > \
        pwall.PRIORITY.index(pwall.EV_CAPPED_BOTH_ENDS)
    assert pwall.PRIORITY.index(pwall.EV_SPACES_STOP_AT_BOTH_FACES) < \
        pwall.PRIORITY.index(pwall.EV_THICKNESS_MODE)


def test_a_wall_may_own_several_disjoint_stretches_of_one_line():
    """One drawn line runs past three rooms; it is three walls, not one."""
    assert pwall._intersect([(0.0, 100.0), (200.0, 400.0)],
                            [(50.0, 300.0)]) == [(50.0, 100.0),
                                                 (200.0, 300.0)]
    assert pwall._subtract([(0.0, 1000.0)], [(400.0, 600.0)]) == \
        [(0.0, 400.0), (600.0, 1000.0)]


# --------------------------------- §5 a line inside a room bounds nothing

def test_a_counter_front_is_not_where_the_floor_ends():
    rep = _measured("C_FINISH_AND_DETAIL_LINES_BESIDE_A_WALL")
    dropped = [d for o in rep.ownership for d in o.dropped]
    assert dropped, "no line was found standing inside a space"
    assert all(d.why == wface.NOT_BOUNDING_INSIDE_A_SPACE for d in dropped)


def test_a_strip_is_a_wall_only_when_both_its_lines_are_one_band():
    src = _code(wface)
    assert "_band_pairs" in src
    assert "_side" in src


def test_no_layer_is_trusted_or_distrusted():
    src = _code(wface)
    for forbidden in ("layer", "COUNTER", "FURNITURE", "7757"):
        assert forbidden not in src


# --------------------------------------- §4 the basis is named, not switched

def test_every_basis_this_engine_knows_is_named():
    assert set(wface.BASES) == {
        wface.CLEAR_INTERNAL_FINISH_FACE, wface.STRUCTURAL_FACE,
        wface.WALL_CENTERLINE, wface.EXTERNAL_FACE,
        wface.CLEAR_FACE_NOT_ESTABLISHED, wface.BASIS_NOT_ESTABLISHED}
    assert all(b in wface.WHAT_EACH_BASIS_IS for b in wface.BASES)


def test_a_released_polygon_names_every_side_it_has():
    rep = _measured("E_FOUR_WALLS_FOUR_THICKNESSES")
    released = [r.clear for r in rep.rows
                if r.clear is not None and r.clear.basis_established]
    assert released
    for c in released:
        assert c.boundary_faces
        for f in c.boundary_faces:
            assert f.basis == wface.CLEAR_INTERNAL_FINISH_FACE
            assert f.cad_provenance or f.face_id
        rec = c.record()
        assert rec["measurement_basis"] == wface.CLEAR_INTERNAL_FINISH_FACE
        assert rec["boundary_face_ids"] or rec["wall_band_ids"]


def test_a_side_nobody_can_attribute_blocks_the_release():
    """NOT_ESTABLISHED is a verdict, not a gap to be filled in."""
    assert wface.WHAT_EACH_BASIS_IS[wface.BASIS_NOT_ESTABLISHED]
    rep = _measured("I_OUTSIDE_THE_ENVELOPE_WITH_NO_SITE_RING")
    for r in rep.rows:
        c = r.clear
        if c is None or c.basis_established:
            continue
        assert c.basis == wface.BASIS_NOT_ESTABLISHED
        assert c.notes.get("why_not_released")


# ------------------------------------ §3 ownership, and opposite faces

def test_one_wall_gives_opposite_faces_to_the_two_rooms_it_separates():
    rep = _measured("H_ONE_WALL_TWO_DIFFERENT_CLEAR_WIDTHS")
    by_band: dict = {}
    for r in rep.rows:
        c = r.clear
        if c is None or not c.basis_established:
            continue
        for f in c.boundary_faces:
            if f.wall_band_id:
                by_band.setdefault(f.wall_band_id, set()).add(f.face_id)
    assert any(len(v) >= 2 for v in by_band.values()), \
        "no wall gave its two opposite faces to two different spaces"


def test_a_face_knows_which_side_it_faces():
    rep = _measured("A_TWO_ROOMS_SHARE_ONE_WALL")
    faces = [f for o in rep.ownership for f in o.faces]
    assert faces
    assert {f.side for f in faces} <= {wface.SPACE_LEFT, wface.SPACE_RIGHT}
    assert all(f.interior_exterior in wface.OWNERSHIP for f in faces)


# ------------------------------- §9 the building and the site are two things

def test_the_building_question_is_not_the_site_question():
    assert set(iexr.BUILDING_VERDICTS) == {
        iexr.INSIDE_BUILDING, iexr.OUTSIDE_BUILDING, iexr.BUILDING_UNKNOWN}
    assert set(iexr.SITE_VERDICTS) == {
        iexr.SITE_ESTABLISHED, iexr.SITE_UNKNOWN}
    assert iexr.frozen_parameters()["why"][
        "a_missing_site_is_not_an_interior"]


def test_no_site_ring_does_not_make_outside_the_building_interior():
    rep = _measured("I_OUTSIDE_THE_ENVELOPE_WITH_NO_SITE_RING")
    roles = rep.space_roles
    assert roles is not None
    assert all(m.site is None for m in roles.envelopes.values()), \
        "a site boundary was invented where the fixture drew none"
    for v in roles.verdicts:
        if v.role == srole.EXTERIOR_EXTENT_UNRESOLVED:
            assert not v.is_interior


def test_exterior_extent_unresolved_is_a_role_of_its_own():
    assert srole.EXTERIOR_EXTENT_UNRESOLVED in srole.ROLES
    assert srole.EXTERIOR_EXTENT_UNRESOLVED in srole.EXTERIOR_ROLES
    assert srole.frozen_parameters()["EXTERIOR_EXTENT_UNRESOLVED"]


# ------------------------------------------- the record keeping (§0 again)

def test_round_6_steps_1_to_5_are_in_the_manifest_and_immutable():
    fr = next(f for f in fman.ROUNDS
              if f.round_name == "ROUND_6_GEOMETRY_STEPS_1_TO_5")
    assert fr.commit == "bc8e96f"
    assert fr.code_hashes_at_freeze["PHYSICAL_WALL_BAND_HASH"] == \
        "b6d79d2b5c5e2c13eb5d546d"
    assert fr.record()["immutable"]


def test_every_divergence_round_6a_causes_was_predicted():
    for fr in fman.ROUNDS:
        rec = fman.replay(fr)
        assert not rec["UNPREDICTED_DIVERGENCE"], rec["round"]


def test_no_historical_artifact_was_rewritten_by_round_6a():
    fman.assert_no_artifact_was_rewritten()
