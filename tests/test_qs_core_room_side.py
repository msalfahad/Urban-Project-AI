"""Which side of a window owns the room-use standard.

A window separates an occupied room from the open air.  R6 resolved the room by distance and called the
ordinary external window an ambiguity: on the real drawing a roof terrace competed with the bedroom on the
other side of the glass, and three windows lost their standard to a polygon nobody would call a room.

Each case here is stated as a building, not as a number: what is on each side, what the source calls it, and
what the engine may therefore conclude.
"""

from __future__ import annotations

from engine.qs_core import admission as AD, geom, hosting as H, pipeline, room_category as RC, \
    synthetic as S, transforms as TR

TOL = S.TOL


def resolve(plan, space_role=S.space_role):
    r = S.run(plan, wall_height=3.0, room_category_mapping=S.LABEL_TO_CATEGORY,
              standard_table=S.STANDARD_TABLE, space_role=space_role)
    return r["ROOM_CATEGORY_REGISTER"]["REGISTER"][0], r


# 1 ------------------------------------------------------------------ bedroom versus roof terrace
def test_a_bedroom_on_one_side_and_a_roof_on_the_other_resolves_to_the_bedroom():
    row, _r = resolve(S.a_window_between_two_spaces(inside="BED ROOM", outside="ROOF"))
    assert row["ROOM"]["STATUS"] == RC.ROOM_RESOLVED
    assert row["ROOM"]["LABEL"] == "BED ROOM"
    assert row["ROOM"]["ROLE"] == RC.ENCLOSED_ROOM
    assert row["CATEGORY"]["CATEGORY"] == "BEDROOM"
    assert "enclosed side" in row["ROOM"]["WHY"]


def test_the_open_side_is_published_as_a_candidate_rather_than_hidden():
    row, _r = resolve(S.a_window_between_two_spaces(inside="BED ROOM", outside="ROOF"))
    roles = {c["LABEL"]: c["ROLE"] for c in row["ROOM"]["CANDIDATES"]}
    assert roles["ROOF"] == RC.EXTERNAL_OR_OPEN
    sides = {c["LABEL"]: c["SIDE"] for c in row["ROOM"]["CANDIDATES"]}
    assert sides["BED ROOM"] != sides["ROOF"], "the two spaces are on opposite sides of the wall"


# 2 ------------------------------------------------------------------ bathroom versus external roof
def test_a_bathroom_against_an_external_roof_takes_the_bathroom_standard():
    row, _r = resolve(S.a_window_between_two_spaces(inside="BATH", outside="ROOF"))
    assert row["CATEGORY"]["CATEGORY"] == "BATHROOM"
    assert row["STANDARD_ANSWERED_THE_HEIGHT"] is True


# 3 ------------------------------------------------------------------ two internal rooms
def test_two_enclosed_rooms_either_side_is_a_real_ambiguity_and_stays_one():
    row, _r = resolve(S.a_window_between_two_spaces(inside="BED ROOM", outside="KITCHEN"))
    assert row["ROOM"]["STATUS"] == RC.ROOM_AMBIGUOUS
    assert row["CATEGORY"]["CATEGORY"] is None
    assert "2 enclosed rooms" in row["ROOM"]["WHY"]


# 4 ------------------------------------------------------------------ two external areas
def test_two_open_areas_give_no_room_and_therefore_no_standard():
    row, _r = resolve(S.a_window_between_two_spaces(inside="TERRACE", outside="ROOF"))
    assert row["ROOM"]["STATUS"] == RC.ROOM_NOT_FOUND
    assert row["CATEGORY"]["CATEGORY"] is None
    assert "occupied room" in row["ROOM"]["WHY"]


def test_a_space_the_source_does_not_classify_is_not_treated_as_open_air():
    """An unclassified neighbour is missing evidence, not evidence of absence."""
    row, _r = resolve(S.a_window_between_two_spaces(inside="BED ROOM", outside="STORE 3"))
    assert row["ROOM"]["STATUS"] == RC.ROOM_AMBIGUOUS
    assert "does not classify" in row["ROOM"]["WHY"]


# 5 ------------------------------------------------------------------ rigid motion
def test_the_answer_survives_translation_and_rotation():
    base, _r = resolve(S.a_window_between_two_spaces())
    reference = (base["ROOM"]["STATUS"], base["ROOM"]["LABEL"], base["CATEGORY"]["CATEGORY"])
    for dx, dy, turns in ((812.5, -640.25, 0), (0.0, 0.0, 1), (-40.0, 15.0, 2), (9.0, 9.0, 3)):
        plan = TR.transform_plan(S.a_window_between_two_spaces(), dx=dx, dy=dy, quarter_turns=turns)
        row, _r = resolve(plan)
        assert (row["ROOM"]["STATUS"], row["ROOM"]["LABEL"],
                row["CATEGORY"]["CATEGORY"]) == reference, (dx, dy, turns)


# 6 ------------------------------------------------------------------ different segmentation
def test_the_answer_survives_a_differently_segmented_wall():
    plan = S.a_window_between_two_spaces()
    base, _r = resolve(plan)
    cut = TR.resegment_plan(S.a_window_between_two_spaces(), cuts=3)
    row, _r = resolve(cut)
    assert (row["ROOM"]["STATUS"], row["ROOM"]["LABEL"], row["CATEGORY"]["CATEGORY"]) == \
           (base["ROOM"]["STATUS"], base["ROOM"]["LABEL"], base["CATEGORY"]["CATEGORY"])


# ------------------------------------------------------------------ the engine holds no vocabulary
def test_without_a_role_classifier_the_engine_refuses_rather_than_guessing():
    """The words are the drawing's.  With nobody to classify them, two named spaces are two named spaces."""
    row, _r = resolve(S.a_window_between_two_spaces(), space_role=None)
    assert row["ROOM"]["STATUS"] == RC.ROOM_AMBIGUOUS
    assert "classifies none of them" in row["ROOM"]["WHY"]
