"""A standard by room use is only as good as the room it was resolved for.

R5 offered LIVING_ROOM as the guide category for every window in the villa.  One number then answered a
bedroom, a kitchen, a hall and a bathroom, and because it came from an approved guide the answer looked
evidenced.  A project-wide default is a guess with a citation attached.
"""

from __future__ import annotations

from engine.qs_core import (admission as AD, evidence as EV, hosting as H, room_category as RC,
                            spaces as SP, synthetic as S)

TOL = S.TOL


def resolved(plan=None):
    plan = plan or S.a_flat_with_four_different_room_uses()
    AD.normalize_opening_population(plan["CANDIDATES"], [], S.DRAFTING_RESOLUTION, TOL)
    walls = [c for c in plan["COMPONENTS"] if c.kind == "WALL_BAND"]
    H.resolve_hosts(plan["CANDIDATES"], walls, TOL)
    assembly = SP.assemble_semantic_spaces(plan["COMPONENTS"], plan["BARRIERS"], [], plan["LABELS"],
                                           TOL, plan["SLIVER_MIN_DIMENSION_M"], plan["REVISION"])
    rows = []
    for c in plan["CANDIDATES"]:
        room = RC.resolve_host_room(c, assembly["SPACES"], TOL)
        cat = RC.category_for(room, S.LABEL_TO_CATEGORY)
        rows.append({"OPENING_REF": c.candidate_ref, "ROOM": room, "CATEGORY": cat,
                     "CLAIM": RC.standard_claim(cat, S.STANDARD_TABLE, "STANDARD_V1")})
    return plan, assembly, rows


def test_four_rooms_of_different_use_receive_four_different_categories():
    _plan, _assembly, rows = resolved()
    cats = {r["OPENING_REF"]: r["CATEGORY"]["CATEGORY"] for r in rows}
    assert len(set(cats.values())) == 4, cats
    assert all(v is not None for v in cats.values()), cats


def test_every_category_carries_the_host_room_that_produced_it():
    _plan, _assembly, rows = resolved()
    for r in rows:
        assert r["CATEGORY"]["STATUS"] == RC.CATEGORY_RESOLVED
        assert r["CATEGORY"]["ROOM"]["ROOM_ID"], r["OPENING_REF"]
        assert r["CATEGORY"]["ROOM"]["LABEL"], r["OPENING_REF"]
        assert r["CATEGORY"]["WHY"]


def test_the_standard_claim_ranks_as_a_guide_and_names_the_room_it_came_from():
    _plan, _assembly, rows = resolved()
    for r in rows:
        claim = r["CLAIM"]
        assert claim.source == EV.APPROVED_GUIDE
        assert claim.detail["ROOM_LABEL"] == r["ROOM"]["LABEL"]
        assert r["CATEGORY"]["CATEGORY"] in claim.reference


def test_four_different_categories_give_four_different_heights():
    _plan, _assembly, rows = resolved()
    heights = {r["OPENING_REF"]: r["CLAIM"].value for r in rows}
    assert len(set(heights.values())) == 4, heights


def test_a_mutation_that_gives_every_window_one_category_is_caught():
    """The R5 behaviour, re-implemented: one category for the whole project."""
    _plan, _assembly, rows = resolved()
    honest = RC.build_register(rows)
    assert honest["DISTINCT_CATEGORY_COUNT"] == 4

    mutant_rows = [dict(r, CATEGORY=dict(r["CATEGORY"], CATEGORY="LARGE_HALL",
                                         SOURCE="PROJECT_WIDE_DEFAULT")) for r in rows]
    mutant = RC.build_register(mutant_rows)
    assert mutant["DISTINCT_CATEGORY_COUNT"] == 1
    assert mutant["DISTINCT_CATEGORY_COUNT"] < len(mutant["DISTINCT_ROOMS"]), \
        "one category across four distinct rooms is the defect this check exists to see"


def test_an_unresolved_room_leaves_the_category_unresolved_rather_than_guessing():
    plan = S.a_flat_with_four_different_room_uses()
    stray = S.candidate("WIN-NOWHERE", (400.0, 400.0, 401.2, 400.2), "X", kind="WINDOW", height=None)
    plan["CANDIDATES"].append(stray)
    _plan, _assembly, rows = resolved(plan)
    row = next(r for r in rows if r["OPENING_REF"] == "WIN-NOWHERE")
    assert row["ROOM"]["STATUS"] == RC.ROOM_NOT_FOUND
    assert row["CATEGORY"]["CATEGORY"] is None and row["CLAIM"] is None
    assert row["CATEGORY"]["STATUS"].startswith(RC.CATEGORY_NO_ROOM)


def test_a_label_the_mapping_does_not_cover_is_reported_not_defaulted():
    plan = S.a_flat_with_four_different_room_uses()
    plan["LABELS"][0] = type(plan["LABELS"][0])("PLANT ROOM", plan["LABELS"][0].x, plan["LABELS"][0].y)
    _plan, _assembly, rows = resolved(plan)
    row = next(r for r in rows if r["ROOM"].get("LABEL") == "PLANT ROOM")
    assert row["CATEGORY"]["STATUS"] == RC.CATEGORY_UNMAPPED
    assert row["CLAIM"] is None


def test_the_engine_holds_no_label_vocabulary_of_its_own():
    import pathlib
    text = pathlib.Path("engine/qs_core/room_category.py").read_text("utf-8")
    for word in ("BEDROOM", "KITCHEN", "BATHROOM", "LIVING_ROOM", "DEWANIYA", "HALL"):
        assert word not in text, f"{word} is a project's vocabulary and does not belong in the engine"
