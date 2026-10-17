"""Round 5: is the wall there, who says so, and what may be measured from it.

Round 4 left P7757's labelled plan as one 194 m² face holding every room
stamp on it. The partitions are drawn; they are drawn in pieces. So this
round asks whether a fragmented run still describes one physical wall — and
most of what these tests hold is the other half of that question:

    a gap nothing explains stays a gap
    a door in the gap is why the gap is empty
    a wall that ends is not a wall with a hole in it
    an open plan is not several rooms because it has several labels
    and a partition recovered for TOPOLOGY is not blockwork

plus §0's separate point, which is about record-keeping rather than
geometry: a freeze is immutable, and replaying it later is a different act.
"""

from __future__ import annotations

import pytest

from engine import cad_adapter as ad
from engine import cad_measure as cm
from engine import cad_profile as cp
from engine import face_subdivision as fsub
from engine import freeze_manifest as fman
from engine import junction_recovery as jrec
from engine import partition_continuity as pcont
from engine import physical_wall as pwall
from engine import round4_fixtures as r4
from engine import round5_fixtures as fx
from engine import round5_selftest as r5
from engine.cad_fixtures import Builder


def _measured(name):
    case = next(c for c in fx.cases() if c.name.startswith(name))
    nd = ad.normalize(case.decode, source_file=name, source_hash="FIXTURE")
    return nd, cm.measure(nd, cp.build(nd))


def _spans(rep):
    return [s for c in rep.continuity for s in c.spans]


# ------------------------------------------------------ §0 freeze semantics

def test_a_freeze_and_a_replay_are_different_objects():
    m = fman.manifest()
    assert set(m["the_four_objects"]) == {
        "HISTORICAL_ARTIFACT_HASH", "CODE_HASH_AT_FREEZE",
        "DEPENDENCY_HASHES_AT_FREEZE", "CURRENT_REPLAY_HASH"}
    assert all(r["immutable"] for r in m["rounds"])


def test_round_2s_freeze_is_what_round_2_recorded():
    fr = next(f for f in fman.ROUNDS if f.round_name.startswith("ROUND_2"))
    assert fr.synthetic_artifact_hash["ROUND_2_SYNTHETIC_HASH"] == \
        "de1caf07e16e738b3e34dcc5"
    assert fr.project_output_hash["PROJECT_2_CAD_ROUND2_HASH"] == \
        "70e2f4c34a6b1374687fb20f"


def test_a_divergent_replay_is_reported_and_is_not_a_failure():
    """Round 3 rewrote the seed classifier. That shows up HERE, by name."""
    fr = next(f for f in fman.ROUNDS if f.round_name.startswith("ROUND_2"))
    rep = fman.replay(fr)
    assert "ROUND_2_SYNTHETIC_HASH" in rep["diverged"]
    row = rep["rows"]["ROUND_2_SYNTHETIC_HASH"]
    assert row["SYNTHETIC_ARTIFACT_HASH_AT_FREEZE"] == \
        "de1caf07e16e738b3e34dcc5"
    assert row["CURRENT_REPLAY_HASH"] != \
        row["SYNTHETIC_ARTIFACT_HASH_AT_FREEZE"]
    assert "not a failure" in rep["what_divergence_means"]


def test_a_project_output_hash_is_never_replayed():
    for fr in fman.ROUNDS:
        rep = fman.replay(fr)
        for name in fr.project_output_hash:
            assert rep["rows"][name]["status"] == fman.NOT_REPLAYABLE


def test_no_historical_artifact_was_rewritten():
    rows = fman.assert_no_artifact_was_rewritten()
    assert rows


# ------------------------------------------------------- §3, §5 the wall

def test_a_wall_survives_its_faces_being_drawn_in_pieces():
    b = Builder()
    r4._ring(b, 0, 0, 10000, 4000)
    fx._frag_v(b, 4900, 0, 4000, b_gaps=[(1200, 2600)])
    nd = ad.normalize(b.build(), source_file="T", source_hash="T")
    cands = cm.wall_candidates(nd, tuple(cp.build(nd).wall_like_layers()))
    walls = pwall.build(cands, region_id="DR-001")
    wall = next(w for w in walls.walls
                if w.axis == "V" and abs(w.face_a_mm - 4900) < 1)
    assert wall.thickness_mm == 200.0
    assert [s.coverage for s in wall.spans] == [
        pwall.BOTH_FACES, pwall.ONE_FACE_ONLY, pwall.BOTH_FACES]
    rec = wall.record()
    assert rec["MATERIAL_QUANTITY_AUTHORITY"]["established_length_mm"] == \
        2600.0
    assert rec["INFERRED_PHYSICAL_WALL_EXTENT"]["length_mm"] == 4000.0


