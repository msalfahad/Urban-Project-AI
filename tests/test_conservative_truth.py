"""Snap topology, two recalls, the blind sample, and the blob work list.

Four instruments, each closing a specific way of overclaiming:
  a tolerance called safe because the AREA barely moved;
  one recall number covering both what is reachable and what is measured;
  a 434.8 m population resting on one classifier nobody sampled;
  a work list whose predicted effects read as measured ones.
"""

import pytest
from shapely.geometry import box

from engine import blob_causes as bc
from engine import snap_topology as stp
from engine import space_recall as sr
from engine import stroke_sample as ssm
from engine import unpaired_strokes as us


# --- §7 snap topology ----------------------------------------------------

def _two_near(gap):
    return [box(0.0, 0.0, 1000.0, 200.0),
            box(1000.0 + gap, 0.0, 2000.0, 200.0)]


def test_area_is_not_the_test_and_the_report_says_so():
    r = stp.diff(_two_near(0.02), fine_mm=0.01, coarse_mm=0.05,
                 noise_floor_mm=0.01).record()
    assert "no area cost" in r["why_area_is_not_the_test"]
    assert "which rooms exist" in r["why_area_is_not_the_test"]


def test_a_join_within_the_measured_noise_floor_is_benign():
    r = stp.diff(_two_near(0.004), fine_mm=0.001, coarse_mm=0.05,
                 noise_floor_mm=0.01)
    assert r.joins and all(j.join_class == stp.NOISE_JOIN for j in r.joins)
    assert r.coarse_is_defensible
    assert "one node recorded twice" in r.joins[0].why


def test_a_join_beyond_the_noise_floor_with_no_patch_is_false():
    r = stp.diff(_two_near(0.02), fine_mm=0.001, coarse_mm=0.05,
                 noise_floor_mm=0.01)
    assert r.joins and r.joins[0].join_class == stp.FALSE_JOIN
    assert not r.coarse_is_defensible
    assert "invented a wall" in r.joins[0].why
    assert "JUNCTION_PATCH" in r.record()["verdict"]


class _Patch:
    def __init__(self, pid, poly):
        self.patch_id, self.polygon = pid, poly
        self.is_validated = True


def test_a_join_a_validated_patch_covers_is_valid_but_should_come_from_it():
    r = stp.diff(_two_near(0.02), fine_mm=0.001, coarse_mm=0.05,
                 noise_floor_mm=0.01,
                 patches=[_Patch("JP-1", box(990.0, 0.0, 1010.0, 200.0))])
    assert r.joins[0].join_class == stp.VALID_JUNCTION
    assert "rather than from the rounding" in r.joins[0].why
    assert r.coarse_is_defensible


def test_with_no_measured_floor_a_join_is_unresolved_not_benign():
    r = stp.diff(_two_near(0.02), fine_mm=0.001, coarse_mm=0.05,
                 noise_floor_mm=None)
    assert r.joins[0].join_class == stp.UNRESOLVED_JOIN
    assert not r.coarse_is_defensible


def test_shapes_the_coarse_grid_does_not_merge_produce_no_join():
    r = stp.diff([box(0.0, 0.0, 1000.0, 200.0),
                  box(5000.0, 0.0, 6000.0, 200.0)],
                 fine_mm=0.01, coarse_mm=0.05, noise_floor_mm=0.01)
    assert r.joins == []
    assert r.coarse_is_defensible


# --- §12 two recalls ------------------------------------------------------

class _Cand:
    def __init__(self, gid, area=20.0,
                 role="OCCUPIABLE_SPACE_CANDIDATE",
                 basis="CLEAR_INTERNAL_FINISH_FACE"):
        self.space_geometry_id, self.area_m2 = gid, area
        self.geometry_role, self.measurement_basis = role, basis


def _recall(**kw):
    base = dict(candidates=[_Cand("SG-1")],
                labels_inside={"SG-1": ("BED-01",)}, in_scope_spaces=17)
    base.update(kw)
    cands = base.pop("candidates")
    return sr.assess(cands, **base)


def test_a_clean_single_label_component_is_release_eligible():
    r = _recall()
    assert r.diagnostic_count == 1
    assert r.release_count == 1


def test_unestablished_material_blocks_release_but_not_diagnostic():
    # This is BED-01's actual situation: a plausible polygon that no
    # quantity may be built on.
    r = _recall(dependency_of=lambda c: {
        "depends_on_unestablished_material": True,
        "unestablished_boundary_length_m": 5.104})
    assert r.diagnostic_count == 1
    assert r.release_count == 0
    got = r.record()
    assert got["the_gap_is_the_hypothesis"]["spaces"] == 1
    assert sr.BLOCK_UNESTABLISHED in got["block_reasons"]
    assert got["single_label_but_blocked"][0][
        "unestablished_boundary_m"] == pytest.approx(5.104)


