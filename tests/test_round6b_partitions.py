"""Round 6B: one drawn line, three different authorities.

A 100 mm block wall drawn once is still a wall; a worktop drawn once is
still a worktop. Telling them apart needs POSITIVE architectural evidence,
and whatever the answer, a line has no thickness — so the tests that
matter most here are the ones that hold when the answer is YES:

    the topology may be established
    the clear area may not, unless the face is found independently
    the MATERIAL never is, and that is not a threshold
"""

from __future__ import annotations

import io
import tokenize

import pytest

from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_profile as cp
from engine import freeze_manifest as fman
from engine import round6b_fixtures as fx
from engine import round6b_selftest as r6b
from engine import semantic_seed as seeds_mod
from engine import single_line_partition as slp
from engine import wall_face_ownership as wface


def _code(module):
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
    return cm.measure(nd, cp.build(nd),
                      semantic=seeds_mod.classify(nd.texts))


# ------------------------------------------------------- §7 the twelve cases

@pytest.mark.parametrize("case", fx.cases(), ids=lambda c: c.name)
def test_every_round_6b_case_holds(case):
    res = r6b.check(case)
    assert res.passed, f"{case.name}: {res.failures} observed={res.observed}"


def test_the_round_6b_requirements_are_frozen():
    rep = r6b.assert_frozen()
    assert rep["cases"] == 12
    assert rep["passed"] == 12


# ------------------------------- §1 the three authorities are not the same

def test_the_three_authorities_are_three_different_things():
    assert slp.TOPOLOGY_ESTABLISHED != slp.CLEAR_FACE_ESTABLISHED
    assert slp.CLEAR_FACE_ESTABLISHED != slp.MATERIAL_ESTABLISHED
    assert set(slp.RESULTS) == {slp.RESULT_A, slp.RESULT_B, slp.RESULT_C}
    assert all(r in slp.WHAT_EACH_RESULT_IS for r in slp.RESULTS)


def test_the_three_results_are_never_collapsed():
    """§4. Each one has to be reachable, or the distinction is decorative."""
    a = _measured("I_CLEAR_FACE_FROM_CONTINUATION")
    b = _measured("H_TOPOLOGY_ESTABLISHED_THICKNESS_UNKNOWN")
    c = _measured("G_AN_ISOLATED_DECORATIVE_LINE")
    seen = set()
    for rep in (a, b, c):
        for pr in rep.partitions:
            seen |= {cand.status for cand in pr.candidates}
    assert slp.RESULT_A in seen
    assert slp.RESULT_B in seen
    assert slp.RESULT_C in seen


# --------------------------------------- §3 positive evidence, never circular

def test_dividing_a_region_is_not_evidence():
    for name in ("C_A_WORKTOP", "D_A_DIMENSION_LINE", "G_AN_ISOLATED"):
        rep = _measured(name)
        est = [c for pr in rep.partitions for c in pr.candidates
               if c.establishes_topology]
        assert not est, f"{name} accepted {[c.evidence for c in est]}"


def test_spanning_the_room_is_what_a_fitting_does():
    """Wall-to-wall may support a partition; it may never establish one."""
    assert slp.EV_TERMINATES_AT_ESTABLISHED_WALLS in slp.SUPPORTING
    assert slp.EV_TERMINATES_AT_ESTABLISHED_WALLS not in slp.STRONG
    assert slp.frozen_parameters()["why"]["wall_to_wall_is_not_strong"]


def test_a_partition_needs_one_strong_token_and_two_in_total():
    assert slp.MIN_TOKENS == 2
    rep = _measured("A_ONE_PARTITION_LINE_BETWEEN_TWO_WALLS")
    for pr in rep.partitions:
        for c in pr.candidates:
            if not c.establishes_topology:
                continue
            assert any(t in slp.STRONG for t in c.evidence)
            assert len(c.evidence) >= slp.MIN_TOKENS


