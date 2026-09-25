"""What an answer is actually worth: blocker sets, and the difference between affecting and releasing.

R6 reported 565 dependency impacts, 246 of them exact duplicates, and then said four material questions were
"the whole bottleneck" and would "unblock all 127 rows".  Both statements were produced by counting edges.
Neither was produced by asking, of any single row, whether anything else was still holding it up.
"""

from __future__ import annotations

from engine.qs_core import dependency as DEP, questions as QN, synthetic as S


def a_graph_with(nodes):
    return {"NODES": {"WALL_LINE": list(nodes)}, "EDGES": []}


def register_with(edges):
    reg = QN.Register()
    for qid, node in edges:
        reg.ask(qid.split("::")[1], qid.split("::", 2)[2], f"what about {node}?")
        reg.impact(qid, node, "WALL_LINE", "it is not final while this is open")
    return reg


def test_recording_the_same_edge_twice_changes_nothing_but_the_tally():
    reg = QN.Register()
    reg.ask("K", "S", "q?")
    for _ in range(5):
        reg.impact("RQ::K::S", "W-1", "WALL_LINE", "same effect")
    out = reg.as_dict()
    assert out["DEPENDENCY_IMPACT_COUNT"] == 1
    assert out["REPEATED_INSERTIONS"] == 4
    assert out["DUPLICATE_IMPACT_ROWS"] == 0


def test_a_row_with_two_blockers_is_released_by_neither_answer_alone():
    reg = register_with([("RQ::WALL_MATERIAL_NOT_ESTABLISHED::G1", "W-1"),
                         ("RQ::OPENING_HEIGHT_NOT_ESTABLISHED::OP-1", "W-1")])
    b = DEP.blocker_sets(a_graph_with(["W-1"]), reg.as_dict())
    node = b["NODES"]["W-1"]
    assert node["BLOCKER_COUNT"] == 2
    assert node["ANSWER_ALONE_RELEASES_NODE"] is None
    for qid, rec in b["BY_ROOT_QUESTION"].items():
        assert rec["RELEASES_NODES"] == []
        assert rec["REMOVES_A_BLOCKER_BUT_LEAVES_OTHERS"] == ["W-1"]
    assert node["REMAINING_BLOCKERS_IF_ANSWERED"][
        "RQ::WALL_MATERIAL_NOT_ESTABLISHED::G1"] == ["RQ::OPENING_HEIGHT_NOT_ESTABLISHED::OP-1"]


def test_a_row_with_one_blocker_is_released_by_that_answer():
    reg = register_with([("RQ::WALL_MATERIAL_NOT_ESTABLISHED::G1", "W-1")])
    b = DEP.blocker_sets(a_graph_with(["W-1"]), reg.as_dict())
    assert b["NODES"]["W-1"]["ANSWER_ALONE_RELEASES_NODE"] == "RQ::WALL_MATERIAL_NOT_ESTABLISHED::G1"
    assert b["BY_ROOT_QUESTION"]["RQ::WALL_MATERIAL_NOT_ESTABLISHED::G1"]["RELEASES_NODES"] == ["W-1"]


def test_a_subtotal_blocked_by_several_rows_needs_all_of_their_answers():
    reg = register_with([("RQ::A::1", "SUBTOTAL::0.2"), ("RQ::B::2", "SUBTOTAL::0.2"),
                         ("RQ::A::1", "W-1"), ("RQ::B::2", "W-2")])
    graph = {"NODES": {"WALL_LINE": ["W-1", "W-2"], "THICKNESS_SUBTOTAL": ["SUBTOTAL::0.2"]}, "EDGES": []}
    b = DEP.blocker_sets(graph, reg.as_dict())
    assert b["NODES"]["SUBTOTAL::0.2"]["BLOCKER_COUNT"] == 2
    one = DEP.simulate(b, ["RQ::A::1"])
    assert [n["NODE"] for n in one["RELEASED_NODES"]] == ["W-1"]
    assert any(n["NODE"] == "SUBTOTAL::0.2" for n in one["STILL_BLOCKED"])
    both = DEP.simulate(b, ["RQ::A::1", "RQ::B::2"])
    assert both["STILL_BLOCKED"] == [] and both["RELEASED_NODE_COUNT"] == 3


def test_building_the_blocker_sets_twice_gives_the_same_answer():
    reg = register_with([("RQ::A::1", "W-1"), ("RQ::B::2", "W-1")])
    graph = a_graph_with(["W-1"])
    assert DEP.blocker_sets(graph, reg.as_dict()) == DEP.blocker_sets(graph, reg.as_dict())


def test_an_excluded_row_is_not_reported_as_blocked():
    reg = register_with([("RQ::A::1", "W-1")])
    rows = [{"COMPONENT_REF": "W-2", "STATUS": "EXCLUDED_NOT_MASONRY"}]
    b = DEP.blocker_sets(a_graph_with(["W-1", "W-2"]), reg.as_dict(), rows)
    assert b["NODES"]["W-2"]["NODE_STATUS"] == DEP.NODE_EXCLUDED
    assert b["NODES"]["W-1"]["NODE_STATUS"] == DEP.NODE_BLOCKED


def test_the_three_words_are_defined_in_the_register_itself():
    b = DEP.blocker_sets(a_graph_with([]), QN.Register().as_dict())
    assert set(b["DEFINITIONS"]) == {"AFFECTS", "REMOVES_ONE_BLOCKER", "RELEASES"}
    assert "only remaining blocker" in b["RULE"]


def test_on_a_real_fixture_the_pipeline_publishes_the_blocker_sets():
    r = S.run(S.small_plan("R1"), wall_height=3.0)
    b = r["BLOCKER_SETS"]
    assert b["DEFINITIONS"] and "NODES" in b
    for node, rec in b["NODES"].items():
        if rec["ANSWER_ALONE_RELEASES_NODE"] is not None:
            assert len(rec["BLOCKER_IDS"]) == 1, (node, rec["BLOCKER_IDS"])