def test_a_diagnostic_portal_blocks_release():
    r = _recall(release_of=lambda c: {
        "release_class": "DIAGNOSTIC_PARTITION_BARRIER"})
    assert r.release_count == 0
    assert sr.BLOCK_DIAGNOSTIC_BARRIER in r.record()["block_reasons"]


def test_a_multi_label_component_counts_in_neither():
    r = _recall(labels_inside={"SG-1": ("BED-01", "BTH-03")})
    assert r.diagnostic_count == 0
    assert r.release_count == 0


def test_a_wrong_basis_blocks_release():
    r = _recall(candidates=[_Cand("SG-1", basis="SOMETHING_ELSE")])
    assert r.release_count == 0
    assert sr.BLOCK_NO_BASIS in r.record()["block_reasons"]


def test_a_shaft_is_not_an_occupiable_space():
    r = _recall(candidates=[_Cand("SG-1", role="SHAFT_CANDIDATE")])
    assert r.release_count == 0
    assert sr.BLOCK_ROLE in r.record()["block_reasons"]


def test_the_two_recalls_state_their_different_bases():
    got = _recall().record()
    assert "within reach, not how much is measured" in \
        got[sr.DIAGNOSTIC_RECALL]["basis"]
    assert "production-level evidence" in got[sr.RELEASE_RECALL]["basis"]
    assert "let a guess count as a measured room" in \
        got["the_gap_is_the_hypothesis"]["why"]


# --- §8 / §9 the single-line audit and its blind sample ------------------

def test_the_existence_claim_is_separate_from_the_geometry_claim():
    assert us.SINGLE_LINE_EXISTENCE_SUPPORTED != \
        us.SINGLE_LINE_GEOMETRY_COMPLETE
    # The old name now resolves to the WEAKER claim, so any caller still
    # using it gets the correct one.
    assert us.CONFIRMED_SINGLE_LINE_WALL == \
        us.SINGLE_LINE_EXISTENCE_SUPPORTED
    assert us.SINGLE_LINE_EXISTENCE_SUPPORTED in us.EXISTENCE_ONLY_CLASSES
    assert us.GEOMETRY_REQUIREMENTS


def _one(**kw):
    base = dict(length=2000.0, dup=False, near_gap=None, support=0.9,
                peers=0, pen_match=True, pen_pt=1.14, parallel_mm=None,
                meets=2)
    base.update(kw)
    return us._classify_one(**base)


def test_a_parallel_face_nearby_means_it_is_not_single_line():
    # The one thing a single-line wall is defined by NOT having. The old
    # test looked only for collinear neighbours on the same line.
    cls, why = _one(parallel_mm=51.0)
    assert cls == us.STROKE_UNRESOLVED
    assert "one side of a candidate PAIR" in why


def test_the_wrong_pen_does_not_support_a_wall_and_is_not_non_wall_either():
    cls, why = _one(pen_match=False, pen_pt=0.36)
    assert cls == us.STROKE_UNRESOLVED
    assert "UNRESOLVED and not non-wall" in why


def test_a_run_longer_than_any_villa_wall_is_a_grid_or_border_line():
    cls, why = _one(length=50_000.0)
    assert cls == us.ANNOTATION_OR_DETAIL
    assert "grid line" in why


def test_a_run_nothing_meets_is_not_part_of_a_wall_network():
    cls, why = _one(meets=0)
    assert cls == us.NON_WALL_GEOMETRY
    assert "part of a wall network" in why


def test_all_four_requirements_together_support_existence():
    cls, why = _one()
    assert cls == us.SINGLE_LINE_EXISTENCE_SUPPORTED
    assert "may NOT create material geometry" in why
    assert "TOPOLOGY_SEPARATOR_HYPOTHESIS" in why


class _S:
    def __init__(self, i, axis, fixed, a, b, cls, pen=1.14, sup=1.0):
        self.stroke_id, self.axis, self.fixed_mm = i, axis, fixed
        self.start_mm, self.end_mm, self.stroke_class = a, b, cls
        self.stroke_width_pt, self.raster_support = pen, sup
        self.collinear_neighbours = 0
        self.nearest_band_id, self.nearest_band_gap_mm = "", None
        self.evidence = ("DRAWN_WITH_THE_WALL_PEN",)

    @property
    def length_mm(self):
        return self.end_mm - self.start_mm


def test_the_sample_is_deterministic_for_a_given_seed():
    pop = [_S(f"VS-{i:04d}", "H", 100.0 * i, 0.0, 4000.0,
              us.SINGLE_LINE_EXISTENCE_SUPPORTED) for i in range(20)]
    a = ssm.draw(pop, population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED,
                 seed="AR-00")
    b = ssm.draw(pop, population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED,
                 seed="AR-00")
    assert [m.stroke_id for m in a.members] == [m.stroke_id
                                                for m in b.members]