def test_no_room_size_rule_and_no_project_coordinate():
    src = _code(slp)
    assert "7757" not in src
    assert "area" not in src
    assert slp.frozen_parameters()["why"]["no_room_size_rule"]


# ------------------------------------- §6 the material rule, which is absolute

def test_a_partition_never_establishes_material():
    for case in fx.cases():
        rep = r6b.check(case)
        assert rep.passed or "material" not in " ".join(rep.failures)
    rep = _measured("K_A_TOPOLOGY_ONLY_PARTITION_MAKES_NO_MATERIAL")
    for pr in rep.partitions:
        for c in pr.candidates:
            assert c.material_authority == slp.MATERIAL_NOT_ESTABLISHED
            assert c.record()["material_contribution_m"] == 0.0


def test_partition_length_is_taken_off_the_measurable_wall():
    rep = _measured("L_SEPARATED_ROOMS_WITH_NO_BLOCKWORK_EITHER_SIDE")
    seen = False
    for r in rep.rows:
        q = r.quantities
        held = q.get("SINGLE_LINE_PARTITION_LENGTH_MM", 0.0)
        if not held:
            continue
        seen = True
        assert q["MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM"] <= (
            q["SPACE_BOUNDARY_LENGTH_MM"] - held + 1.0)
    assert seen, "no space was bounded by a partition at all"


def test_the_material_rule_is_stated_where_it_is_enforced():
    assert slp.frozen_parameters()["why"][
        "material_is_never_established_here"]
    from engine import room_partition_graph as rpg

    src = open(rpg.__file__, encoding="utf-8").read()
    assert "SINGLE_LINE_PARTITION_LENGTH_MM" in src
    assert "_partition_length_mm" in src


# -------------------------------------- §5 the clear face is found, not assumed

def test_a_centreline_is_never_substituted_for_a_face():
    src = _code(slp)
    for forbidden in ("/ 2", "* 0.5", "centre", "center"):
        assert forbidden not in src


def test_the_clear_face_comes_from_evidence_outside_the_line():
    assert set(slp.FACE_EVIDENCE) == {
        slp.FACE_FROM_A_CONTINUING_BAND, slp.FACE_FROM_A_DIMENSION,
        slp.FACE_FROM_A_JAMB}
    rep = _measured("I_CLEAR_FACE_FROM_CONTINUATION")
    good = [c for pr in rep.partitions for c in pr.candidates
            if c.establishes_clear_face]
    assert good
    for c in good:
        assert c.face_evidence
        assert c.clear_face_mm is not None


def test_removing_the_evidence_removes_the_clear_face():
    rep = _measured("J_THE_SAME_GEOMETRY_WITHOUT_THE_EVIDENCE")
    assert not [c for pr in rep.partitions for c in pr.candidates
                if c.establishes_clear_face]


def test_a_space_held_by_an_unknown_thickness_does_not_release_its_area():
    rep = _measured("H_TOPOLOGY_ESTABLISHED_THICKNESS_UNKNOWN")
    held = [r for r in rep.rows if r.clear is not None
            and r.clear.basis == wface.CLEAR_FACE_NOT_ESTABLISHED]
    assert held, "the fixture's partition established no topology at all"
    for r in held:
        assert not r.clear.basis_established
        assert r.clear.topology_established
        assert r.clear.notes.get("why_not_released")


# ------------------------------------------------ the record keeping (§0 again)

def test_round_6a_is_in_the_manifest_and_immutable():
    fr = next(f for f in fman.ROUNDS
              if f.round_name == "ROUND_6A_WALL_FACE_OWNERSHIP")
    assert fr.commit == "b646fb6"
    assert fr.record()["immutable"]


def test_every_divergence_round_6b_causes_was_predicted():
    for fr in fman.ROUNDS:
        rec = fman.replay(fr)
        assert not rec["UNPREDICTED_DIVERGENCE"], rec["round"]


def test_no_historical_artifact_was_rewritten_by_round_6b():
    fman.assert_no_artifact_was_rewritten()
