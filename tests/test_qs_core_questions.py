"""One unanswered fact is one question, and the three categories a wall row can be in are three.

R5 reported forty-five open questions for thirty-seven unresolved facts, because a door whose host was unknown
was counted where it was admitted and again where the graph could not associate it with a wall.  It also
reported 111 of 173 rows final and 143 of 173 lines released, which cannot both describe the same run: the 143
included 43 rows excluded from the trade, and an excluded row is not a released quantity.
"""

from __future__ import annotations

from engine.qs_core import questions as QN, synthetic as S


def test_asking_the_same_fact_twice_yields_one_root_question():
    reg = QN.Register()
    a = reg.ask("HOST_WALL_UNRESOLVED", "D-1", "Which wall hosts D-1?")
    b = reg.ask("HOST_WALL_UNRESOLVED", "D-1", "Which wall hosts D-1?")
    out = reg.as_dict()
    assert a == b
    assert out["ROOT_QUESTION_COUNT"] == 1
    assert out["ROOT_QUESTIONS"][0]["ASKED_TIMES"] == 2, "the second ask is recorded, not counted"


def test_impacts_are_counted_separately_and_never_as_questions():
    reg = QN.Register()
    qid = reg.ask("HOST_WALL_UNRESOLVED", "D-1", "Which wall hosts D-1?")
    for node in ("W-1", "W-2", "SUBTOTAL::0.2", "BOQ::MASONRY::0.2"):
        reg.impact(qid, node, "NODE", "not final while this is unknown")
    out = reg.as_dict()
    assert out["ROOT_QUESTION_COUNT"] == 1 and out["DEPENDENCY_IMPACT_COUNT"] == 4
    assert out["IMPACTS_PER_ROOT_QUESTION"][qid] == 4
    assert "never presented" in out["RULE"]


def test_an_impact_that_references_no_root_question_is_reported():
    reg = QN.Register()
    reg.impact("RQ::NOWHERE::X", "W-1", "WALL_LINE", "orphan")
    assert reg.as_dict()["IMPACTS_WITHOUT_A_ROOT_QUESTION"] == ["RQ::NOWHERE::X"]


def test_the_id_is_stable_across_registers_so_downstream_stages_can_reference_it():
    assert QN.root_id("HOST_WALL_UNRESOLVED", "D-1") == QN.root_id("HOST_WALL_UNRESOLVED", "D-1")
    assert QN.root_id("HOST_WALL_UNRESOLVED", "D-1") != QN.root_id("OPENING_HEIGHT_NOT_ESTABLISHED", "D-1")


def test_the_pipeline_never_asks_two_questions_about_one_unresolved_host():
    plan = S.small_plan("R1")
    plan["COMPONENTS"].append(S.wall_band("EXTRA", (4.0, 1.0, 4.2, 2.2), 0.20, "Y"))
    r = S.run(plan, wall_height=3.0)
    qs = r["QUESTIONS"]
    subjects = [(q["KIND"], q["SUBJECT_REF"]) for q in qs["ROOT_QUESTIONS"]]
    assert len(subjects) == len(set(subjects))
    for ref in r["HOST_REGISTER"]["HOST_UNRESOLVED_REFS"]:
        about = [q for q in qs["ROOT_QUESTIONS"] if q["SUBJECT_REF"] == ref]
        assert len(about) == 1, about


def test_a_wall_row_is_reported_in_exactly_one_of_three_categories():
    r = S.run(S.small_plan("R1"), wall_height=3.0)
    cats = r["PUBLICATION"]["ROW_CATEGORIES"]
    assert cats["FINAL"] + cats["BLOCKED"] + cats["EXCLUDED"] == cats["OF"] == len(r["WALL_ROWS"])


def test_the_graph_field_is_named_for_what_it_contains():
    r = S.run(S.small_plan("R1"), wall_height=3.0)
    graph = r["DEPENDENCY_GRAPH"]
    assert "RELEASED_WALL_LINES" not in graph, \
        "a field called released must not contain rows excluded from the trade"
    assert "NON_BLOCKED_WALL_LINES" in graph and graph["NON_BLOCKED_MEANS"]


def test_non_blocked_is_not_the_same_as_final_when_a_band_is_excluded():
    """The arithmetic that made the last report contradict itself, made explicit."""
    plan = S.small_plan("R1")
    plan["COMPONENTS"].append(S.wall_band("STUB", (6.0, 6.0, 6.2, 6.2), 0.20, "X"))
    r = S.run(plan, wall_height=3.0)
    cats = r["PUBLICATION"]["ROW_CATEGORIES"]
    non_blocked = len(r["DEPENDENCY_GRAPH"]["NON_BLOCKED_WALL_LINES"])
    assert cats["EXCLUDED"] >= 1, "the fixture has to actually produce an excluded band"
    assert non_blocked == cats["FINAL"] + cats["EXCLUDED"]
    assert non_blocked != cats["FINAL"]