def test_a_different_seed_draws_a_different_sample():
    pop = [_S(f"VS-{i:04d}", "H", 100.0 * i, 0.0, 4000.0,
              us.SINGLE_LINE_EXISTENCE_SUPPORTED) for i in range(20)]
    a = ssm.draw(pop, population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED,
                 seed="A")
    b = ssm.draw(pop, population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED,
                 seed="B")
    assert [m.stroke_id for m in a.members] != [m.stroke_id
                                                for m in b.members]


def test_the_sample_reports_evidence_and_refuses_a_verdict():
    pop = [_S("VS-1", "H", 100.0, 0.0, 4000.0,
              us.SINGLE_LINE_EXISTENCE_SUPPORTED)]
    got = ssm.draw(pop,
                   population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED
                   ).record()
    m = got["members"][0]
    assert m["verdict"] == "NOT_ADJUDICATED_HERE"
    assert "agreement with the list" in m["why_no_verdict"]
    assert got["blind"]
    assert "not consulted" in got["what_blind_means"]


def test_strata_with_no_members_are_named_not_hidden():
    pop = [_S("VS-1", "H", 100.0, 0.0, 4000.0,
              us.SINGLE_LINE_EXISTENCE_SUPPORTED)]
    got = ssm.draw(pop,
                   population_class=us.SINGLE_LINE_EXISTENCE_SUPPORTED
                   ).record()
    assert set(got["notes"]["strata_with_no_members"]) <= set(ssm.STRATA)
    assert ssm.SHORT in got["notes"]["strata_with_no_members"]


# --- §14 the blob work list ----------------------------------------------

class _Leak:
    def __init__(self, lid, a, b, gid="SG-1", bands=(), portals=(),
                 strokes=(), width=100.0):
        self.leak_id, self.space_a, self.space_b = lid, a, b
        self.space_geometry_id = gid
        self.bands_at_frontier = tuple(bands)
        self.portals_at_frontier = tuple(portals)
        self.strokes_at_aperture = tuple(strokes)
        self.unpaired_strokes_at_frontier = tuple(strokes)
        self.passage_width_mm = width


def test_a_separator_with_nothing_drawn_is_low_confidence():
    t = bc.build([_Leak("LK-1", "A", "B")],
                 labels_inside={"SG-1": ("A", "B")})
    row = t.record()["ranked"][0]
    assert row["current_representation"] == bc.REP_NOTHING
    assert row["confidence"] == bc.CONF_LOW
    assert "nothing to recover" in row["why"]


def test_a_fragmented_mate_is_medium_confidence_and_flagged():
    t = bc.build([_Leak("LK-1", "A", "B", strokes=("VS-1",))],
                 labels_inside={"SG-1": ("A", "B")},
                 strokes=[_S("VS-1", "H", 0.0, 0.0, 100.0,
                             us.FRAGMENTED_MATE)])
    row = t.record()["ranked"][0]
    assert row["current_representation"] == bc.REP_FRAGMENTED
    assert row["fragmented_mate_involved"]
    assert row["confidence"] == bc.CONF_MEDIUM


def test_an_unmeasured_effect_is_never_reported_as_measured():
    t = bc.build([_Leak("LK-1", "A", "B")],
                 labels_inside={"SG-1": ("A", "B")})
    assert t.record()["ranked"][0][
        "effect_when_repaired"] == bc.NOT_MEASURED
    assert "wish list" in t.record()["effect_column"]


def test_a_measured_counterfactual_is_quoted_with_its_verdict():
    class _P:
        patch_id = "JP-1"
        is_validated = True
        gap_repair_class = "REPAIR_IS_JUNCTION_ASSEMBLY"
        provenance = {"leak_id": "LK-1"}
    t = bc.build([_Leak("LK-1", "A", "B")],
                 labels_inside={"SG-1": ("A", "B")}, patches=[_P()],
                 counterfactual={"repairs_applied": ["JP-1"],
                                 "delta": {"single_room_candidates": 0,
                                           "largest_blob_labels": 0},
                                 "verdict": "REPAIRS_CHANGED_NOTHING_IN_"
                                            "THE_PARTITION"})
    row = t.record()["ranked"][0]
    assert row["effect_when_repaired"].startswith("MEASURED")
    assert "CHANGED_NOTHING" in row["effect_when_repaired"]
    assert row["confidence"] == bc.CONF_HIGH


def test_ranking_is_by_rooms_unlocked_not_by_length():
    leaks = [_Leak("LK-small", "A", "B", gid="SG-2", width=5000.0),
             _Leak("LK-big", "C", "D", gid="SG-1", width=50.0)]
    t = bc.build(leaks, labels_inside={"SG-1": tuple("CDEFGHIJ"),
                                       "SG-2": ("A", "B")})
    ranked = t.record()["ranked"]
    assert ranked[0]["separator_id"] == "LK-big"
    assert "NOT the separator's length" in t.record()["ranking"]


def test_a_single_label_component_is_not_in_the_table():
    t = bc.build([_Leak("LK-1", "A", "B")],
                 labels_inside={"SG-1": ("A",)})
    assert t.rows == []
