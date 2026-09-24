"""The same building, described differently, has to measure the same.

These are not consistency checks between two engine structures.  They take one drawing, change something that
is not the building - where it sits, which way round it is, how finely the extractor cut it up, which drawing
convention the draughtsman used - and require the quantities to come back identical.  A result that moves under
any of these depends on the description rather than on the building, and that dependence is invisible in any
single run, which is exactly why R4 could look self-consistent and be wrong.
"""

from __future__ import annotations

from engine.qs_core import pipeline, synthetic as S
from engine.qs_core.entities import KIND_WALL_BAND

MASONRY = ("BLOCKWORK",)


def annotations_for(plan):
    return {c.component_ref: {"MATERIAL": "BLOCKWORK", "LAYER": "WALL"}
            for c in plan["COMPONENTS"] if c.kind == KIND_WALL_BAND}


def run(plan):
    return pipeline.run(plan, max_opening_span=S.MAX_OPENING_SPAN,
                        drafting_resolution_m=S.DRAFTING_RESOLUTION, wall_height_evidence=S.WALL_HEIGHT,
                        annotations=annotations_for(plan), masonry_materials=MASONRY)


def quantities(result):
    """What the building is, stripped of every name and coordinate the description chose."""
    walls = sorted((round(r["THICKNESS_M"], 6), round(r["NET_AREA_M2"], 6))
                   for r in result["WALL_ROWS"] if r["NET_AREA_M2"] is not None)
    blocked = sorted(round(r["THICKNESS_M"], 6) for r in result["WALL_ROWS"]
                     if r["NET_AREA_M2"] is None)
    spaces = sorted(round(s["AREA_M2"], 6) for s in result["SPACES"])
    openings = sorted(round(o["AREA_M2"], 6) for o in result["OPENING_REGISTER"]["REGISTER"]
                      if o["AREA_M2"] is not None)
    return {"WALLS": walls, "BLOCKED_THICKNESSES": blocked, "SPACES": spaces, "OPENINGS": openings,
            "PUBLISHED": {k: v["FINAL_QUANTITY"] for k, v in result["PUBLICATION"]["SUBTOTALS"].items()}}


def test_the_baseline_plan_produces_quantities_at_all():
    q = quantities(run(S.small_plan("R1")))
    assert q["WALLS"] and q["SPACES"] and q["OPENINGS"]


def test_quantities_do_not_move_when_the_building_is_translated():
    a = quantities(run(S.small_plan("R1")))
    b = quantities(run(S.transform_plan(S.small_plan("R1"), dx=137.5, dy=-64.25)))
    assert a == b


def test_quantities_do_not_move_when_the_building_is_rotated_through_right_angles():
    a = quantities(run(S.small_plan("R1")))
    for turns in (1, 2, 3):
        b = quantities(run(S.transform_plan(S.small_plan("R1"), quarter_turns=turns)))
        assert a["WALLS"] == b["WALLS"], turns
        assert a["SPACES"] == b["SPACES"] and a["OPENINGS"] == b["OPENINGS"]
        assert sorted(a["PUBLISHED"].values()) == sorted(b["PUBLISHED"].values())


def test_quantities_do_not_move_under_rotation_and_translation_together():
    a = quantities(run(S.small_plan("R1")))
    b = quantities(run(S.transform_plan(S.small_plan("R1"), dx=-500.0, dy=250.0, quarter_turns=3)))
    assert a["WALLS"] == b["WALLS"] and a["SPACES"] == b["SPACES"]


def test_quantities_do_not_move_when_the_extractor_cuts_the_walls_into_more_pieces():
    a = quantities(run(S.small_plan("R1")))
    for cuts in (2, 3, 5):
        b = quantities(run(S.resegment_plan(S.small_plan("R1"), cuts=cuts)))
        assert a == b, cuts


def test_two_equivalent_cad_representations_of_one_wall_measure_the_same():
    """One draughtsman runs the wall through the door; the other stops at each jamb.  Same wall."""
    bands_span = [S.wall_band("W", (0.0, 0.0, 6.0, 0.20), 0.20, "X")]
    bands_stop = [S.wall_band("W-L", (0.0, 0.0, 2.0, 0.20), 0.20, "X"),
                  S.wall_band("W-R", (2.9, 0.0, 6.0, 0.20), 0.20, "X")]
    door = ("OP", (2.0, 0.0, 2.9, 0.20), "X")

    def measure(bands):
        plan = {"COMPONENTS": list(bands) + [S.floor_region("F", [(0.0, 1.0, 6.0, 4.0)])],
                "BARRIERS": [], "LABELS": [], "REVISION": "R1", "TOLERANCE_M": S.TOL,
                "SLIVER_MIN_DIMENSION_M": S.SLIVER_MIN, "FLOOR": S.FLOOR,
                "CANDIDATES": [S.candidate(*door)]}
        return quantities(run(plan))

    a, b = measure(bands_span), measure(bands_stop)
    assert a["WALLS"] == b["WALLS"], (a["WALLS"], b["WALLS"])
    assert a["OPENINGS"] == b["OPENINGS"]


def test_the_metamorphic_record_is_the_one_the_acceptance_gate_reads():
    from engine.qs_core import acceptance

    base = run(S.small_plan("R1"))
    moved = run(S.transform_plan(S.small_plan("R1"), dx=10.0, dy=10.0, quarter_turns=1))
    cut = run(S.resegment_plan(S.small_plan("R1"), cuts=3))
    record = {
        "RIGID_MOTION": {"EQUIVALENT": quantities(base) == quantities(moved),
                         "TRANSFORM": "dx=10, dy=10, one quarter turn"},
        "SEGMENTATION": {"EQUIVALENT": quantities(base) == quantities(cut), "CUTS": 3},
        "REPRESENTATION": {"EQUIVALENT": True,
                           "NOTE": "proved in test_two_equivalent_cad_representations_of_one_wall"},
    }
    doc = pipeline.acceptance_document(base, metamorphic=record)
    graded = acceptance.grade(doc)
    assert all(c["RESULT"] == "PASS" for c in graded["CHECKS"] if c["CHECK"] in ("A8", "A9", "A10")), \
        [c for c in graded["CHECKS"] if c["RESULT"] == "FAIL"]


def test_a_barrier_backed_room_boundary_survives_being_turned_through_a_right_angle():
    """Barriers are lines, not rectangles; a transformation that forgot them would merge two rooms into one."""
    from engine.qs_core import spaces as SP, transforms as T

    comps, barriers, _ops, labels = S.single_line_partition()
    plan = {"COMPONENTS": comps, "BARRIERS": barriers, "CANDIDATES": [], "LABELS": labels,
            "REVISION": "R1", "TOLERANCE_M": S.TOL, "SLIVER_MIN_DIMENSION_M": S.SLIVER_MIN, "FLOOR": S.FLOOR}
    before = SP.assemble_semantic_spaces(plan["COMPONENTS"], plan["BARRIERS"], [], plan["LABELS"],
                                         S.TOL, S.SLIVER_MIN)
    moved = T.transform_plan(plan, dx=7.0, dy=-3.0, quarter_turns=1)
    after = SP.assemble_semantic_spaces(moved["COMPONENTS"], moved["BARRIERS"], [], moved["LABELS"],
                                        S.TOL, S.SLIVER_MIN)
    assert len(before["SPACES"]) == len(after["SPACES"]) == 2
    assert sorted(s.label for s in before["SPACES"]) == sorted(s.label for s in after["SPACES"])
    assert sorted(round(s.area, 6) for s in before["SPACES"]) == \
        sorted(round(s.area, 6) for s in after["SPACES"])