def test_a_single_unpaired_line_is_never_a_wall():
    b = Builder()
    r4._ring(b, 0, 0, 9000, 5000)
    b.line(500.0, 300.0, 8500.0, 300.0, "ANNO")
    nd = ad.normalize(b.build(), source_file="T", source_hash="T")
    prof = cp.build(nd)
    assert "ANNO" not in prof.wall_like_layers()


def test_a_corner_overhang_is_not_a_missing_face():
    """Every ring wraps its outer face past its inner one. That is a corner."""
    b = Builder()
    r4._ring(b, 0, 0, 8000, 5000)
    nd = ad.normalize(b.build(), source_file="T", source_hash="T")
    cands = cm.wall_candidates(nd, tuple(cp.build(nd).wall_like_layers()))
    walls = pwall.build(cands, region_id="DR-001")
    assert not [s for w in walls.walls for s in w.spans
                if s.coverage != pwall.BOTH_FACES]


# --------------------------------------------------- §4, §7, §8 continuity

def test_one_continuous_face_establishes_the_wall():
    _nd, rep = _measured("A_")
    spans = [s for s in _spans(rep) if s.coverage == pwall.ONE_FACE_ONLY]
    assert spans
    assert spans[0].verdict == pcont.ESTABLISHED
    assert spans[0].topology_authority == pcont.TOPOLOGY_VALIDATED
    assert spans[0].material_authority == pcont.MATERIAL_CANDIDATE


def test_an_unexplained_collinear_gap_stays_a_gap():
    _nd, rep = _measured("F_")
    verdicts = {s.verdict for s in _spans(rep)}
    assert pcont.UNRESOLVED_GAP in verdicts
    assert not [s for s in _spans(rep)
                if s.verdict == pcont.UNRESOLVED_GAP and s.may_subdivide]
    assert rep.counts()["release_eligible"] == 0


def test_there_is_no_bridge_collinear_gap_rule():
    import pathlib

    src = pathlib.Path("engine/partition_continuity.py").read_text(
        encoding="utf-8")
    assert "def bridge" not in src
    params = pcont.frozen_parameters()
    assert set(params["RAISING_TOKENS"]) == {pcont.EV_E_CROSSES,
                                             pcont.EV_D_T_JUNCTION}
    assert pcont.EV_A_COLLINEAR in params["CONSEQUENCES_OF_COLLINEARITY"]


def test_a_door_in_the_gap_is_why_the_gap_is_empty():
    _nd, rep = _measured("C_")
    spans = [s for s in _spans(rep)
             if s.verdict == pcont.OPENING_INTERRUPTION]
    assert spans
    assert all(s.material_authority == pcont.MATERIAL_ABSENT for s in spans)
    assert not any(s.may_subdivide for s in spans)


def test_no_material_is_ever_recovered_across_an_opening():
    """Across every one of the twenty-three drawings, without exception."""
    for case in fx.cases():
        nd = ad.normalize(case.decode, source_file=case.name,
                          source_hash="FIXTURE")
        rep = cm.measure(nd, cp.build(nd))
        for s in _spans(rep):
            if s.verdict == pcont.OPENING_INTERRUPTION:
                assert s.material_authority == pcont.MATERIAL_ABSENT, \
                    f"{case.name} {s.span_id}"
                assert not s.may_subdivide, f"{case.name} {s.span_id}"


# ------------------------------------------------- §6 the two authorities

def test_topology_authority_does_not_grant_material_authority():
    _nd, rep = _measured("W_")
    released = [r for r in rep.rows
                if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]
    assert released
    withheld = [r for r in released
                if r.material_authority != pcont.MATERIAL_ESTABLISHED]
    assert withheld, "a recovered room must not silently gain blockwork"
    assert withheld[0].record()["material_boq_status"] == \
        "MATERIAL_RELEASE_BLOCKED"


def test_a_supported_span_may_subdivide_and_may_not_release():
    assert pcont.TOPOLOGY_SUPPORTED != pcont.TOPOLOGY_VALIDATED
    row = pcont.Continuation(
        span_id="X", wall_id="W", region_id="R", axis="V", lo=0.0, hi=100.0,
        coverage=pwall.NEITHER_FACE, verdict=pcont.SUPPORTED,
        topology_authority=pcont.TOPOLOGY_SUPPORTED,
        material_authority=pcont.MATERIAL_CANDIDATE)
    assert row.may_subdivide
    assert not row.may_release


# ------------------------------------------------ §12, §13 junctions

@pytest.mark.parametrize("miss,recovered", [(2.0, True), (1500.0, False)])
def test_a_junction_is_recovered_by_a_derived_tolerance(miss, recovered):
    b = Builder()
    r4._ring(b, 0, 0, 10000, 6000)
    fx._frag_v(b, 4900, 0, 6000 - miss)
    nd = ad.normalize(b.build(), source_file="T", source_hash="T")
    cands = cm.wall_candidates(nd, tuple(cp.build(nd).wall_like_layers()))
    walls = pwall.build(cands, region_id="DR-001")
    rep = jrec.recover(walls.walls, region_id="DR-001", candidates=cands)
    got = [j for j in rep.junctions if "V-4900" in j.wall_id
           and j.separation_mm > 0]
    assert bool([j for j in got if j.is_recovered]) is recovered
    for j in got:
        assert j.tolerance_mm >= j.drafting_resolution_mm
        assert j.record()["tolerance_came_from"]["local_wall_thickness_mm"]


def test_the_tolerance_is_derived_and_reported_not_a_client_constant():
    params = jrec.frozen_parameters()
    assert params["TOLERANCE_RULE"].startswith("max(drafting_resolution_mm")
    assert "no_client_constant" in params["why"]
    import pathlib

    src = pathlib.Path("engine/junction_recovery.py").read_text(
        encoding="utf-8")
    assert "7757" not in src


def test_a_column_is_observed_and_never_becomes_a_room():
    _nd, rep = _measured("I_")
    cols = [c for r in rep.junctions for c in r.columns]
    assert cols
    released = [r for r in rep.rows
                if r._release()["status"] == "RELEASE_ELIGIBLE_GEOMETRY"]
    for r in released:
        assert r.enclosure.area_m2 > 1.0


# ------------------------------------- §9, §10, §11 subdivision and semantics

def test_labels_diagnose_undersegmentation_and_never_create_geometry():
    _nd, rep = _measured("K_")
    diag = [d for r in rep.subdivisions for d in r.diagnoses]
    assert len(diag) == 1
    assert diag[0].outcome == fsub.ONE_PHYSICAL_SPACE
    assert diag[0].record()["flag"] == fsub.POSSIBLE_UNDERSEGMENTED
    assert rep.counts()["release_eligible"] == 0
    assert rep.counts()["functional_zone_groups"] == 1


def test_an_unresolved_interior_leaves_the_partition_unresolved():
    _nd, rep = _measured("V_")
    diag = [d for r in rep.subdivisions for d in r.diagnoses]
    assert diag and diag[0].outcome == fsub.ROOM_PARTITION_UNRESOLVED
    assert diag[0].unresolved_internal_hypotheses
    assert rep.counts()["release_eligible"] == 0


def test_a_face_is_never_subdivided_by_its_labels():
    for case in fx.cases():
        nd = ad.normalize(case.decode, source_file=case.name,
                          source_hash="FIXTURE")
        rep = cm.measure(nd, cp.build(nd))
        for r in rep.subdivisions:
            for d in r.diagnoses:
                if d.outcome == fsub.MULTIPLE_PHYSICAL_SPACES:
                    assert d.supported_internal_partitions, case.name


def test_a_recovered_side_is_boundary_and_is_not_measurable_material():
    _nd, rep = _measured("A_")
    held = [r for r in rep.rows if r.recovered_boundary]
    assert held
    q = held[0].quantities
    assert q["RECOVERED_BOUNDARY_LENGTH_MM"] > 0
    assert (q["MATERIAL_AUTHORITY_ESTABLISHED_LENGTH_MM"]
            < q["MATERIAL_PRESENT_LENGTH_MM"])
    assert "absent along every recovered span" in q["never"]


def test_what_may_subdivide_a_face_is_stated():
    assert "not a label" in fsub.WHAT_MAY_SUBDIVIDE
    assert "expected room count" in fsub.WHAT_MAY_SUBDIVIDE


# ------------------------------------------------------------- the freeze

def test_the_twenty_three_round5_cases_hold():
    rep = r5.assert_frozen()
    assert rep["cases"] == 23
    assert rep["failed"] == 0
    assert rep["required_results_held"] is True


def test_rounds_two_to_four_still_hold_under_round_five():
    from engine import round2_selftest as r2
    from engine import round3_selftest as r3
    from engine import round4_selftest as r4st

    assert r2.assert_frozen()["failed"] == 0
    assert r3.assert_frozen()["failed"] == 0
    assert r4st.assert_frozen()["failed"] == 0


def test_the_freeze_hashes_are_stable():
    for fn in (r5.freeze_hash, fman.schema_hash, pwall.wall_band_hash,
               pcont.continuity_hash, jrec.junction_hash,
               fsub.subdivision_hash):
        assert fn() == fn() and len(fn()) == 24


def test_no_tolerance_was_invented_this_round():
    from engine import space_enclosure as enc

    assert pwall.MIN_WALL_MM == cp.MIN_WALL_THICKNESS_MM
    assert pwall.MAX_WALL_MM == cp.MAX_WALL_THICKNESS_MM
    assert pwall.MIN_FACE_OVERLAP_MM == cp.MIN_FACE_OVERLAP_MM
    assert pwall.JOIN_MM == enc.JUNCTION_REACH_MM
    assert pwall.COLLINEAR_TOL_MM == enc.COLLINEAR_JOIN_MM
